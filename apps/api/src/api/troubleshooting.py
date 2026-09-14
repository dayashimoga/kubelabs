"""
REST API endpoints for the Production Troubleshooting Library.
Provides searchable, filterable catalog of real-world failure patterns
grouped by difficulty tier and technology without spoiling root causes.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from packages.lab_schema import LabRegistry, ScenarioFactory
from packages.incident_core import IncidentCatalog

router = APIRouter(prefix="/troubleshooting", tags=["troubleshooting"])

# In-memory registry caches
_registry = LabRegistry()
try:
    from pathlib import Path
    root = Path(__file__).resolve().parents[4]
    _registry.load_from_directory(root / "labs")
except Exception:
    pass


class TroubleshootingItem(BaseModel):
    id: str
    title: str
    track: str
    difficulty: str
    runtime_classification: str
    symptoms: List[str]
    diagnostic_commands: List[str]
    category: str
    type: str  # "lab" or "incident"


@router.get("/search")
def search_troubleshooting(
    q: Optional[str] = Query(None, description="Search term (e.g. CrashLoopBackOff, 503, OOMKilled, DNS, Pending, High CPU)"),
    track: Optional[str] = Query(None, description="Technology track filter"),
    difficulty: Optional[str] = Query(None, description="Difficulty tier filter (beginner, intermediate, advanced, production)"),
    runtime: Optional[str] = Query(None, description="Runtime classification (real, emulated, simulated)"),
):
    """Search and filter the Troubleshooting Library across all cataloged failure modes."""
    # Gather all labs
    all_labs = {l.id: l for l in _registry.list_all()}
    for l in ScenarioFactory.get_all_scenarios():
        all_labs[l.id] = l

    items: List[TroubleshootingItem] = []

    for lab in all_labs.values():
        symptoms = []
        if lab.common_errors:
            symptoms.extend(lab.common_errors)
        if lab.what_why:
            symptoms.append(lab.what_why[:120] + "...")

        diag_cmds = []
        if lab.troubleshooting_workflow:
            diag_cmds.extend(lab.troubleshooting_workflow[:2])

        item = TroubleshootingItem(
            id=lab.id,
            title=lab.title,
            track=lab.track,
            difficulty=lab.difficulty.value if hasattr(lab.difficulty, "value") else str(lab.difficulty),
            runtime_classification=lab.runtime_classification.value if hasattr(lab.runtime_classification, "value") else str(lab.runtime_classification),
            symptoms=symptoms if symptoms else ["Service degradation or unexpected exit condition detected."],
            diagnostic_commands=diag_cmds if diag_cmds else ["Inspect container logs and system metrics."],
            category=lab.track,
            type="lab",
        )
        items.append(item)

    # Gather incidents
    inc_catalog = IncidentCatalog()
    for inc in inc_catalog.list_all():
        diag_strings = [
            cmd["command"] if isinstance(cmd, dict) and "command" in cmd else str(cmd)
            for cmd in inc.diagnostic_commands[:2]
        ]
        item = TroubleshootingItem(
            id=inc.id,
            title=inc.title,
            track="sre-incident",
            difficulty="production" if inc.severity.value in ["SEV-1", "SEV-0"] else "advanced",
            runtime_classification="real",
            symptoms=inc.initial_symptoms,
            diagnostic_commands=diag_strings if diag_strings else ["Inspect alerts and service mesh metrics."],
            category="sre",
            type="incident",
        )
        items.append(item)

    # Filtering
    filtered = items

    if q:
        query_lower = q.lower().strip()
        filtered = [
            i for i in filtered
            if query_lower in i.title.lower()
            or query_lower in i.track.lower()
            or query_lower in i.id.lower()
            or any(query_lower in s.lower() for s in i.symptoms)
            or any(query_lower in d.lower() for d in i.diagnostic_commands)
        ]

    if track and track != "all":
        filtered = [i for i in filtered if i.track.lower() == track.lower()]

    if difficulty and difficulty != "all":
        filtered = [i for i in filtered if i.difficulty.lower() == difficulty.lower()]

    if runtime and runtime != "all":
        filtered = [i for i in filtered if i.runtime_classification.lower() == runtime.lower()]

    # Group results by difficulty tier as requested by Requirement 8
    grouped: Dict[str, List[Dict[str, Any]]] = {
        "beginner": [],
        "intermediate": [],
        "advanced": [],
        "production": [],
    }

    for item in filtered:
        diff_key = item.difficulty.lower()
        if diff_key in grouped:
            grouped[diff_key].append(item.model_dump())
        else:
            grouped["intermediate"].append(item.model_dump())

    return {
        "total_results": len(filtered),
        "results": [i.model_dump() for i in filtered],
        "grouped_by_difficulty": grouped,
    }
