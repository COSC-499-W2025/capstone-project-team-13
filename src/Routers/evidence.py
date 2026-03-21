"""
src/Routers/evidence.py
=======================
HTTP endpoints for the Evidence management system.
All evidence is stored in the project's success_evidence JSON column.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.Databases.database import db_manager
from src.Services.auth_service import get_current_user_id

router = APIRouter(prefix="/evidence", tags=["Evidence"])


# ── Request models ─────────────────────────────────────────────────────────────

class MetricRequest(BaseModel):
    metric_name: str
    value: str
    description: Optional[str] = ""

class FeedbackRequest(BaseModel):
    text: str
    source: Optional[str] = ""
    rating: Optional[int] = None

class AchievementRequest(BaseModel):
    description: str
    date: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_project_or_404(project_id: int, user_id: Optional[int]):
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user_id is not None and project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your project")
    return project

def _get_evidence_manager():
    try:
        from src.Evidence.evidenceManager import evidence_manager
        return evidence_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="Evidence module not available")


# ── GET evidence ───────────────────────────────────────────────────────────────

@router.get("/{project_id}")
def get_evidence(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Return all evidence for a project."""
    _get_project_or_404(project_id, user_id)
    em = _get_evidence_manager()
    evidence = em.get_evidence(project_id)
    return evidence or {}


# ── Auto-extract ───────────────────────────────────────────────────────────────

@router.post("/{project_id}/extract")
def auto_extract(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Automatically extract evidence from the project files."""
    project = _get_project_or_404(project_id, user_id)
    em = _get_evidence_manager()
    try:
        evidence = em.extract_and_store_evidence(project, project.file_path)
        return {"extracted": True, "evidence": evidence or {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


# ── Add metric ─────────────────────────────────────────────────────────────────

@router.post("/{project_id}/metric")
def add_metric(
    project_id: int,
    body: MetricRequest,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Add a manual metric to a project's evidence."""
    _get_project_or_404(project_id, user_id)
    em = _get_evidence_manager()
    # Try to cast value to number
    value: object = body.value
    try:
        value = float(body.value) if "." in body.value else int(body.value)
    except (ValueError, TypeError):
        pass
    success = em.add_manual_metric(project_id, body.metric_name, value, body.description or "")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save metric")
    return {"added": True, "metric_name": body.metric_name, "value": value}


# ── Add feedback ───────────────────────────────────────────────────────────────

@router.post("/{project_id}/feedback")
def add_feedback(
    project_id: int,
    body: FeedbackRequest,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Add feedback or a testimonial to a project's evidence."""
    _get_project_or_404(project_id, user_id)
    em = _get_evidence_manager()
    if body.rating is not None and not (1 <= body.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    success = em.add_feedback(project_id, body.text, body.source or "", body.rating)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    return {"added": True}


# ── Add achievement ────────────────────────────────────────────────────────────

@router.post("/{project_id}/achievement")
def add_achievement(
    project_id: int,
    body: AchievementRequest,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Add an achievement or award to a project's evidence."""
    _get_project_or_404(project_id, user_id)
    em = _get_evidence_manager()
    success = em.add_achievement(project_id, body.description, body.date)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save achievement")
    return {"added": True}


# ── Clear evidence ─────────────────────────────────────────────────────────────

@router.delete("/{project_id}")
def clear_evidence(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Clear all evidence for a project."""
    _get_project_or_404(project_id, user_id)
    em = _get_evidence_manager()
    success = em.clear_evidence(project_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear evidence")
    return {"cleared": True, "project_id": project_id}