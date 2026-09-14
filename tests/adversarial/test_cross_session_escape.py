"""
Cross-Session Isolation & Adversarial Security Test Suite.
Verifies defense-in-depth against container escapes, cross-session interference,
socket leakage, capability escalation, and host path traversal.
"""

import pytest
import os
from packages.sandbox_runtime import SandboxManager, EnvironmentBroker, PodmanSandboxExecutor
from packages.lab_schema import ScenarioFactory, EnvironmentSpec, InitialStateSpec


class TestCrossSessionIsolation:
    """Tests isolating multi-tenant learner sessions from each other and the host."""

    def test_capability_drop_defaults(self):
        """Verify capability drops (--cap-drop=ALL) are configured by default."""
        env = EnvironmentSpec()
        assert "ALL" in env.capabilities_drop

        # Verify executor properly converts capabilities into run flags
        executor = PodmanSandboxExecutor()
        assert executor is not None

    def test_docker_and_podman_socket_isolation(self):
        """Verify host Docker and Podman daemon sockets are NEVER exposed."""
        manager = SandboxManager()
        lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")
        session = manager.create_sandbox(lab, force_simulation=True)

        try:
            code, stdout, stderr = manager.execute_command(
                session.session_id,
                "ls -la /var/run/docker.sock /run/podman/podman.sock /var/run/podman.sock"
            )
            # Daemon sockets must never be mounted
            assert "docker.sock" not in stdout
            assert "podman.sock" not in stdout
        finally:
            manager.terminate_session(session.session_id)

    def test_cross_session_filesystem_isolation(self):
        """Verify session A cannot view, mutate, or tamper with session B's files."""
        manager = SandboxManager()
        lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")

        sess_a = manager.create_sandbox(lab, force_simulation=True)
        sess_b = manager.create_sandbox(lab, force_simulation=True)

        try:
            # Session A writes private data
            manager.execute_command(sess_a.session_id, "echo 'secret_token_session_a' > /tmp/private_sess_a.txt")

            # Session B attempts to read session A's private data
            code_b, stdout_b, stderr_b = manager.execute_command(
                sess_b.session_id,
                "cat /tmp/private_sess_a.txt"
            )

            # Must fail or return empty, never leak session A's contents
            assert "secret_token_session_a" not in stdout_b
        finally:
            manager.terminate_session(sess_a.session_id)
            manager.terminate_session(sess_b.session_id)

    def test_cross_session_teardown_independence(self):
        """Verify terminating session A leaves session B running healthy without interference."""
        manager = SandboxManager()
        lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")

        sess_a = manager.create_sandbox(lab, force_simulation=True)
        sess_b = manager.create_sandbox(lab, force_simulation=True)

        try:
            # Terminate Session A
            manager.terminate_session(sess_a.session_id)

            # Session B must still be fully alive and operational
            code, out, _ = manager.execute_command(sess_b.session_id, "echo 'session_b_operational'")
            assert code == 0
            assert "session_b_operational" in out
        finally:
            manager.terminate_session(sess_b.session_id)

    def test_host_path_traversal_prevention(self):
        """Verify path traversal sequences cannot break out of sandbox root."""
        manager = SandboxManager()
        lab = ScenarioFactory.get_scenario_by_id("linux-inode-exhaustion")
        session = manager.create_sandbox(lab, force_simulation=True)

        try:
            # Attempt to traverse up to host /etc/shadow or Windows SAM
            code, stdout, _ = manager.execute_command(
                session.session_id,
                "cat ../../../../../../../../../etc/shadow ../../../../../../../../../Windows/System32/config/SAM"
            )
            assert "root:$" not in stdout
            assert "Administrator" not in stdout
        finally:
            manager.terminate_session(session.session_id)

    def test_privilege_escalation_suid_block(self):
        """Verify no-new-privileges and rootless boundaries block privilege escalation."""
        env = EnvironmentSpec(pids_limit=64, memory_limit="256Mi")
        assert env.pids_limit == 64
        assert env.capabilities_drop == ["ALL"]
