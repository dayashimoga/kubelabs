"""
Unit and Integration Tests for Incident Engine, Random Incident Mode,
Troubleshooting Library, and SRE Scoring.
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.src.main import app
from packages.incident_core import IncidentEngine, IncidentCatalog, IncidentStatus

client = TestClient(app)


def test_incident_engine_full_lifecycle():
    engine = IncidentEngine()
    session = engine.start_incident("checkout-latency-spike", "test-lifecycle-01")

    assert session.status == IncidentStatus.TRIGGERED
    assert session.incident.id == "checkout-latency-spike"

    # Acknowledge
    session.acknowledge()
    assert session.status == IncidentStatus.ACKNOWLEDGED
    assert session.acknowledged_at is not None

    # Record inspection command
    session.record_inspection("kubectl logs -l app=inventory-service")
    assert session.status == IncidentStatus.INVESTIGATING
    assert len(session.inspected_commands) == 1

    # Test hypothesis
    session.test_hypothesis("hyp-01")
    assert "hyp-01" in session.tested_hypotheses

    # Apply incorrect mitigation
    wrong_fix = session.apply_fix("kubectl delete pod --all -n default")
    assert not wrong_fix

    # Apply correct mitigation
    correct_fix = session.apply_fix("kubectl rollout restart deployment/checkout-service")
    assert correct_fix
    assert session.status == IncidentStatus.MITIGATING
    assert session.mitigated_at is not None

    # Verify resolution and score
    score = session.verify_resolution()
    assert score.total_score >= 80
    assert score.detection_score > 0
    assert score.fix_score > 0
    assert session.status == IncidentStatus.RESOLVED

    # Post-mortem generation
    pm = session.generate_post_mortem()
    assert "# SRE Incident Post-Mortem" in pm
    assert "Checkout Latency Spike" in pm
    assert "Customer Impact" in pm
    assert "Root Cause Analysis" in pm


def test_start_random_incident_mode():
    engine = IncidentEngine()
    session = engine.start_random_incident("rand-session-01")

    assert session is not None
    assert session.session_id == "rand-session-01"
    assert session.incident is not None
    # Verify randomized background noise was injected
    assert len(session.incident.initial_symptoms) >= 3


def test_api_troubleshooting_search_and_filters():
    # 1. Broad search
    res = client.get("/api/v1/troubleshooting/search?q=CrashLoopBackOff")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] > 0
    assert "grouped_by_difficulty" in data
    assert "beginner" in data["grouped_by_difficulty"]
    assert "production" in data["grouped_by_difficulty"]

    # 2. Filter by track
    res_track = client.get("/api/v1/troubleshooting/search?track=kubernetes")
    assert res_track.status_code == 200
    track_data = res_track.json()
    for item in track_data["results"]:
        assert item["track"] == "kubernetes"

    # 3. Filter by difficulty
    res_diff = client.get("/api/v1/troubleshooting/search?difficulty=production")
    assert res_diff.status_code == 200
    diff_data = res_diff.json()
    for item in diff_data["results"]:
        assert item["difficulty"] == "production"


def test_api_random_incident_workflow():
    # Start random incident
    res = client.post("/api/v1/incidents/random/start", json={"session_id": "api-rand-1"})
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "api-rand-1"
    assert "incident_id" in data
    assert len(data["initial_symptoms"]) >= 3

    # Inspect command
    inspect_res = client.post(
        "/api/v1/incidents/session/api-rand-1/inspect",
        json={"command": "curl -s http://localhost:8080/health"},
    )
    assert inspect_res.status_code == 200
    assert inspect_res.json()["status"] == "investigating"

    # Hypothesis test
    hyp_res = client.post(
        "/api/v1/incidents/session/api-rand-1/hypothesis",
        json={"hypothesis_id": "hyp-01"},
    )
    assert hyp_res.status_code == 200

    # Mitigate
    mit_res = client.post(
        "/api/v1/incidents/session/api-rand-1/mitigate",
        json={"command": "kubectl patch deployment web -p 'replicas: 5'"},
    )
    assert mit_res.status_code == 200

    # Resolve
    res_resolve = client.post("/api/v1/incidents/session/api-rand-1/resolve")
    assert res_resolve.status_code == 200
    res_data = res_resolve.json()
    assert "score" in res_data
    assert "post_mortem" in res_data
    assert res_data["score"]["total_score"] > 0

    # Get post-mortem
    pm_res = client.get("/api/v1/incidents/session/api-rand-1/post-mortem")
    assert pm_res.status_code == 200
    assert "# SRE Incident Post-Mortem" in pm_res.json()["post_mortem_markdown"]
