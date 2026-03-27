"""
src/Routers/resumes.py
======================
Resume API endpoints. All business logic lives in resume_service and
resume_export_service. This file handles HTTP concerns only.

All endpoints require authentication — resume features are not available
to guests. Users can only access/modify bullets for their own projects.

Endpoints
---------
Per-project bullet endpoints:
  POST   /resume/projects/{project_id}/generate    generate & store bullets
  GET    /resume/projects/{project_id}             get stored bullets
  POST   /resume/projects/{project_id}/edit        edit bullets / header
  POST   /resume/projects/{project_id}/regenerate  regenerate all bullets
  GET    /resume/projects/{project_id}/ats         view ATS scores
  DELETE /resume/projects/{project_id}             delete stored bullets

Full resume endpoints:
  POST   /resume/generate      smart generate full resume (fills missing bullets)
  GET    /resume               get stored resume JSON
  POST   /resume/save          save enriched resume (after frontend adds extras)
  GET    /resume/download/pdf  export resume as PDF
  GET    /resume/download/docx export resume as DOCX
"""

import io

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from src.Databases.database import db_manager
from src.Services.auth_service import require_auth
from src.Services.resume_service import (
    get_project_bullets,
    generate_project_bullets,
    regenerate_project_bullets,
    edit_project_bullets,
    get_project_ats,
    delete_project_bullets,
    generate_full_resume,
    get_full_resume,
    save_full_resume,
)
from src.Services.resume_export_service import (
    generate_resume_pdf,
    generate_resume_docx,
    get_resume_page_count,
)

router = APIRouter(prefix="/resume", tags=["Resume"])


# ── request models ────────────────────────────────────────────────────────────

class GenerateBulletsRequest(BaseModel):
    num_bullets: int = 3


class EditBulletsRequest(BaseModel):
    bullets: list[str]
    header: Optional[str] = None


# ── per-project bullet endpoints ──────────────────────────────────────────────

@router.post("/projects/{project_id}/generate")
def generate_bullets_endpoint(
    project_id: int,
    body: GenerateBulletsRequest = Body(default=GenerateBulletsRequest()),
    user_id: int = Depends(require_auth)
):
    """Generate and store resume bullets for a project."""
    return generate_project_bullets(
        project_id=project_id,
        user_id=user_id,
        num_bullets=body.num_bullets
    )


@router.get("/projects/{project_id}")
def get_bullets_endpoint(
    project_id: int,
    user_id: int = Depends(require_auth)
):
    """Get stored resume bullets for a project."""
    return get_project_bullets(project_id=project_id, user_id=user_id)


@router.post("/projects/{project_id}/edit")
def edit_bullets_endpoint(
    project_id: int,
    body: EditBulletsRequest,
    user_id: int = Depends(require_auth)
):
    """Edit stored resume bullets and/or header for a project."""
    return edit_project_bullets(
        project_id=project_id,
        user_id=user_id,
        bullets=body.bullets,
        header=body.header
    )


@router.post("/projects/{project_id}/regenerate")
def regenerate_bullets_endpoint(
    project_id: int,
    body: GenerateBulletsRequest = Body(default=GenerateBulletsRequest()),
    user_id: int = Depends(require_auth)
):
    """Regenerate all bullets for a project, replacing existing ones."""
    return regenerate_project_bullets(
        project_id=project_id,
        user_id=user_id,
        num_bullets=body.num_bullets
    )


@router.get("/projects/{project_id}/ats")
def get_ats_endpoint(
    project_id: int,
    user_id: int = Depends(require_auth)
):
    """Get detailed ATS scores for a project's stored bullets."""
    return get_project_ats(project_id=project_id, user_id=user_id)


@router.delete("/projects/{project_id}")
def delete_bullets_endpoint(
    project_id: int,
    user_id: int = Depends(require_auth)
):
    """Delete stored resume bullets for a project."""
    return delete_project_bullets(project_id=project_id, user_id=user_id)


# ── full resume endpoints ─────────────────────────────────────────────────────

@router.post("/generate")
def generate_resume_endpoint(
    body: GenerateBulletsRequest = Body(default=GenerateBulletsRequest()),
    user_id: int = Depends(require_auth)
):
    """
    Smart full-resume generate. Checks all user projects for stored bullets —
    generates missing ones, then assembles and stores the full resume.
    """
    return generate_full_resume(user_id=user_id, num_bullets=body.num_bullets)


@router.get("")
def get_resume_endpoint(
    user_id: int = Depends(require_auth)
):
    """Return the stored resume JSON."""
    return get_full_resume(user_id=user_id)


@router.post("/save")
def save_resume_endpoint(
    body: dict = Body(...),
    user_id: int = Depends(require_auth)
):
    """
    Save the enriched resume back to the database.
    Called after the frontend adds education, work history, skills, etc.
    """
    return save_full_resume(user_id=user_id, resume_data=body)


@router.post("/page-count")
def page_count_endpoint(
    body: dict = Body(...),
    user_id: int = Depends(require_auth)
):
    """
    Build the resume PDF in memory from the supplied payload and return
    the page count. Nothing is saved to the database.
    """
    try:
        pages = get_resume_page_count(body)
        return {"pages": pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page count failed: {e}")


@router.get("/download/pdf")
def download_pdf_endpoint(
    user_id: int = Depends(require_auth)
):
    """Export the stored resume as a downloadable PDF."""
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


@router.get("/download/docx")
def download_docx_endpoint(
    user_id: int = Depends(require_auth)
):
    """Export the stored resume as a downloadable DOCX."""
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