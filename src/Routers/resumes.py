"""
src/Routers/resumes.py
======================
Replaces the stub file.  All business logic lives in resume_export_service;
this file only handles HTTP concerns.

Endpoints
---------
POST /resume/generate               build & cache résumé data for a user
GET  /resume/{user_id}              return cached résumé JSON
POST /resume/{user_id}/edit         patch awards list, rebuild cached data
GET  /resume/{user_id}/download/pdf  stream one-page résumé as PDF
GET  /resume/{user_id}/download/docx stream one-page résumé as DOCX
"""

import io
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from src.Databases.database import db_manager
from src.Services.resume_export_service import (
    get_resume_preview_data,
    generate_resume_pdf,
    generate_resume_docx,
)

router = APIRouter(prefix="/resume", tags=["Resume"])


# ── request models ────────────────────────────────────────────────────────────

class ResumeEditRequest(BaseModel):
    awards: Optional[list[str]] = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_resume(user_id: int = 1):
    """Compile résumé from the database and persist it in the user record."""
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        data = get_resume_preview_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    db_manager.update_user(user_id, {"_resume": json.dumps(data)})
    return {"message": "Resume generated", "resume": data}


@router.get("/{user_id}")
def get_resume(user_id: int):
    """Return the most-recently generated résumé JSON."""
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found. Call POST /resume/generate first.",
        )
    return {"user_id": user_id, "resume": user.resume}


@router.post("/{user_id}/edit")
def edit_resume(user_id: int, body: ResumeEditRequest):
    """Patch the résumé (e.g. add/replace awards) and rebuild cached data."""
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.awards is not None:
        current = user.resume or {}
        current["awards"] = body.awards
        db_manager.update_user(user_id, {"_resume": json.dumps(current)})

    try:
        data = get_resume_preview_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db_manager.update_user(user_id, {"_resume": json.dumps(data)})
    return {"message": f"Resume {user_id} updated", "resume": data}


@router.get("/{user_id}/download/pdf")
def download_resume_pdf(user_id: int):
    """Stream résumé as a downloadable PDF."""
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        pdf_bytes = generate_resume_pdf(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    fname = f"resume_{user.first_name}_{user.last_name}.pdf".replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/{user_id}/download/docx")
def download_resume_docx(user_id: int):
    """Stream résumé as a downloadable DOCX."""
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        docx_bytes = generate_resume_docx(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {e}")

    fname = f"resume_{user.first_name}_{user.last_name}.docx".replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )