"""
Tests ensuring EnvironmentBroker strictly enforces zero silent fallback for REAL environments.
"""

import pytest
from packages.sandbox_runtime.src.broker import EnvironmentBroker, RuntimeProvisioningError
from packages.lab_schema import LabSpec, EnvironmentSpec, EnvironmentType, LabRuntimeClassification, InitialStateSpec, TaskSpec, CleanupPolicy


def test_broker_simulation_mode_explicit():
    broker = EnvironmentBroker()
    lab = LabSpec(
        id="test-sim-explicit",
        title="Simulated Lab",
        track="linux",
        runtime_classification=LabRuntimeClassification.SIMULATED,
        objectives=["Test"],
        what_why="Test",
        environment=EnvironmentSpec(type=EnvironmentType.CONTAINER),
        initial_state=InitialStateSpec(seed_data={"k8s": {}}),
        tasks=[TaskSpec(id="t1", title="T1", description="D1", order=1)],
        cleanup_policy=CleanupPolicy(),
    )
    rec = broker.start_environment("sim-session-1", lab, force_simulation=True)
    assert rec["provider"] == "simulator"
    assert rec["classification"] == LabRuntimeClassification.SIMULATED
    broker.destroy_environment("sim-session-1")


def test_broker_strict_error_when_real_fails():
    broker = EnvironmentBroker(podman_binary="non-existent-podman-binary-123")
    lab = LabSpec(
        id="test-real-must-fail",
        title="Real Lab Requiring Podman",
        track="linux",
        runtime_classification=LabRuntimeClassification.REAL,
        objectives=["Test"],
        what_why="Test",
        environment=EnvironmentSpec(type=EnvironmentType.CONTAINER),
        tasks=[TaskSpec(id="t1", title="T1", description="D1", order=1)],
        cleanup_policy=CleanupPolicy(),
    )

    # Must raise RuntimeProvisioningError and NOT silently fall back to simulator
    with pytest.raises(RuntimeProvisioningError) as exc_info:
        broker.start_environment("fail-session-1", lab, force_simulation=False)

    assert "Podman runtime is not available" in str(exc_info.value) or "Failed to provision" in str(exc_info.value)
