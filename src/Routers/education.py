"""
src/Routers/education.py
========================
Education endpoints. All endpoints require authentication.
Users can only access and modify their own education entries.

Endpoints
---------
GET    /education                  get all education entries for the authenticated user
POST   /education                  add a new education entry
DELETE /education/{education_id}   delete an education entry
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from src.Databases.database import db_manager
from src.Services.auth_service import require_auth

router = APIRouter(prefix="/education", tags=["Education"])


# ── request models ────────────────────────────────────────────────────────────

class EducationRequest(BaseModel):
    institution: str
    degree_type: str
    topic: str
    start_date: str          # ISO format: "2021-09-01"
    end_date: Optional[str] = None  # None means "present"
    location: Optional[str] = None
    gpa: Optional[str] = None
    details: Optional[list[str]] = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def get_education(user_id: int = Depends(require_auth)):
    """Return all education entries for the authenticated user."""
    entries = db_manager.get_education_for_user(user_id)
    return {"education": [e.to_dict() for e in entries]}


@router.post("")
def add_education(body: EducationRequest, user_id: int = Depends(require_auth)):
    """Add a new education entry for the authenticated user."""
    from datetime import datetime

    try:
        start = datetime.fromisoformat(body.start_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid start_date format. Use ISO format: YYYY-MM-DD")

    end = None
    if body.end_date:
        try:
            end = datetime.fromisoformat(body.end_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid end_date format. Use ISO format: YYYY-MM-DD")

    entry = db_manager.add_education({
        "user_id":     user_id,
        "institution": body.institution,
        "degree_type": body.degree_type,
        "topic":       body.topic,
        "start_date":  start,
        "end_date":    end,
        "location":    body.location,
        "gpa":         body.gpa,
        "details":     body.details or [],
    })

    return {"message": "Education entry added", "education": entry.to_dict()}


@router.delete("/{education_id}")
def delete_education(education_id: int, user_id: int = Depends(require_auth)):
    """Delete an education entry. Only the owner can delete."""
    entries = db_manager.get_education_for_user(user_id)
    if not any(e.id == education_id for e in entries):
        raise HTTPException(
            status_code=404,
            detail="Education entry not found or you do not have permission to delete it"
        )

    success = db_manager.delete_education(education_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete education entry")

    return {"success": True, "message": "Education entry deleted"}