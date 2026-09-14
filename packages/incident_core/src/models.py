"""
Domain models for SEV-1/SEV-2 Incident Simulator and SRE Scoring.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"


class IncidentStatus(str, Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"


class AlertEvent(BaseModel):
    id: str
    name: str
    severity: str  # critical, warning, page
    status: str  # firing, resolved
    started_at: str
    description: str
    labels: Dict[str, str] = Field(default_factory=dict)


class IncidentHypothesis(BaseModel):
    id: str
    statement: str
    plausible: bool
    evidence_required: str
    disproven_by: Optional[str] = None


class IncidentSpec(BaseModel):
    id: str
    title: str
    severity: IncidentSeverity
    summary: str
    impact: str
    initial_symptoms: List[str]
    topology: Dict[str, Any]
    affected_services: List[str]
    root_cause_explanation: str
    remediation_steps: List[str]
    prevention_measures: List[str]
    alerts: List[AlertEvent] = Field(default_factory=list)
    hypotheses: List[IncidentHypothesis] = Field(default_factory=list)
    diagnostic_commands: List[Dict[str, str]] = Field(default_factory=list)
    mitigation_command: str
    verification_check: str


class IncidentScore(BaseModel):
    detection_score: int = Field(default=0, ge=0, le=100)
    evidence_gathering_score: int = Field(default=0, ge=0, le=100)
    hypothesis_score: int = Field(default=0, ge=0, le=100)
    investigation_score: int = Field(default=0, ge=0, le=100)
    root_cause_score: int = Field(default=0, ge=0, le=100)
    fix_score: int = Field(default=0, ge=0, le=100)
    verification_score: int = Field(default=0, ge=0, le=100)
    prevention_score: int = Field(default=0, ge=0, le=100)
    total_score: int = Field(default=0, ge=0, le=100)
    feedback: List[str] = Field(default_factory=list)
