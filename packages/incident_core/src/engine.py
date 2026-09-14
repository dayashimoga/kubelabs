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
        """Calculate SRE score across 7 production dimensions."""
        now = time.time()
        self.resolved_at = now
        self.status = IncidentStatus.RESOLVED

        # 1. Detection score (Faster ack = higher score; acknowledging within 60s gives full score 100)
        ack_delay = max(0.0, (self.acknowledged_at - self.started_at)) if self.acknowledged_at else 300.0
        if ack_delay <= 60:
            detection_score = 100
        else:
            detection_score = max(50, min(100, int(round(100 - ((ack_delay - 60) / 10)))))

        # 2. Evidence Gathering score (Diagnostic telemetry and commands)
        evidence_gathering_score = min(100, 50 + len(self.inspected_commands) * 20) if self.inspected_commands else 50

        # 3. Hypothesis score (Hypothesis formulations and tests)
        hypothesis_score = min(100, 50 + len(self.tested_hypotheses) * 35) if self.tested_hypotheses else 50

        # Investigation composite score
        investigation_score = int((evidence_gathering_score + hypothesis_score) / 2)

        # 4. Root Cause score
        root_cause_score = 90 if self.tested_hypotheses else 60

        # 5. Fix score
        fix_score = 95 if self.status in [IncidentStatus.MITIGATING, IncidentStatus.RESOLVED] else 30

        # 6. Verification score
        verification_score = 90

        # 7. Prevention score
        prevention_score = 85

        # Penalty for hint requests
        penalty = self.hint_requests_count * 5

        total = int((detection_score + evidence_gathering_score + hypothesis_score + root_cause_score + fix_score + verification_score + prevention_score) / 7)
        total = max(10, total - penalty)

        feedback = [
            f"Detection: Acknowledged in {int(ack_delay)}s.",
            f"Evidence Gathering: Executed {len(self.inspected_commands)} diagnostic probes.",
            f"Hypothesis: Tested {len(self.tested_hypotheses)} root-cause hypotheses.",
            f"Root Cause: Thorough analysis of subsystem failure.",
            f"Mitigation: Applied verified remediation commands.",
            f"Verification: Automated system state confirmed healthy.",
            f"Prevention: Reviewed architectural safeguards to stop recurrence.",
        ]
        if penalty > 0:
            feedback.append(f"Hint penalty deducted: -{penalty} points.")

        return IncidentScore(
            detection_score=detection_score,
            evidence_gathering_score=evidence_gathering_score,
            hypothesis_score=hypothesis_score,
            investigation_score=investigation_score,
            root_cause_score=root_cause_score,
            fix_score=fix_score,
            verification_score=verification_score,
            prevention_score=prevention_score,
            total_score=total,
            feedback=feedback,
        )

    def generate_post_mortem(self) -> str:
        ttd = int((self.acknowledged_at - self.started_at)) if self.acknowledged_at else 0
        ttm = int((self.mitigated_at - self.started_at)) if self.mitigated_at else 0
        ttr = int((self.resolved_at - self.started_at)) if self.resolved_at else int(time.time() - self.started_at)

        md = f"""# SRE Incident Post-Mortem: {self.incident.title}
**Severity**: {self.incident.severity.value} | **Status**: {self.status.value.upper()}

## Executive Summary
{self.incident.summary}

- **Customer Impact**: {self.incident.impact}
- **Time to Detect (TTD)**: {ttd} seconds
- **Time to Mitigate (TTM)**: {ttm} seconds
- **Time to Resolve (TTR)**: {ttr} seconds
- **Affected Microservices**: {', '.join(self.incident.affected_services)}

## Root Cause Analysis
{self.incident.root_cause_explanation}

## Incident Timeline
- **T+0s**: Anomaly detected by automated SLO monitoring and alert routing.
- **T+{ttd}s**: On-call SRE acknowledged alert and initiated War Room triage.
- **T+{ttm}s**: Mitigation executed: `{self.applied_fixes[-1] if self.applied_fixes else self.incident.mitigation_command}`.
- **T+{ttr}s**: Service restoration confirmed via synthetic probing and SLI convergence.

## Remediation Steps
{chr(10).join(f"- {s}" for s in self.incident.remediation_steps)}

## Preventative Safeguards & Action Items
{chr(10).join(f"- [ ] {p}" for p in self.incident.prevention_measures)}
"""
        return md



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

    def start_random_incident(self, session_id: str) -> IncidentSession:
        import random
        import copy
        incidents = self.catalog.list_all()
        if not incidents:
            raise ValueError("No incidents available in catalog.")
        selected = random.choice(incidents)
        spec = copy.deepcopy(selected)
        noise_symptoms = [
            "Transient 1.2% CPU jitter observed on neighboring ingress proxies.",
            "Periodic BGP route flap noted in secondary availability zone.",
            "Cron batch analytics report triggered elevated disk read I/O.",
            "DNS cache TTL expiration spike observed on internal CoreDNS.",
        ]
        spec.initial_symptoms.append(random.choice(noise_symptoms))
        session = IncidentSession(session_id, spec)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[IncidentSession]:
        return self.sessions.get(session_id)
