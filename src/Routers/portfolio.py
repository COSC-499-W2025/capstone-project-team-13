from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from src.Services.portfolio_service import (
    get_portfolio,
    get_portfolio_project,
    update_portfolio_project,
    get_portfolio_stats,
    get_portfolio_summary,
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


class UpdateProjectRequest(BaseModel):
    is_featured: Optional[bool] = None
    is_hidden: Optional[bool] = None
    user_rank: Optional[int] = None
    user_role: Optional[str] = None
    user_contribution_percent: Optional[float] = None
    custom_description: Optional[str] = None


@router.get("")
def get_portfolio_endpoint(include_hidden: bool = Query(default=False)):
    """Return full portfolio: all projects, stats, and summary."""
    return get_portfolio(include_hidden=include_hidden)


@router.get("/stats")
def get_portfolio_stats_endpoint(include_hidden: bool = Query(default=False)):
    """Return only portfolio-level statistics."""
    return get_portfolio_stats(include_hidden=include_hidden)


@router.get("/summary")
def get_portfolio_summary_endpoint(include_hidden: bool = Query(default=False)):
    """Return only the portfolio summary text and highlights."""
    return get_portfolio_summary(include_hidden=include_hidden)


@router.get("/{project_id}")
def get_portfolio_project_endpoint(project_id: int):
    """Return a single project card by ID."""
    result = get_portfolio_project(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return result


@router.patch("/{project_id}")
def update_portfolio_project_endpoint(project_id: int, body: UpdateProjectRequest):
    """Update portfolio display settings for a project."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    result = update_portfolio_project(project_id, updates)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result