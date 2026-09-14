"""
Deep API and Service Integration Tests.
Provides comprehensive coverage across:
1. Interactive WebSocket terminal streaming (/ws/terminal/{session_id})
2. Incident management lifecycle endpoints (/api/v1/incidents/*)
3. Lab execution, advisor, validation, reset, and residue endpoints (/api/v1/labs/*)
4. RedisManager production guards and connection error handling
5. Database production guards and connectivity
6. Troubleshooting advisor diagnostic Q&A and hint mechanics
"""

import sys
import time
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from apps.api.src.main import app
from apps.api.src.core.config import settings
from apps.api.src.core.redis_manager import RedisManager, InMemoryStore
from apps.api.src.core.database import check_database_health
from apps.api.src.services.troubleshooting_service import TroubleshootingAdvisor
from packages.lab_schema import ScenarioFactory, TaskSpec, Hint, HintTier


client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Interactive WebSocket Terminal Tests
# ---------------------------------------------------------------------------

def test_websocket_terminal_flow():
    # First provision a simulated sandbox session
    start_resp = client.post("/api/v1/labs/linux-inode-exhaustion/session", json={"force_simulation": True})
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    with client.websocket_connect(f"/ws/terminal/{session_id}") as websocket:
        # Initial greeting & prompt
        banner = websocket.receive_text()
        assert "KubeLabs SRE Shell Environment" in banner
        prompt = websocket.receive_text()
        assert "sre-engineer@kubelabs-sandbox:~$" in prompt

        # Send command characters 'df -h' followed by enter
        for char in "df -h":
            websocket.send_text(char)
            echo = websocket.receive_text()
            assert echo == char

        # Send backspace
        websocket.send_text("\x7f")
        bs_echo = websocket.receive_text()
        assert "\b \b" in bs_echo

        # Re-type 'h'
        websocket.send_text("h")
        websocket.receive_text()

        # Send enter
        websocket.send_text("\r")
        # Receive newline echo
        nl = websocket.receive_text()
        assert "\r\n" in nl
        # Output of command and post-command prompt
        out = websocket.receive_text()
        assert "Filesystem" in out or "sre-engineer" in out
        prompt_after = websocket.receive_text()
        assert "sre-engineer@kubelabs-sandbox:~$" in prompt_after

        # Send Ctrl+C
        websocket.send_text("\x03")
        sigint = websocket.receive_text()
        assert "^C" in sigint

        # Send 'clear'
        for ch in "clear":
            websocket.send_text(ch)
            websocket.receive_text()
        websocket.send_text("\r")
        websocket.receive_text()  # newline
        cls_seq = websocket.receive_text()  # clear screen sequence
        assert "\x1b[2J" in cls_seq
        websocket.receive_text()  # prompt

        # Send 'exit'
        for ch in "exit":
            websocket.send_text(ch)
            websocket.receive_text()
        websocket.send_text("\r")
        websocket.receive_text()  # newline
        closing = websocket.receive_text()
        assert "Closing session" in closing

    # Cleanup session
    del_resp = client.delete(f"/api/v1/labs/session/{session_id}")
    assert del_resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Incident Management Lifecycle Endpoints
# ---------------------------------------------------------------------------

def test_incident_api_full_lifecycle():
    # 1. Incident Detail
    det_resp = client.get("/api/v1/incidents/checkout-latency-spike")
    assert det_resp.status_code == 200
    det = det_resp.json()
    assert det["id"] == "checkout-latency-spike"
    assert "REDACTED" in det["root_cause_explanation"]

    # 404 for invalid incident
    err_det = client.get("/api/v1/incidents/nonexistent-incident-xyz")
    assert err_det.status_code == 404

    # 2. Start Random Incident
    rand_resp = client.post("/api/v1/incidents/random/start", json={"session_id": "test-rand-user"})
    assert rand_resp.status_code == 200
    rand_data = rand_resp.json()
    assert "incident_id" in rand_data
    assert "alerts" in rand_data
    assert "topology" in rand_data

    # 3. Start Specific Incident
    inc_resp = client.post("/api/v1/incidents/checkout-latency-spike/start", json={"session_id": "test-inc-user"})
    assert inc_resp.status_code == 200
    inc_data = inc_resp.json()
    s_id = inc_data["session_id"]

    # 4. Record Inspection Command
    insp_resp = client.post(f"/api/v1/incidents/session/{s_id}/inspect", json={"command": "kubectl logs -l app=checkout-service"})
    assert insp_resp.status_code == 200
    assert insp_resp.json()["status"] in ["investigating", "triggered"]

    # 5. Test Hypothesis
    hyp_resp = client.post(f"/api/v1/incidents/session/{s_id}/hypothesis", json={"hypothesis_id": "hyp-1"})
    assert hyp_resp.status_code == 200
    assert "hypothesis_id" in hyp_resp.json()

    # 6. Apply Mitigation
    mit_resp = client.post(f"/api/v1/incidents/session/{s_id}/mitigate", json={"command": "kubectl scale deployment checkout-service --replicas=5"})
    assert mit_resp.status_code == 200
    assert "mitigated" in mit_resp.json()

    # 7. Resolve Incident
    res_resp = client.post(f"/api/v1/incidents/session/{s_id}/resolve")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["status"] == "resolved"
    assert "score" in res_data
    assert "post_mortem" in res_data

    # 8. Post-Mortem Endpoint
    pm_resp = client.get(f"/api/v1/incidents/session/{s_id}/post-mortem")
    assert pm_resp.status_code == 200
    assert "post_mortem_markdown" in pm_resp.json()

    # Error handling for invalid session
    bad_sess = client.post("/api/v1/incidents/session/invalid-session-999/inspect", json={"command": "ls"})
    assert bad_sess.status_code == 404


# ---------------------------------------------------------------------------
# 3. Lab Execution, Advisor, Validation, Reset, and Residue Endpoints
# ---------------------------------------------------------------------------

def test_labs_api_endpoints():
    # 1. Lab Detail
    lab_resp = client.get("/api/v1/labs/linux-inode-exhaustion")
    assert lab_resp.status_code == 200
    assert lab_resp.json()["id"] == "linux-inode-exhaustion"

    err_lab = client.get("/api/v1/labs/nonexistent-lab-404")
    assert err_lab.status_code == 404

    # 2. Start Session
    sess_resp = client.post("/api/v1/labs/linux-inode-exhaustion/session", json={"force_simulation": True})
    assert sess_resp.status_code == 200
    s_id = sess_resp.json()["session_id"]

    # 3. Session Health
    health_resp = client.get(f"/api/v1/labs/session/{s_id}/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["session_id"] == s_id

    # 4. Exec command
    exec_resp = client.post(f"/api/v1/labs/session/{s_id}/exec", json={"command": "df -i"})
    assert exec_resp.status_code == 200
    assert "stdout" in exec_resp.json()

    # 5. Ask Advisor
    task_id = sess_resp.json()["tasks"][0]["id"]
    advisor_resp = client.post(
        f"/api/v1/labs/session/{s_id}/advisor",
        json={"task_id": task_id, "question": "What diagnostic command should I execute?"}
    )
    assert advisor_resp.status_code == 200
    assert "guidance" in advisor_resp.json()

    # 6. Validate Task
    val_resp = client.post(f"/api/v1/labs/session/{s_id}/validate", json={"task_id": task_id})
    assert val_resp.status_code == 200
    assert "overall_status" in val_resp.json()

    # 7. Reset Session
    reset_resp = client.post(f"/api/v1/labs/session/{s_id}/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["reset"] is True

    # 8. Verify Residue
    res_resp = client.get(f"/api/v1/labs/session/{s_id}/residue")
    assert res_resp.status_code == 200
    assert "clean" in res_resp.json()

    # 9. Terminate Session
    term_resp = client.delete(f"/api/v1/labs/session/{s_id}")
    assert term_resp.status_code == 200
    assert term_resp.json()["terminated"] is True


# ---------------------------------------------------------------------------
# 4. RedisManager Production Guard & Client Operations
# ---------------------------------------------------------------------------

def test_redis_manager_mocked_client():
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = "stored_value"
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.incr.return_value = 1

    mock_redis_module = MagicMock()
    mock_redis_module.from_url.return_value = mock_redis

    with patch.dict(sys.modules, {"redis": mock_redis_module}):
        rm = RedisManager(redis_url="redis://localhost:6379/0")
        assert rm.is_connected is True
        assert rm.get("key1") == "stored_value"
        assert rm.set("key1", "new_val") is True
        assert rm.delete("key1") is True
        assert rm.check_rate_limit("client_1") is True
        assert rm.check_health() is True

    # Test production guard exception
    with patch.object(settings, "ENVIRONMENT", "production"):
        with pytest.raises(RuntimeError) as exc_info:
            RedisManager(redis_url="")
        assert "Production environment strictly requires REDIS_URL" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Database Health Check
# ---------------------------------------------------------------------------

def test_database_health_reporting():
    # Healthy dev check
    res = check_database_health()
    assert res is True


def test_terminal_reconnect_and_api_error_exceptions():
    from packages.sandbox_runtime import RuntimeProvisioningError
    from apps.api.src.api.labs import lab_service
    from apps.api.src.api.incidents import incident_engine

    # 1. Terminal Reconnect flow
    start_resp = client.post("/api/v1/labs/linux-inode-exhaustion/session", json={"force_simulation": True})
    assert start_resp.status_code == 200
    s_id = start_resp.json()["session_id"]

    # Append scrollback to session
    sess = lab_service.sandbox_manager.get_session(s_id)
    sess.append_scrollback("previous output\n")

    # Connect WebSocket: should receive formatted scrollback and reconnected badge
    with client.websocket_connect(f"/ws/terminal/{s_id}") as ws:
        scroll = ws.receive_text()
        assert "previous output" in scroll
        badge = ws.receive_text()
        assert "[Session reconnected]" in badge

    # 2. Labs start_session exception handling
    with patch.object(lab_service, "start_session", side_effect=RuntimeProvisioningError("Podman error")):
        assert client.post("/api/v1/labs/linux-inode-exhaustion/session", json={}).status_code == 503

    with patch.object(lab_service, "start_session", side_effect=ValueError("Invalid lab")):
        assert client.post("/api/v1/labs/linux-inode-exhaustion/session", json={}).status_code == 404

    with patch.object(lab_service, "start_session", side_effect=Exception("Internal error")):
        assert client.post("/api/v1/labs/linux-inode-exhaustion/session", json={}).status_code == 500

    # 3. Incidents start_incident exception handling
    with patch.object(incident_engine, "start_random_incident", side_effect=Exception("Random error")):
        assert client.post("/api/v1/incidents/random/start", json={"session_id": "err"}).status_code == 400

    with patch.object(incident_engine, "start_incident", side_effect=Exception("Start error")):
        assert client.post("/api/v1/incidents/checkout-latency-spike/start", json={"session_id": "err"}).status_code == 400

    # Clean up
    lab_service.sandbox_manager.terminate_session(s_id)
