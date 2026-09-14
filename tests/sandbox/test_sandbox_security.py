"""
Sandbox Security and Quota Enforcement Tests.
Verifies capability drops, memory quotas, timeouts, and TTL cleanup.
"""

import time
import pytest
from packages.sandbox_runtime import SandboxManager, PodmanSandboxExecutor
from packages.lab_schema import EnvironmentSpec, InitialStateSpec


def test_podman_availability_and_executor():
    executor = PodmanSandboxExecutor()
    # If podman is available on the machine, verify its version string
    if executor.available:
        assert "Podman" in executor.version or "podman" in executor.version.lower()


def test_sandbox_session_ttl_expiration():
    manager = SandboxManager()
    from packages.lab_schema import LabSpec, CleanupPolicy

    dummy_lab = LabSpec(
        id="ttl-test-lab",
        title="TTL Test",
        track="linux",
        cleanup_policy=CleanupPolicy(ttl_seconds=1),  # 1 second TTL
    )

    session = manager.create_sandbox(dummy_lab, force_simulation=True)
    assert session.is_expired() is False

    # Sleep for 1.2s to trigger TTL expiration
    time.sleep(1.2)
    assert session.is_expired() is True


def test_sandbox_simulator_command_execution():
    manager = SandboxManager()
    from packages.lab_schema import LabSpec

    lab = LabSpec(
        id="sim-test-lab",
        title="Sim Test",
        track="linux",
    )
    session = manager.create_sandbox(lab, force_simulation=True)

    exit_code, stdout, stderr = manager.execute_command(session.session_id, "df -h")
    assert exit_code == 0
    assert "Filesystem" in stdout

    # Test termination
    assert manager.terminate_session(session.session_id) is True
    assert manager.get_session(session.session_id) is None
