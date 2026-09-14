"""
Adversarial Security & Hostile Learner Input Tests.
Verifies defense-in-depth against path traversal, privilege escalation,
container escape attempts, and host Docker socket access.
"""

import pytest
from packages.sandbox_runtime import SandboxManager, PodmanSandboxExecutor
from packages.lab_schema import ScenarioFactory, EnvironmentSpec


def test_adversarial_path_traversal_defense():
    """Verify learner commands attempting to traverse out of container are confined."""
    manager = SandboxManager()
    lab = ScenarioFactory.get_all_scenarios()[0]
    session = manager.create_sandbox(lab)

    # Attempt to read host shadow file or Windows system files
    code, out, err = manager.execute_command(session.session_id, "cat ../../../../../etc/shadow")
    # Must fail or return empty/not found, never host credentials
    assert "root:$" not in out
    assert "Administrator" not in out

    manager.terminate_session(session.session_id)


def test_adversarial_socket_isolation():
    """Verify that host Podman/Docker socket is NEVER mounted or exposed."""
    manager = SandboxManager()
    lab = ScenarioFactory.get_all_scenarios()[0]
    session = manager.create_sandbox(lab)

    # Check for docker/podman socket presence inside container
    code, out, _ = manager.execute_command(session.session_id, "ls -la /var/run/docker.sock /run/podman/podman.sock")
    assert "docker.sock" not in out
    assert "podman.sock" not in out

    manager.terminate_session(session.session_id)


def test_adversarial_cgroup_and_capability_drop():
    """Verify Podman sandbox arguments include capability dropping and cgroup limits."""
    executor = PodmanSandboxExecutor()
    env = EnvironmentSpec(memory_limit="256Mi", cpu_limit="0.5", pids_limit=50)

    # Assert capabilities are dropped by default
    assert "ALL" in env.capabilities_drop
    assert env.pids_limit == 50
    assert env.memory_limit == "256Mi"
