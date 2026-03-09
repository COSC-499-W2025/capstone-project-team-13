from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
from typing import Optional
from src.Services.auth_service import require_auth
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