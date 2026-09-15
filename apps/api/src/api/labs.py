"""
REST API endpoints for Labs, Sandboxes, Troubleshooting, and Validators.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..core.config import settings
from ..services.lab_service import LabService

router = APIRouter(prefix="/labs", tags=["labs"])
lab_service = LabService(settings.LABS_DIR)


from packages.sandbox_runtime import RuntimeProvisioningError


class StartSessionRequest(BaseModel):
    force_simulation: bool = False


class ExecCommandRequest(BaseModel):
    command: str


class AskAdvisorRequest(BaseModel):
    task_id: str
    question: str
    recent_command: Optional[str] = None
    recent_output: Optional[str] = None


class ValidateTaskRequest(BaseModel):
    task_id: str


class SaveFileRequest(BaseModel):
    path: str
    content: str


@router.get("/tracks")
def get_tracks():
    return {"tracks": lab_service.get_tracks()}


@router.get("")
def list_labs(track: Optional[str] = None):
    labs = lab_service.list_labs(track)
    return [
        {
            "id": l.id,
            "version": l.version,
            "title": l.title,
            "track": l.track,
            "difficulty": l.difficulty.value,
            "estimated_minutes": l.estimated_minutes,
            "validation_status": l.validation_status.value,
            "objectives": l.objectives,
        }
        for l in labs
    ]


@router.get("/{lab_id}")
def get_lab_detail(lab_id: str):
    lab = lab_service.get_lab(lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail=f"Lab {lab_id} not found.")
    return lab.model_dump()


@router.post("/{lab_id}/session")
def start_session(lab_id: str, req: StartSessionRequest = StartSessionRequest()):
    try:
        return lab_service.start_session(lab_id, force_simulation=req.force_simulation)
    except RuntimeProvisioningError as exc:
        raise HTTPException(status_code=503, detail=f"Runtime provisioning failed: {str(exc)}")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/session/{session_id}/health")
def get_session_health(session_id: str):
    sess = lab_service.sandbox_manager.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return sess.health


@router.post("/session/{session_id}/exec")
def execute_command(session_id: str, req: ExecCommandRequest):
    return lab_service.execute_command(session_id, req.command)


@router.post("/session/{session_id}/advisor")
def ask_advisor(session_id: str, req: AskAdvisorRequest):
    try:
        return lab_service.ask_advisor(
            session_id=session_id,
            task_id=req.task_id,
            question=req.question,
            recent_command=req.recent_command,
            recent_output=req.recent_output,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/{session_id}/file")
def save_session_file(session_id: str, req: SaveFileRequest):
    try:
        lab_service.save_file(session_id, req.path, req.content)
        return {"session_id": session_id, "path": req.path, "status": "saved"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/{session_id}/validate")
def validate_task(session_id: str, req: ValidateTaskRequest):
    try:
        report = lab_service.validate_task(session_id, req.task_id)
        return report.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    success = lab_service.reset_session(session_id)
    return {"session_id": session_id, "reset": success}


@router.get("/session/{session_id}/residue")
def verify_session_residue(session_id: str):
    return lab_service.verify_session_residue(session_id)


@router.delete("/session/{session_id}")
def terminate_session(session_id: str):
    success = lab_service.sandbox_manager.terminate_session(session_id)
    return {"session_id": session_id, "terminated": success}

