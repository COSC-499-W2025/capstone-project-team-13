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

