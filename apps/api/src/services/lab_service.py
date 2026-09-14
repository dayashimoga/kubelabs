"""
Lab Service: Manages lab registry, active sandbox sessions,
hint unlocking with penalty calculation, and validation execution.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from ..core.config import settings

from packages.lab_schema import LabSpec, TaskSpec, ValidationReport, ValidationOverallStatus, LabRegistry, ScenarioFactory
from packages.validator_core import ValidatorEngine, ExecutionContext
from packages.sandbox_runtime import SandboxManager, SandboxSession
from .troubleshooting_service import TroubleshootingAdvisor


class LabService:
    def __init__(self, labs_dir: Path):
        self.labs_dir = labs_dir
        self.registry = LabRegistry()
        self.sandbox_manager = SandboxManager()
        self.validator_engine = ValidatorEngine()
        self.advisor = TroubleshootingAdvisor()
        self.reload_labs()

    def reload_labs(self) -> int:
        self.registry.load_from_directory(self.labs_dir)
        for s in ScenarioFactory.get_all_scenarios():
            if s.id not in self.registry._labs:
                self.registry.register(s)
        return len(self.registry.list_all())

    def list_labs(self, track: Optional[str] = None) -> List[LabSpec]:
        if track:
            return self.registry.list_by_track(track)
        return self.registry.list_all()

    def get_lab(self, lab_id: str) -> Optional[LabSpec]:
        return self.registry.get_by_id(lab_id)

    def get_tracks(self) -> List[str]:
        return self.registry.get_tracks()

    def start_session(self, lab_id: str, force_simulation: bool = False) -> Dict[str, Any]:
        lab = self.get_lab(lab_id)
        if not lab:
            raise ValueError(f"Lab '{lab_id}' not found.")

        session = self.sandbox_manager.create_sandbox(lab, force_simulation=force_simulation)
        return {
            "session_id": session.session_id,
            "lab_id": lab.id,
            "title": lab.title,
            "track": lab.track,
            "is_container": session.is_container,
            "runtime_classification": session.runtime_classification.value,
            "expires_at": session.expires_at,
            "health": session.health,
            "tasks": [t.model_dump() for t in lab.tasks],
            "topology": lab.topology.model_dump() if lab.topology else None,
        }

    def reset_session(self, session_id: str) -> bool:
        return self.sandbox_manager.reset_sandbox(session_id)

    def verify_session_residue(self, session_id: str) -> Dict[str, Any]:
        clean, residue = self.sandbox_manager.verify_zero_residue(session_id)
        return {"clean": clean, "residue": residue}

    def execute_command(self, session_id: str, command: str) -> Dict[str, Any]:
        exit_code, stdout, stderr = self.sandbox_manager.execute_command(session_id, command)
        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}

    def ask_advisor(
        self,
        session_id: str,
        task_id: str,
        question: str,
        recent_command: Optional[str] = None,
        recent_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = self.sandbox_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        target_task = None
        for t in session.lab_spec.tasks:
            if t.id == task_id:
                target_task = t
                break
        if not target_task and session.lab_spec.tasks:
            target_task = session.lab_spec.tasks[0]

        return self.advisor.answer_diagnostic_question(
            session.lab_spec, target_task, question, recent_command, recent_output
        )

    def validate_task(self, session_id: str, task_id: str) -> ValidationReport:
        session = self.sandbox_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired.")

        target_task: Optional[TaskSpec] = None
        for t in session.lab_spec.tasks:
            if t.id == task_id:
                target_task = t
                break

        if not target_task:
            raise ValueError(f"Task {task_id} not found in lab {session.lab_id}")

        sim = session.simulator
        sim_state = sim.state if sim else {}

        context = ExecutionContext(
            sandbox_id=session.session_id,
            container_id=session.container_id,
            podman_executor=self.sandbox_manager.podman if session.is_container else None,
            simulation_state=sim_state,
        )

        return self.validator_engine.validate_rules(target_task.validators, context)
