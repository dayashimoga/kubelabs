"""
REST API endpoints for Assessments & Quizzes.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])
assessment_service = AssessmentService()


class GradeSubmissionRequest(BaseModel):
    answers: Dict[str, Any]


@router.get("/{track}")
def get_track_questions(track: str):
    questions = assessment_service.get_questions_for_track(track)
    return {"track": track, "questions": questions}


@router.post("/{track}/submit")
def submit_answers(track: str, req: GradeSubmissionRequest):
    return assessment_service.grade_submission(track, req.answers)
