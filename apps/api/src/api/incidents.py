"""
REST API endpoints for SEV-1/SEV-2 Incident Simulator.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.config import settings
from packages.incident_core import IncidentEngine

router = APIRouter(prefix="/incidents", tags=["incidents"])
incident_engine = IncidentEngine()


class StartIncidentRequest(BaseModel):
    session_id: str


class InspectCommandRequest(BaseModel):
    command: str


class HypothesisRequest(BaseModel):
    hypothesis_id: str


class MitigateRequest(BaseModel):
    command: str


@router.get("")
def list_incidents():
    incidents = incident_engine.catalog.list_all()
    return [
        {
            "id": inc.id,
            "title": inc.title,
            "severity": inc.severity.value,
            "summary": inc.summary,
            "impact": inc.impact,
            "affected_services": inc.affected_services,
        }
        for inc in incidents
    ]


@router.get("/{incident_id}")
def get_incident_detail(incident_id: str):
    inc = incident_engine.catalog.get(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    data = inc.model_dump()
    # Mask root cause and mitigation until resolved
    data["root_cause_explanation"] = "REDACTED: Formulate hypothesis and investigate telemetry."
    data["mitigation_command"] = "REDACTED: Determine appropriate SRE remediation."
    return data


@router.post("/{incident_id}/start")
def start_incident(incident_id: str, req: StartIncidentRequest):
    try:
        session = incident_engine.start_incident(incident_id, req.session_id)
        return {
            "session_id": session.session_id,
            "incident_id": session.incident.id,
            "title": session.incident.title,
            "severity": session.incident.severity.value,
            "status": session.status.value,
            "alerts": [a.model_dump() for a in session.incident.alerts],
            "topology": session.incident.topology,
            "initial_symptoms": session.incident.initial_symptoms,
            "hypotheses": [h.model_dump() for h in session.incident.hypotheses],
            "diagnostic_commands": session.incident.diagnostic_commands,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/{session_id}/inspect")
def inspect_command(session_id: str, req: InspectCommandRequest):
    session = incident_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    session.record_inspection(req.command)
    return {"status": session.status.value, "command": req.command}


@router.post("/session/{session_id}/hypothesis")
def test_hypothesis(session_id: str, req: HypothesisRequest):
    session = incident_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    session.test_hypothesis(req.hypothesis_id)
    for h in session.incident.hypotheses:
        if h.id == req.hypothesis_id:
            return {
                "hypothesis_id": h.id,
                "statement": h.statement,
                "plausible": h.plausible,
                "evidence_required": h.evidence_required,
                "disproven_by": h.disproven_by,
            }

    return {"status": "recorded", "hypothesis_id": req.hypothesis_id}


@router.post("/session/{session_id}/mitigate")
def apply_mitigation(session_id: str, req: MitigateRequest):
    session = incident_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    success = session.apply_fix(req.command)
    return {
        "status": session.status.value,
        "mitigated": success,
        "feedback": "Remediation command matched mitigation strategy! Verify system recovery." if success else "Command executed, but failure symptom persists. Re-inspect telemetry.",
    }


@router.post("/session/{session_id}/resolve")
def resolve_incident(session_id: str):
    session = incident_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    score = session.verify_resolution()
    return {
        "status": session.status.value,
        "score": score.model_dump(),
        "root_cause_revealed": session.incident.root_cause_explanation,
        "remediation_revealed": session.incident.remediation_steps,
        "prevention_measures": session.incident.prevention_measures,
    }
