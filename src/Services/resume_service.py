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

    # Generate missing bullets — skip projects that fail, don't block the whole resume
    generated_count = 0
    for project in all_projects:
        if not db_manager.get_resume_bullets(project.id):
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

    # Assemble in resumeGenerator.py format: name header + projects with bullets
    resume_projects = []
    for project in all_projects:
        bd = db_manager.get_resume_bullets(project.id) or {}
        resume_projects.append({
            "name": project.name,
            "header": bd.get("header") or project.name,
            "bullets": bd.get("bullets") or [],
            "ats_score": bd.get("ats_score"),
        })

    resume_data = {
        "name": f"{user.first_name} {user.last_name}",
        "projects": resume_projects,
        "generated_at": datetime.utcnow().isoformat(),
    }

    db_manager.update_user(user_id, {"resume": resume_data})

    return {
        "message": "Resume generated",
        "bullets_generated_for": generated_count,
        "resume": resume_data,
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

    return {"resume": user.resume}


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