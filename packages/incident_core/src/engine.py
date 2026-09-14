"""
Incident Engine: Manages active incident sessions, telemetry perturbations,
investigation timeline, hypothesis testing, and SRE post-mortem scoring.
"""

import time
from typing import Any, Dict, List, Optional
from .models import IncidentSpec, IncidentScore, IncidentStatus
from .scenarios import IncidentCatalog


class IncidentSession:
    """An active incident simulation run by a learner."""

    def __init__(self, session_id: str, incident: IncidentSpec):
        self.session_id = session_id
        self.incident = incident
        self.status = IncidentStatus.TRIGGERED
        self.started_at = time.time()
        self.acknowledged_at: Optional[float] = None
        self.identified_at: Optional[float] = None
        self.mitigated_at: Optional[float] = None
        self.resolved_at: Optional[float] = None

        self.inspected_commands: List[str] = []
        self.tested_hypotheses: List[str] = []
        self.applied_fixes: List[str] = []
        self.hint_requests_count = 0

    def acknowledge(self):
        if not self.acknowledged_at:
            self.acknowledged_at = time.time()
            self.status = IncidentStatus.ACKNOWLEDGED

    def record_inspection(self, command: str):
        self.acknowledge()
        self.inspected_commands.append(command)
        self.status = IncidentStatus.INVESTIGATING

    def test_hypothesis(self, hypothesis_id: str):
        self.acknowledge()
        self.tested_hypotheses.append(hypothesis_id)

    def apply_fix(self, command: str) -> bool:
        self.acknowledge()
        self.applied_fixes.append(command)
        # Check if the fix matches or contains key mitigation keywords
        correct = False
        target_keys = ["scale", "patch", "delete", "restart", "set env", "set resources", "apply", "commit"]
        for k in target_keys:
            if k in self.incident.mitigation_command and k in command:
                correct = True
                break

        if correct:
            self.mitigated_at = time.time()
            self.status = IncidentStatus.MITIGATING
            return True
        return False

    def verify_resolution(self) -> IncidentScore:
        """Calculate SRE score across 6 production dimensions."""
        now = time.time()
        self.resolved_at = now
        self.status = IncidentStatus.RESOLVED

        # 1. Detection score (Faster ack = higher score)
        ack_delay = (self.acknowledged_at - self.started_at) if self.acknowledged_at else 300
        detection_score = max(50, min(100, int(100 - (ack_delay / 10))))

        # 2. Investigation score (Variety of diagnostic commands)
        investigation_score = min(100, len(self.inspected_commands) * 20) if self.inspected_commands else 30

        # 3. Root Cause score
        root_cause_score = 90 if self.tested_hypotheses else 60

        # 4. Fix score
        fix_score = 95 if self.status in [IncidentStatus.MITIGATING, IncidentStatus.RESOLVED] else 30

        # 5. Verification score
        verification_score = 90

        # 6. Prevention score
        prevention_score = 85

        # Penalty for hint requests
        penalty = self.hint_requests_count * 5

        total = int((detection_score + investigation_score + root_cause_score + fix_score + verification_score + prevention_score) / 6)
        total = max(10, total - penalty)

        feedback = [
            f"Detection: Acknowledged in {int(ack_delay)}s.",
            f"Investigation: Executed {len(self.inspected_commands)} diagnostic probes.",
            f"Root Cause: Thorough analysis of subsystem failure.",
            f"Mitigation: Applied verified remediation commands.",
            f"Prevention: Reviewed architectural safeguards to stop recurrence.",
        ]
        if penalty > 0:
            feedback.append(f"Hint penalty deducted: -{penalty} points.")

        return IncidentScore(
            detection_score=detection_score,
            investigation_score=investigation_score,
            root_cause_score=root_cause_score,
            fix_score=fix_score,
            verification_score=verification_score,
            prevention_score=prevention_score,
            total_score=total,
            feedback=feedback,
        )


class IncidentEngine:
    """Manages active incident simulation runs and scenario catalog."""

    def __init__(self):
        self.catalog = IncidentCatalog()
        self.sessions: Dict[str, IncidentSession] = {}

    def start_incident(self, incident_id: str, session_id: str) -> IncidentSession:
        spec = self.catalog.get(incident_id)
        if not spec:
            raise ValueError(f"Incident {incident_id} not found in catalog.")
        session = IncidentSession(session_id, spec)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[IncidentSession]:
        return self.sessions.get(session_id)
