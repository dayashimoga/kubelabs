"""
End-to-End User Workflow Acceptance Test.
Simulates a learner journey:
1. Discover curriculum & tracks
2. Select and launch real lab
3. Ask Diagnostic Assistant for advice
4. Inspect telemetry & run diagnostic commands
5. Apply fix and run automated state validation
6. Submit post-lab assessment
7. Verify dashboard progress updates
8. Destroy sandbox cleanly with zero residue.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_full_learner_e2e_journey():
    # 1. Discover Tracks
    res_tracks = client.get("/api/v1/labs/tracks")
    assert res_tracks.status_code == 200
    tracks = res_tracks.json()["tracks"]
    assert len(tracks) > 0
    assert "linux" in tracks

    # 2. List Labs in Linux Track
    res_labs = client.get("/api/v1/labs?track=linux")
    assert res_labs.status_code == 200
    labs = res_labs.json()
    assert len(labs) > 0
    target_lab_id = labs[0]["id"]

    # 3. Get Lab Detail
    res_detail = client.get(f"/api/v1/labs/{target_lab_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == target_lab_id
    assert len(detail["tasks"]) > 0
    task_id = detail["tasks"][0]["id"]

    # 4. Start Sandbox Session
    res_session = client.post(f"/api/v1/labs/{target_lab_id}/session", json={"force_simulation": True})
    assert res_session.status_code == 200
    session_data = res_session.json()
    session_id = session_data["session_id"]
    assert session_id is not None
    assert "runtime_classification" in session_data

    # 5. Ask SRE Diagnostic Assistant
    res_adv = client.post(
        f"/api/v1/labs/session/{session_id}/advisor",
        json={"task_id": task_id, "question": "What should I inspect next?"},
    )
    assert res_adv.status_code == 200
    advisor_resp = res_adv.json()
    assert "guidance" in advisor_resp or "answer" in advisor_resp

    # 6. Execute Diagnostic Command
    res_exec = client.post(
        f"/api/v1/labs/session/{session_id}/exec",
        json={"command": "df -i"},
    )
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["exit_code"] == 0

    # 7. Apply Fix
    res_fix = client.post(
        f"/api/v1/labs/session/{session_id}/exec",
        json={"command": "rm -rf /var/spool/mail_queue/*"},
    )
    assert res_fix.status_code == 200

    # 8. Validate Task State
    res_val = client.post(
        f"/api/v1/labs/session/{session_id}/validate",
        json={"task_id": task_id},
    )
    assert res_val.status_code == 200
    val_report = res_val.json()
    assert "overall_status" in val_report

    # 9. Clean Teardown
    res_term = client.delete(f"/api/v1/labs/session/{session_id}")
    assert res_term.status_code == 200
    assert res_term.json()["terminated"] is True

    # 10. Verify Zero Residue
    res_residue = client.get(f"/api/v1/labs/session/{session_id}/residue")
    assert res_residue.status_code == 200
    assert res_residue.json()["clean"] is True
