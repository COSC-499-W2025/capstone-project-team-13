"""
Resume Service
==============
Business logic for resume API endpoints.
Wraps existing bullet generators and database operations.
"""

from typing import Optional
from src.Databases.database import db_manager
from src.Resume.codeBulletGenerator import CodeBulletGenerator
from src.Resume.textBulletGenerator import TextBulletGenerator
from src.Resume.mediaBulletGenerator import MediaBulletGenerator
from src.Resume.resumeAnalytics import score_all_bullets


def _get_generator(project):
    """Return the correct bullet generator for a project's type."""
    if project.project_type == "code":
        return CodeBulletGenerator()
    if project.project_type == "text":
        return TextBulletGenerator()
    return MediaBulletGenerator()


def get_resume(project_id: int, user_id: Optional[int] = None) -> Optional[dict]:
    """
    Return stored resume bullets for a project.
    Returns None if project not found or user doesn't own it.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None
    
    # Verify ownership
    if project.user_id != user_id:
        return None  # User doesn't own this project

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


def generate_resume(project_id: int, num_bullets: int = 3, user_id: Optional[int] = None) -> dict:
    """
    Generate and store resume bullets for a project.
    Returns the generated bullets data or an error dict.
    Only allows generation if user owns the project.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return {"success": False, "error": f"Project {project_id} not found"}
    
    # Verify ownership
    if project.user_id != user_id:
        return {"success": False, "error": "You don't have permission to access this project"}

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
        return {"success": False, "error": str(e)}


def edit_resume(project_id: int, bullets: list, header: Optional[str] = None, user_id: Optional[int] = None) -> dict:
    """
    Update stored resume bullets for a project.
    Recalculates ATS score after edit.
    Only allows editing if user owns the project.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return {"success": False, "error": f"Project {project_id} not found"}
    
    # Verify ownership
    if project.user_id != user_id:
        return {"success": False, "error": "You don't have permission to access this project"}

    # Keep existing header if none provided
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
        return {"success": False, "error": "Failed to save updated bullets"}

    return {
        "success": True,
        "project_id": project_id,
        "header": header,
        "bullets": bullets,
        "ats_score": scoring["overall_score"],
        "num_bullets": len(bullets),
    }



