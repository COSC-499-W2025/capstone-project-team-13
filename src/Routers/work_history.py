"""
src/Routers/work_history.py
===========================
Work history endpoints. All endpoints require authentication.
Users can only access and modify their own work history entries.

Endpoints
---------
GET    /work-history                get all work history entries for the authenticated user
POST   /work-history                add a new work history entry
DELETE /work-history/{work_id}      delete a work history entry
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from src.Databases.database import db_manager
from src.Services.auth_service import require_auth

router = APIRouter(prefix="/work-history", tags=["Work History"])


# ── request models ────────────────────────────────────────────────────────────

class WorkHistoryRequest(BaseModel):
    company: str
    role: str
    experience_type: Optional[str] = "work"
    start_date: str                   # ISO format: "2024-05-01"
    end_date: Optional[str] = None    # None means "present"
    location: Optional[str] = None
    bullets: Optional[list[str]] = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def get_work_history(user_id: int = Depends(require_auth)):
    """Return all work history entries for the authenticated user."""
    entries = db_manager.get_work_history_for_user(user_id)
    return {"work_history": [e.to_dict() for e in entries]}


@router.post("")
def add_work_history(body: WorkHistoryRequest, user_id: int = Depends(require_auth)):
    """Add a new work history entry for the authenticated user."""
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

    entry = db_manager.add_work_history({
        "user_id":    user_id,
        "company":    body.company,
        "role":       body.role,
        "experience_type": body.experience_type or "work",
        "start_date": start,
        "end_date":   end,
        "location":   body.location,
        "bullets":    body.bullets or [],
    })

    return {"message": "Work history entry added", "work_history": entry.to_dict()}


@router.delete("/{work_id}")
def delete_work_history(work_id: int, user_id: int = Depends(require_auth)):
    """Delete a work history entry. Only the owner can delete."""
    entries = db_manager.get_work_history_for_user(user_id)
    if not any(e.id == work_id for e in entries):
        raise HTTPException(
            status_code=404,
            detail="Work history entry not found or you do not have permission to delete it"
        )

    success = db_manager.delete_work_history(work_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete work history entry")

    return {"success": True, "message": "Work history entry deleted"}
