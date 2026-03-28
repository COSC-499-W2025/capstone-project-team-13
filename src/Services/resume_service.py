"""
Resume Service
==============
Business logic for resume API endpoints.
Wraps existing bullet generators and database operations.

All functions require a user_id from the authenticated JWT token.
Users can only access and modify bullets for their own projects.
"""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from src.Databases.database import db_manager
from src.Resume.codeBulletGenerator import CodeBulletGenerator
from src.Resume.textBulletGenerator import TextBulletGenerator
from src.Resume.mediaBulletGenerator import MediaBulletGenerator
from src.Resume.resumeAnalytics import score_all_bullets, calculate_ats_score


def _get_generator(project):
    """Return the correct bullet generator for a project's type."""
    if project.project_type == "code":
        return CodeBulletGenerator()
    if project.project_type == "text":
        return TextBulletGenerator()
    return MediaBulletGenerator()


def _display_name(project) -> str:
    """Return the best human-readable name for a project (mirrors projects router logic)."""
    import re
    cd = (project.custom_description or "").strip()
    if cd:
        return cd
    name = (project.name or "").strip()
    if re.match(r'^[0-9a-f-]{30,}', name, re.IGNORECASE):
        return project.description or project.ai_description or f"{project.project_type or 'Project'} {project.id}"
    return name


def _check_project_ownership(project_id: int, user_id: int):
    """
    Fetch project and verify it belongs to the authenticated user.
    Raises 404 if not found, 403 if owned by someone else.
    Returns the project on success.
    """
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project"
        )
    return project


# ── per-project bullet operations ─────────────────────────────────────────────

def get_project_bullets(project_id: int, user_id: int) -> dict:
    """
    Return stored resume bullets for a project.
    Raises 404/403 if project not found or not owned by user.
    """
    project = _check_project_ownership(project_id, user_id)

    bullets_data = db_manager.get_resume_bullets(project_id)
    if not bullets_data:
        return {
            "project_id": project_id,
            "project_name": project.name,
            "bullets": None,
            "message": "No resume bullets generated yet"
        }

    return {
        "project_id": project_id,
        "project_name": project.name,
        "header": bullets_data.get("header"),
        "bullets": bullets_data.get("bullets"),
        "ats_score": bullets_data.get("ats_score"),
        "generated_at": bullets_data.get("generated_at"),
        "num_bullets": bullets_data.get("num_bullets"),
    }


def generate_project_bullets(project_id: int, user_id: int, num_bullets: int = 3) -> dict:
    """
    Generate and store resume bullets for a single project.
    Raises 404/403 if project not found or not owned by user.
    """
    project = _check_project_ownership(project_id, user_id)

    try:
        generator = _get_generator(project)
        bullets = generator.generate_resume_bullets(project, num_bullets)
        header = generator.generate_project_header(project)
        scoring = score_all_bullets(bullets, project.project_type)

        db_manager.save_resume_bullets(
            project_id=project_id,
            bullets=bullets,
            header=header,
            ats_score=scoring["overall_score"]
        )

        return {
            "success": True,
            "project_id": project_id,
            "project_name": project.name,
            "header": header,
            "bullets": bullets,
            "ats_score": scoring["overall_score"],
            "num_bullets": len(bullets),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bullets: {str(e)}"
        )


def regenerate_project_bullets(project_id: int, user_id: int, num_bullets: int = 3) -> dict:
    """
    Regenerate all bullets for a project, replacing existing ones.
    Preserves the existing bullet count if num_bullets not specified.
    Raises 404/403 if project not found or not owned by user.
    """
    project = _check_project_ownership(project_id, user_id)

    existing = db_manager.get_resume_bullets(project_id)
    if existing and existing.get("num_bullets"):
        num_bullets = existing["num_bullets"]

    try:
        generator = _get_generator(project)
        bullets = generator.generate_resume_bullets(project, num_bullets)
        header = generator.generate_project_header(project)
        scoring = score_all_bullets(bullets, project.project_type)

        db_manager.save_resume_bullets(
            project_id=project_id,
            bullets=bullets,
            header=header,
            ats_score=scoring["overall_score"]
        )

        return {
            "success": True,
            "project_id": project_id,
            "project_name": project.name,
            "header": header,
            "bullets": bullets,
            "ats_score": scoring["overall_score"],
            "num_bullets": len(bullets),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate bullets: {str(e)}"
        )


def ai_enhance_project_bullets(
    project_id: int, user_id: int, num_bullets: int = 3, current_bullets: list = None
) -> dict:
    """
    Enhance existing resume bullets for a project using AI.
    Uses current_bullets from the request if provided, otherwise reads from DB.
    Falls back to AI generation from scratch if no bullets exist anywhere.
    """
    project = _check_project_ownership(project_id, user_id)

    try:
        from src.AI.ai_enhanced_summarizer import enhance_resume_bullets, generate_resume_bullets

        existing = db_manager.get_resume_bullets(project_id)
        # Prefer bullets passed from the frontend (reflects unsaved edits)
        existing_bullets = current_bullets or (existing.get("bullets") if existing else None)
        header = existing.get("header", project.name) if existing else project.name

        skills = [s.strip() for s in (project.skills or "").split(",") if s.strip()] \
                 if isinstance(project.skills, str) else (project.skills or [])

        if existing_bullets:
            bullets = enhance_resume_bullets(existing_bullets, project.name, skills)
        else:
            # No bullets yet — generate from scratch
            project_dict = {
                "project_name": project.name,
                "skills": skills,
                "file_count": project.file_count,
                "lines_of_code": project.lines_of_code,
                "success_score": getattr(project, "importance_score", 0) or 0,
                "contribution_score": getattr(project, "contribution_score", 0) or 0,
            }
            bullets = generate_resume_bullets(project_dict, num_bullets=num_bullets)

        if not bullets:
            raise ValueError("AI returned no bullets")

        scoring = score_all_bullets(bullets, project.project_type)
        db_manager.save_resume_bullets(
            project_id=project_id,
            bullets=bullets,
            header=header,
            ats_score=scoring["overall_score"],
        )

        return {
            "success": True,
            "project_id": project_id,
            "project_name": project.name,
            "header": header,
            "bullets": bullets,
            "ats_score": scoring["overall_score"],
            "num_bullets": len(bullets),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI bullet enhancement failed: {str(e)}"
        )


def ai_generate_project_bullets(project_id: int, user_id: int, num_bullets: int = 3) -> dict:
    """
    Generate resume bullets for a project using Gemini AI.
    Replaces any existing bullets. Raises 404/403 if project not found or not owned.
    """
    project = _check_project_ownership(project_id, user_id)

    try:
        from src.AI.ai_enhanced_summarizer import generate_resume_bullets

        project_dict = {
            "project_name": project.name,
            "skills": [s.strip() for s in (project.skills or "").split(",") if s.strip()]
                      if isinstance(project.skills, str)
                      else (project.skills or []),
            "file_count": project.file_count,
            "lines_of_code": project.lines_of_code,
            "success_score": getattr(project, "importance_score", 0) or 0,
            "contribution_score": getattr(project, "contribution_score", 0) or 0,
        }

        bullets = generate_resume_bullets(project_dict, num_bullets=num_bullets)
        if not bullets:
            raise ValueError("AI returned no bullets")

        existing = db_manager.get_resume_bullets(project_id)
        header = existing.get("header", project.name) if existing else project.name
        scoring = score_all_bullets(bullets, project.project_type)

        db_manager.save_resume_bullets(
            project_id=project_id,
            bullets=bullets,
            header=header,
            ats_score=scoring["overall_score"],
        )

        return {
            "success": True,
            "project_id": project_id,
            "project_name": project.name,
            "header": header,
            "bullets": bullets,
            "ats_score": scoring["overall_score"],
            "num_bullets": len(bullets),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI bullet generation failed: {str(e)}"
        )


def edit_project_bullets(
    project_id: int,
    user_id: int,
    bullets: list,
    header: Optional[str] = None
) -> dict:
    """
    Update stored resume bullets for a project.
    Recalculates ATS score after edit.
    Raises 404/403 if project not found or not owned by user.
    """
    project = _check_project_ownership(project_id, user_id)

    if header is None:
        existing = db_manager.get_resume_bullets(project_id)
        header = existing.get("header", project.name) if existing else project.name

    scoring = score_all_bullets(bullets, project.project_type)

    success = db_manager.save_resume_bullets(
        project_id=project_id,
        bullets=bullets,
        header=header,
        ats_score=scoring["overall_score"]
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save updated bullets"
        )

    return {
        "success": True,
        "project_id": project_id,
        "header": header,
        "bullets": bullets,
        "ats_score": scoring["overall_score"],
        "num_bullets": len(bullets),
    }


def get_project_ats(project_id: int, user_id: int) -> dict:
    """
    Return detailed ATS scores for a project's stored bullets.
    Raises 404/403 if project not found or not owned by user.
    """
    project = _check_project_ownership(project_id, user_id)

    bullets_data = db_manager.get_resume_bullets(project_id)
    if not bullets_data or not bullets_data.get("bullets"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bullets found for this project. Generate bullets first."
        )

    bullets = bullets_data["bullets"]
    individual = [calculate_ats_score(b, project.project_type) for b in bullets]
    aggregate = score_all_bullets(bullets, project.project_type)

    return {
        "project_id": project_id,
        "project_name": project.name,
        "overall_score": aggregate["overall_score"],
        "bullets_with_metrics": aggregate["bullets_with_metrics"],
        "total_keywords": aggregate["total_keywords"],
        "grade_distribution": aggregate["grade_distribution"],
        "individual_scores": [
            {
                "bullet": b,
                "score": s["score"],
                "grade": s["grade"],
                "feedback": s["feedback"],
                "keywords": s["keywords"],
            }
            for b, s in zip(bullets, individual)
        ],
    }


def delete_project_bullets(project_id: int, user_id: int) -> dict:
    """
    Delete stored resume bullets for a project.
    Raises 404/403 if project not found or not owned by user.
    """
    _check_project_ownership(project_id, user_id)

    existing = db_manager.get_resume_bullets(project_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bullets found for this project."
        )

    success = db_manager.delete_resume_bullets(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bullets"
        )

    return {"success": True, "project_id": project_id, "message": "Bullets deleted"}


# ── full resume operations ─────────────────────────────────────────────────────

def generate_full_resume(user_id: int, num_bullets: int = 3) -> dict:
    """
    Smart full-resume generate:
    1. Fetch all projects for the user
    2. For any project missing bullets, generate and store them
    3. Assemble resume in resumeGenerator format: name header + projects section
    4. Persist to user.resume and return

    Returns the resume JSON.
    """
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    all_projects = db_manager.get_all_projects(user_id=user_id)
    if not all_projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No projects found. Upload a project first."
        )

    # Always regenerate bullets for every project with the requested count
    generated_count = 0
    for project in all_projects:
        try:
            generator = _get_generator(project)
            bullets = generator.generate_resume_bullets(project, num_bullets)
            header = generator.generate_project_header(project)
            scoring = score_all_bullets(bullets, project.project_type)
            db_manager.save_resume_bullets(
                project_id=project.id,
                bullets=bullets,
                header=header,
                ats_score=scoring["overall_score"]
            )
            generated_count += 1
        except Exception:
            continue

    # Assemble projects — use display name, store project_id for stats lookup
    resume_projects = []
    for project in all_projects:
        bd = db_manager.get_resume_bullets(project.id) or {}
        display = _display_name(project)
        resume_projects.append({
            "project_id": project.id,
            "name": display,
            "header": bd.get("header") or display,
            "bullets": bd.get("bullets") or [],
            "ats_score": bd.get("ats_score"),
        })

    resume_data = {
        "name": f"{user.first_name} {user.last_name}",
        "projects": resume_projects,
        "generated_at": datetime.utcnow().isoformat(),
    }

    db_manager.update_user(user_id, {"resume": resume_data})

    # Enrich response with project stats (not saved to DB)
    stats_by_id = {p.id: {
        "lines_of_code": p.lines_of_code or 0,
        "file_count": p.file_count or 0,
        "importance_score": round(p.importance_score or 0.0, 1),
    } for p in all_projects}

    response_projects = [
        {**rp, **stats_by_id.get(rp["project_id"], {})}
        for rp in resume_projects
    ]

    return {
        "message": "Resume generated",
        "bullets_generated_for": generated_count,
        "resume": {**resume_data, "projects": response_projects},
    }


def get_full_resume(user_id: int) -> dict:
    """
    Return the stored resume JSON from user.resume.
    Raises 404 if no resume has been generated yet.
    """
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Call POST /resume/generate first."
        )

    # Enrich projects with live stats (not stored in user.resume)
    stored = user.resume
    all_projects = db_manager.get_all_projects(user_id=user_id)
    stats_by_id = {p.id: {
        "lines_of_code": p.lines_of_code or 0,
        "file_count": p.file_count or 0,
        "importance_score": round(p.importance_score or 0.0, 1),
    } for p in all_projects}

    enriched_projects = [
        {**rp, **stats_by_id.get(rp.get("project_id"), {})}
        for rp in stored.get("projects", [])
    ]

    return {"resume": {**stored, "projects": enriched_projects}}


def save_full_resume(user_id: int, resume_data: dict) -> dict:
    """
    Save the enriched resume (with frontend-added education, work history,
    skills, etc.) back to user.resume in the database.
    """
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_manager.update_user(user_id, {"resume": resume_data})
    return {"success": True, "message": "Resume saved"}