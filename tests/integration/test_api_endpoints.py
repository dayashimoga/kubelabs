"""
Integration tests for FastAPI REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_tracks_endpoint():
    response = client.get("/api/v1/labs/tracks")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert len(data["tracks"]) > 0


def test_list_labs_endpoint():
    response = client.get("/api/v1/labs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_lab_detail():
    response = client.get("/api/v1/labs/linux-inode-exhaustion")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "linux-inode-exhaustion"
    assert data["track"] == "linux"
    assert len(data["tasks"]) > 0


def test_start_session_and_advisor():
    # 1. Start simulation session
    start_res = client.post("/api/v1/labs/linux-inode-exhaustion/session", json={"force_simulation": True})
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert session_id

    # 2. Ask diagnostic advisor
    adv_res = client.post(
        f"/api/v1/labs/session/{session_id}/advisor",
        json={"task_id": "diagnose-and-prune-inodes", "question": "What should I inspect next?"},
    )
    assert adv_res.status_code == 200
    adv_data = adv_res.json()
    assert "guidance" in adv_data
    assert "Inspection Target" in adv_data["category"]

    # 3. Clean up session
    del_res = client.delete(f"/api/v1/labs/session/{session_id}")
    assert del_res.status_code == 200


def test_k8s_zero_endpoints_api_flow():
    # 1. Start simulation session for k8s-zero-endpoints
    start_res = client.post("/api/v1/labs/k8s-zero-endpoints/session", json={"force_simulation": True})
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]

    # 2. Test saving the fixed service.yaml
    save_res = client.post(
        f"/api/v1/labs/session/{session_id}/file",
        json={
            "path": "/workspace/service.yaml",
            "content": "apiVersion: v1\nkind: Service\nmetadata:\n  name: checkout-svc\nspec:\n  selector:\n    app: checkout-service\n  ports:\n  - port: 8080\n    targetPort: 8080\n",
        },
    )
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "saved"

    # 3. Validate task
    val_res = client.post(
        f"/api/v1/labs/session/{session_id}/validate",
        json={"task_id": "fix-service-selector"},
    )
    assert val_res.status_code == 200
    report = val_res.json()
    assert report["overall_status"] == "PASS"
    assert report["total_score"] == 100

    # 4. Clean up session
    client.delete(f"/api/v1/labs/session/{session_id}")



def test_incidents_catalog_and_start():
    list_res = client.get("/api/v1/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) >= 12

    # Start incident
    start_res = client.post(
        "/api/v1/incidents/checkout-latency-spike/start",
        json={"session_id": "test-inc-1"},
    )
    assert start_res.status_code == 200
    data = start_res.json()
    assert data["incident_id"] == "checkout-latency-spike"
    assert data["severity"] == "SEV-1"


def test_assessments_endpoint():
    res = client.get("/api/v1/assessments/all")
    assert res.status_code == 200
    data = res.json()
    assert len(data["questions"]) > 0

    # Submit quiz
    sub_res = client.post(
        "/api/v1/assessments/all/submit",
        json={"answers": {"q-linux-01": 1}},
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert "percentage" in sub_data
    assert "details" in sub_data


def test_dashboard_endpoint():
    res = client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "user" in data
    assert "radar" in data
    assert len(data["radar"]) == 12
