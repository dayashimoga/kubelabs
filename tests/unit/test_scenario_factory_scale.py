"""
Unit tests for ScenarioFactory scale, 24-track coverage, and pedagogical completeness.
"""

import pytest
from packages.lab_schema import ScenarioFactory, LabSpec, DifficultyLevel, LabRuntimeClassification


def test_scenario_factory_tracks_completeness():
    tracks = ScenarioFactory.get_tracks()
    assert len(tracks) == 24
    expected = [
        "linux", "bash", "git", "networking", "http-dns-tls", "docker", "kubernetes",
        "helm", "kustomize", "terraform", "ansible", "ci-cd", "github-actions",
        "argocd", "prometheus", "grafana", "alertmanager", "loki", "opentelemetry",
        "istio", "aws-eks", "devsecops", "platform-engineering", "sre-resilience"
    ]
    for exp in expected:
        assert exp in tracks, f"Track {exp} missing from ScenarioFactory"


def test_scenario_factory_catalog_depth():
    scenarios = ScenarioFactory.get_all_scenarios()
    assert len(scenarios) >= 30, f"Expected at least 30 scenarios, got {len(scenarios)}"

    tracks_represented = {s.track for s in scenarios}
    all_tracks = set(ScenarioFactory.get_tracks())
    assert tracks_represented == all_tracks, f"Missing tracks in catalog: {all_tracks - tracks_represented}"


def test_scenario_pedagogical_completeness():
    scenarios = ScenarioFactory.get_all_scenarios()
    for s in scenarios:
        assert s.id, "Scenario missing ID"
        assert s.title, f"Scenario {s.id} missing title"
        assert s.track in ScenarioFactory.get_tracks(), f"Scenario {s.id} invalid track {s.track}"
        assert s.objectives and len(s.objectives) >= 1, f"Scenario {s.id} missing objectives"
        assert s.what_why, f"Scenario {s.id} missing what_why"
        assert s.tasks and len(s.tasks) >= 1, f"Scenario {s.id} missing tasks"
        assert s.tasks[0].validators and len(s.tasks[0].validators) >= 1, f"Scenario {s.id} missing validators"
        assert s.tasks[0].hints and len(s.tasks[0].hints) >= 1, f"Scenario {s.id} missing hints"


def test_scenario_lookup_by_id_and_track():
    scenarios = ScenarioFactory.get_all_scenarios()
    first = scenarios[0]

    found = ScenarioFactory.get_scenario_by_id(first.id)
    assert found is not None
    assert found.id == first.id

    missing = ScenarioFactory.get_scenario_by_id("non-existent-lab-id-xyz")
    assert missing is None

    linux_scenarios = ScenarioFactory.get_scenarios_by_track("linux")
    assert len(linux_scenarios) >= 1
    for s in linux_scenarios:
        assert s.track == "linux"
