"""
Sandbox Manager: Unified orchestrator for container and simulation sandboxes.
Enforces TTL expiration, security isolation, and automated cleanup.
"""

import time
import uuid
import threading
from typing import Any, Dict, Optional, Tuple
from packages.lab_schema import LabSpec, EnvironmentType
from .executor import PodmanSandboxExecutor
from .simulator import DeterministicSimulator


class SandboxSession:
    """Represents an active learning sandbox instance."""

    def __init__(
        self,
        session_id: str,
        lab_id: str,
        lab_spec: LabSpec,
        is_container: bool = False,
        container_id: Optional[str] = None,
        simulator: Optional[DeterministicSimulator] = None,
        ttl_seconds: int = 1800,
    ):
        self.session_id = session_id
        self.lab_id = lab_id
        self.lab_spec = lab_spec
        self.is_container = is_container
        self.container_id = container_id
        self.simulator = simulator or DeterministicSimulator(lab_id, lab_spec.initial_state.seed_data)
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def touch(self):
        self.last_activity = time.time()


class SandboxManager:
    """Manages lifecycle of sandboxes with automatic background TTL sweeper."""

    def __init__(self):
        self.sessions: Dict[str, SandboxSession] = {}
        self.podman = PodmanSandboxExecutor()
        self._lock = threading.Lock()
        self._stop_sweeper = threading.Event()
        self._sweeper_thread = threading.Thread(target=self._ttl_sweeper_loop, daemon=True)
        self._sweeper_thread.start()

    def create_sandbox(self, lab: LabSpec, force_simulation: bool = False) -> SandboxSession:
        """Provision a sandbox for the given lab specification."""
        session_id = str(uuid.uuid4())[:8]

        use_container = False
        container_id = None

        if (
            not force_simulation
            and lab.environment.type in [EnvironmentType.CONTAINER, EnvironmentType.HYBRID]
            and self.podman.available
        ):
            try:
                res = self.podman.create_sandbox(
                    sandbox_id=session_id,
                    env_spec=lab.environment,
                    initial_state=lab.initial_state,
                    ttl_seconds=lab.cleanup_policy.ttl_seconds,
                )
                container_id = res["container_id"]
                use_container = True
            except Exception as exc:
                print(f"[SandboxManager] Container launch fallback to simulation: {exc}")
                use_container = False

        sim = DeterministicSimulator(lab.id, lab.initial_state.seed_data)
        session = SandboxSession(
            session_id=session_id,
            lab_id=lab.id,
            lab_spec=lab,
            is_container=use_container,
            container_id=container_id,
            simulator=sim,
            ttl_seconds=lab.cleanup_policy.ttl_seconds,
        )

        with self._lock:
            self.sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[SandboxSession]:
        with self._lock:
            session = self.sessions.get(session_id)
            if session and not session.is_expired():
                session.touch()
                return session
            return None

    def execute_command(self, session_id: str, command: str) -> Tuple[int, str, str]:
        """Execute command in either container or simulation sandbox."""
        session = self.get_session(session_id)
        if not session:
            return 1, "", f"Sandbox session {session_id} not found or expired."

        session.touch()
        if session.is_container and session.container_id:
            return self.podman.exec_command(session.container_id, command)
        else:
            return session.simulator.execute_command(command)

    def terminate_session(self, session_id: str) -> bool:
        """Terminate and clean up a sandbox session."""
        with self._lock:
            session = self.sessions.pop(session_id, None)

        if not session:
            return False

        if session.is_container and session.container_id:
            self.podman.cleanup_container(session.container_id)
        return True

    def _ttl_sweeper_loop(self):
        """Background thread that cleans up expired sessions periodically."""
        while not self._stop_sweeper.is_set():
            time.sleep(30)
            now = time.time()
            expired_ids = []
            with self._lock:
                for sid, sess in self.sessions.items():
                    if now > sess.expires_at:
                        expired_ids.append(sid)

            for sid in expired_ids:
                print(f"[SandboxManager] Sweeping expired sandbox session: {sid}")
                self.terminate_session(sid)
