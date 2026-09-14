"""
Integration tests for /readyz readiness probe and X-Request-ID middleware.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_healthz_endpoint():
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_readyz_endpoint():
    res = client.get("/readyz")
    assert res.status_code == 200
    data = res.json()
    assert "ready" in data
    assert "components" in data
    assert data["components"]["database"] == "connected"


def test_request_id_header_middleware():
    res = client.get("/healthz")
    assert "X-Request-ID" in res.headers
    assert len(res.headers["X-Request-ID"]) > 0

    # Custom request ID preserved
    custom_id = "test-custom-request-id-42"
    res2 = client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert res2.headers["X-Request-ID"] == custom_id


def test_session_health_endpoint():
    # Start a test session
    res_start = client.post("/api/v1/labs/linux-inode-exhaustion/session", json={"force_simulation": True})
    assert res_start.status_code == 200
    sess_id = res_start.json()["session_id"]

    res_health = client.get(f"/api/v1/labs/session/{sess_id}/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "READY"
    assert health_data["expired"] is False
    assert health_data["remaining_ttl_seconds"] > 0
