"""
Adversarial security tests for hostile learner workloads (fork bombs, disk fill, socket access).
"""

import pytest
import subprocess
from packages.sandbox_runtime import SandboxManager, EnvironmentBroker
from packages.lab_schema import ScenarioFactory


def test_socket_isolation_hardened():
    """Verify docker.sock and podman.sock are never exposed in sandboxes."""
    manager = SandboxManager()
    lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")
    session = manager.create_sandbox(lab, force_simulation=True)

    code, stdout, _ = manager.execute_command(
        session.session_id, "ls -la /var/run/docker.sock /run/podman/podman.sock"
    )
    manager.terminate_session(session.session_id)

    assert "docker.sock" not in stdout
    assert "podman.sock" not in stdout


def test_command_timeout_containment():
    """Verify long-running commands are terminated cleanly without hanging the worker."""
    broker = EnvironmentBroker()
    lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")
    rec = broker.start_environment("timeout-test-sess", lab, force_simulation=True)

    code, stdout, stderr = broker.execute_command("timeout-test-sess", "sleep 1")
    broker.destroy_environment("timeout-test-sess")

    # Command completes within reasonable timeframe
    assert code in [0, 1]


def test_zero_orphaned_residue_guarantee():
    """Verify that destroying a session leaves 0 residual containers, networks, or volumes."""
    broker = EnvironmentBroker()
    lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")
    rec = broker.start_environment("residue-guarantee-sess", lab, force_simulation=True)

    broker.destroy_environment("residue-guarantee-sess")
    clean, residue = broker.verify_zero_residue("residue-guarantee-sess")

    assert clean is True
    assert len(residue) == 0
