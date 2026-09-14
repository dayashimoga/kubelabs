"""
Sandbox Manager: Unified orchestrator for container, multi-container, and simulation sandboxes.
Enforces TTL expiration, security isolation, terminal scrollback buffering, and automated cleanup.
"""

import time
import uuid
import threading
from typing import Any, Dict, List, Optional, Tuple
from packages.lab_schema import LabSpec, LabRuntimeClassification
from .broker import EnvironmentBroker
from .scenario_injector import ScenarioInjector
from .simulator import DeterministicSimulator
from .executor import PodmanSandboxExecutor



class SandboxSession:
    """Represents an active learning sandbox instance."""

    def __init__(
        self,
        session_id: str,
        lab_id: str,
        lab_spec: LabSpec,
        broker_record: Dict[str, Any],
        ttl_seconds: int = 1800,
    ):
        self.session_id = session_id
        self.lab_id = lab_id
        self.lab_spec = lab_spec
        self.broker_record = broker_record
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.last_activity = time.time()
        self.scrollback_buffer: List[str] = []
        self._max_scrollback = 1000

    @property
    def is_container(self) -> bool:
        return self.broker_record.get("provider", "").startswith("podman")

    @property
    def container_id(self) -> Optional[str]:
        return self.broker_record.get("container_id")

    @property
    def runtime_classification(self) -> LabRuntimeClassification:
        return self.broker_record.get("classification", LabRuntimeClassification.REAL)

    @property
    def simulator(self) -> Optional[DeterministicSimulator]:
        return self.broker_record.get("simulator")

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def touch(self):
        self.last_activity = time.time()

    def append_scrollback(self, text: str):
        lines = text.splitlines(keepends=True)
        self.scrollback_buffer.extend(lines)
        if len(self.scrollback_buffer) > self._max_scrollback:
            self.scrollback_buffer = self.scrollback_buffer[-self._max_scrollback:]

    def get_scrollback(self) -> str:
        return "".join(self.scrollback_buffer)


class SandboxManager:
    """Manages lifecycle of sandboxes with automatic background TTL sweeper."""

    def __init__(self, podman_binary: str = "podman"):
        self.sessions: Dict[str, SandboxSession] = {}
        self.broker = EnvironmentBroker(podman_binary)
        self._lock = threading.Lock()
        self._stop_sweeper = threading.Event()
        self._sweeper_thread = threading.Thread(target=self._ttl_sweeper_loop, daemon=True)
        self._sweeper_thread.start()

    @property
    def podman(self) -> PodmanSandboxExecutor:
        return self.broker.podman_executor

    def create_sandbox(self, lab: LabSpec, force_simulation: bool = False) -> SandboxSession:
        """Provision a sandbox for the given lab specification using EnvironmentBroker."""
        session_id = str(uuid.uuid4())[:8]

        # Use broker to start environment
        if force_simulation:
            broker_record = {
                "sandbox_id": session_id,
                "provider": "simulator",
                "classification": LabRuntimeClassification.SIMULATED,
                "simulator": self.broker._start_multi_container if False else None,
                "created_at": time.time(),
                "lab_spec": lab,
            }
            # Fallback simulator instance
            from .simulator import DeterministicSimulator
            broker_record["simulator"] = DeterministicSimulator(lab.id, lab.initial_state.seed_data)
            self.broker.active_environments[session_id] = broker_record
        else:
            broker_record = self.broker.start_environment(session_id, lab)

        session = SandboxSession(
            session_id=session_id,
            lab_id=lab.id,
            lab_spec=lab,
            broker_record=broker_record,
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

    def execute_command(self, session_id: str, command: str, target_container: Optional[str] = None) -> Tuple[int, str, str]:
        """Execute command via EnvironmentBroker."""
        session = self.get_session(session_id)
        if not session:
            return 1, "", f"Sandbox session {session_id} not found or expired."

        session.touch()
        code, out, err = self.broker.execute_command(session_id, command, target_container)

        # Buffer command output in session scrollback
        if out:
            session.append_scrollback(out)
        if err:
            session.append_scrollback(err)

        return code, out, err

    def reset_sandbox(self, session_id: str) -> bool:
        """Reset sandbox environment to initial broken/fault state."""
        session = self.get_session(session_id)
        if not session:
            return False
        return self.broker.reset_environment(session_id)

    def terminate_session(self, session_id: str) -> bool:
        """Terminate and clean up a sandbox session."""
        with self._lock:
            session = self.sessions.pop(session_id, None)

        if not session:
            return False

        return self.broker.destroy_environment(session_id)

    def verify_zero_residue(self, session_id: str) -> Tuple[bool, List[str]]:
        """Verify that no containers, networks, or volumes remain for this sandbox."""
        return self.broker.verify_zero_residue(session_id)

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
