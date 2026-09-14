"""
Comprehensive Unit Tests for Sandbox Runtime:
DeterministicSimulator, EnvironmentBroker, KubernetesProvider, and SandboxManager.
"""

import pytest
from packages.lab_schema import (
    LabSpec,
    DifficultyLevel,
    ValidationStatus,
    LabRuntimeClassification,
    EnvironmentSpec,
    EnvironmentType,
    ScenarioFactory,
)
from packages.sandbox_runtime import (
    DeterministicSimulator,
    EnvironmentBroker,
    KubernetesProvider,
    PodmanSandboxExecutor,
    SandboxManager,
)


def test_deterministic_simulator_full_api():
    sim = DeterministicSimulator("linux-inode-exhaustion")

    # Command execution
    code, out, err = sim.execute_command("df -h")
    assert code == 0
    assert "Filesystem" in out

    # Command df -i (inode exhausted initially)
    code_i, out_i, _ = sim.execute_command("df -i")
    assert code_i == 0
    assert "100%" in out_i

    # Repair command
    code_rep, _, _ = sim.execute_command("find /var/spool -name 'qf*' -delete")
    assert code_rep == 0

    # df -i after repair
    code_post, out_post, _ = sim.execute_command("df -i")
    assert "2%" in out_post

    # K8s command in simulator
    sim.state["k8s"]["pods"]["web-app-xyz"] = {"ready": "1/1", "status": "Running", "restarts": 0}
    code_k8s, out_k8s, _ = sim.execute_command("kubectl get pods")
    assert code_k8s == 0
    assert "web-app-xyz" in out_k8s

    # Unhandled command fallback
    code_un, out_un, _ = sim.execute_command("uname -a")
    assert code_un == 0
    assert "uname -a" in out_un


def test_environment_broker_lifecycle():
    broker = EnvironmentBroker()

    # Create a simulation lab spec
    sim_lab = LabSpec(
        id="sim-test-lab",
        title="Simulation Broker Test",
        track="linux",
        difficulty=DifficultyLevel.BEGINNER,
        estimated_minutes=10,
        validation_status=ValidationStatus.PROVEN,
        runtime_classification=LabRuntimeClassification.SIMULATED,
        tasks=[],
        environment=EnvironmentSpec(type=EnvironmentType.SIMULATION),
    )

    env_record = broker.start_environment("test-sbx-01", sim_lab, force_simulation=True)
    assert env_record["provider"] == "simulator"
    assert env_record["sandbox_id"] == "test-sbx-01"

    # Execute command in broker environment
    code, out, err = broker.execute_command("test-sbx-01", "echo broker-test")
    assert code == 0

    # Destroy environment
    broker.destroy_environment("test-sbx-01")
    assert "test-sbx-01" not in broker.active_environments


def test_sandbox_manager_session_lifecycle():
    manager = SandboxManager()
    lab = ScenarioFactory.get_all_scenarios()[0]

    session = manager.create_sandbox(lab)
    assert session is not None
    assert session.session_id in manager.sessions

    # Get session
    retrieved = manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.lab_id == lab.id
    assert retrieved.health["status"] in ["READY", "HEALTHY"]

    # Execute command in session
    code, out, err = manager.execute_command(session.session_id, "echo sandbox-test")
    assert code == 0

    # Terminate session
    term_res = manager.terminate_session(session.session_id)
    assert term_res is True
    assert session.session_id not in manager.sessions


def test_kubernetes_provider_simulation_contract():
    k8s = KubernetesProvider()
    assert k8s.is_podman_available is not None
    assert k8s.is_kubectl_available is not None

    # Check zero residue initially
    clean, orphaned = k8s.verify_zero_residue("test-sbx-01")
    assert clean is True
    assert len(orphaned) == 0
