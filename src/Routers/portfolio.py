from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
from typing import Optional
from src.Services.auth_service import require_auth
from src.Databases.database import db_manager
from src.Services.portfolio_service import (
    get_portfolio,
    get_portfolio_project,
    get_portfolio_stats,
    get_portfolio_summary,
    generate_portfolio,
    edit_portfolio_project
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("")
def get_portfolio_endpoint(
    include_hidden: bool = Query(default=False),
    user_id: int = Depends(require_auth)
):
    """Return the stored portfolio for the authenticated user."""
    return get_portfolio(user_id=user_id, include_hidden=include_hidden)


@router.get("/stats")
def get_portfolio_stats_endpoint(
    include_hidden: bool = Query(default=False),
    user_id: int = Depends(require_auth)
):
    """Return only portfolio-level statistics for the authenticated user."""
    return get_portfolio_stats(user_id=user_id, include_hidden=include_hidden)


@router.get("/summary")
def get_portfolio_summary_endpoint(
    include_hidden: bool = Query(default=False),
    user_id: int = Depends(require_auth)
):
    """Return only the portfolio summary text and highlights for the authenticated user."""
    return get_portfolio_summary(user_id=user_id, include_hidden=include_hidden)


@router.post("/generate")
def generate_portfolio_endpoint(
    include_hidden: bool = Query(default=False),
    user_id: int = Depends(require_auth)
):
    """
    Regenerate the portfolio from current DB state, save it to the user record,
    and return the fresh data.
    """
    return generate_portfolio(user_id=user_id, include_hidden=include_hidden)


@router.get("/showcase")
def get_portfolio_showcase(user_id: int = Depends(require_auth)):
    """
    Return the top 3 projects by importance score with evolution data.
    Must appear before /{project_id} so 'showcase' is not parsed as an int.
    """
    projects = db_manager.get_all_projects(include_hidden=False, user_id=user_id)
    top3 = sorted(projects, key=lambda p: p.importance_score or 0, reverse=True)[:3]

    def evolution(p):
        start = p.date_created or p.created_at
        end = p.date_modified or p.updated_at
        milestones = []
        if start:
            milestones.append({"label": "Project started", "date": start.strftime("%b %Y") if hasattr(start, "strftime") else str(start)})
        if p.file_count and p.file_count > 0:
            milestones.append({"label": f"{p.file_count} files analysed", "date": None})
        if p.lines_of_code and p.lines_of_code > 0:
            milestones.append({"label": f"{p.lines_of_code:,} lines of code", "date": None})
        langs = p.languages if isinstance(p.languages, list) else []
        if langs:
            milestones.append({"label": f"Languages: {', '.join(langs[:3])}", "date": None})
        if end and start and end != start:
            milestones.append({"label": "Latest version", "date": end.strftime("%b %Y") if hasattr(end, "strftime") else str(end)})
        return milestones

    result = []
    for p in top3:
        result.append({
            "id": p.id,
            "name": p.custom_description or p.name,
            "description": p.description or p.ai_description or "",
            "project_type": p.project_type,
            "importance_score": round(p.importance_score or 0, 2),
            "is_featured": p.is_featured,
            "languages": p.languages or [],
            "frameworks": p.frameworks or [],
            "skills": p.skills or [],
            "file_count": p.file_count or 0,
            "lines_of_code": p.lines_of_code or 0,
            "user_role": p.user_role or "",
            "success_evidence": p.success_evidence or "",
            "date_start": p.date_created.strftime("%b %Y") if p.date_created and hasattr(p.date_created, "strftime") else None,
            "date_end": p.date_modified.strftime("%b %Y") if p.date_modified and hasattr(p.date_modified, "strftime") else None,
            "evolution": evolution(p),
        })
    return {"projects": result, "total": len(projects)}


@router.get("/about")
def get_about(user_id: int = Depends(require_auth)):
    """Return the user's About Me fields."""
    user = db_manager.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "about_name":     getattr(user, "about_name", None) or "",
        "about_subtitle": getattr(user, "about_subtitle", None) or "",
        "about_bio":      getattr(user, "about_bio", None) or "",
    }


@router.post("/about")
def save_about(body: dict = Body(...), user_id: int = Depends(require_auth)):
    """Save the user's About Me fields."""
    allowed = {"about_name", "about_subtitle", "about_bio"}
    updates = {k: v for k, v in body.items() if k in allowed}
    user = db_manager.update_user(user_id, updates)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "about_name":     getattr(user, "about_name", None) or "",
        "about_subtitle": getattr(user, "about_subtitle", None) or "",
        "about_bio":      getattr(user, "about_bio", None) or "",
    }


@router.get("/visibility")
def get_portfolio_visibility(user_id: int = Depends(require_auth)):
    """Return whether the authenticated user's portfolio is public."""
    user = db_manager.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"portfolio_public": bool(getattr(user, "portfolio_public", False))}


@router.post("/visibility")
def set_portfolio_visibility(
    body: dict = Body(...),
    user_id: int = Depends(require_auth)
):
    """Set whether the authenticated user's portfolio is public."""
    is_public = bool(body.get("portfolio_public", False))
    user = db_manager.update_user(user_id, {"portfolio_public": is_public})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"portfolio_public": bool(getattr(user, "portfolio_public", False))}


@router.get("/{project_id}")
def get_portfolio_project_endpoint(
    project_id: int,
    user_id: int = Depends(require_auth)
):
    """Return a single project card by ID. Only accessible by the project owner."""
    result = get_portfolio_project(user_id=user_id, project_id=project_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return result


@router.post("/{project_id}/edit")
def edit_portfolio_project_endpoint(
    project_id: int,
    updates: dict = Body(...),
    user_id: int = Depends(require_auth)
):
    """
    Edit a project's fields. Only the project owner can edit.
    Saves the updated portfolio to the user record after editing.
    """
    result = edit_portfolio_project(user_id=user_id, project_id=project_id, updates=updates)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return result