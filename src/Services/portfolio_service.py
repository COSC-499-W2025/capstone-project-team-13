"""
Portfolio Service
================
Business logic for portfolio API endpoints.
Wraps the existing PortfolioFormatter class and database operations.

All functions require a user_id from the authenticated JWT token.
Portfolio data is persisted to the user.portfolio column after
generate and edit operations so GET /portfolio can return the
stored version without recomputing every time.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from src.Databases.database import db_manager
from src.Portfolio.portfolioFormatter import PortfolioFormatter

_portfolio_service = PortfolioFormatter()


def _save_portfolio_to_user(user_id: int, portfolio_data: dict) -> None:
    """Persist the full portfolio JSON to the user's record in the users table."""
    db_manager.update_user(user_id, {'portfolio': portfolio_data})


def get_portfolio(user_id: int, include_hidden: bool = False) -> dict:
    """
    Return the stored portfolio for the authenticated user.
    If no portfolio has been generated yet, generate and store it first.
    """
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return stored portfolio only for the default (non-hidden) view.
    # If include_hidden=True, always regenerate fresh so hidden projects
    # are not filtered out by a previously cached version.
    if user.portfolio and not include_hidden:
        return user.portfolio

    # Otherwise generate fresh, save it, and return it
    portfolio_data = _portfolio_service.get_portfolio_data(
        user_id=user_id,
        include_hidden=include_hidden
    )
    _save_portfolio_to_user(user_id, portfolio_data)
    return portfolio_data


def get_portfolio_project(user_id: int, project_id: int) -> Optional[dict]:
    """
    Return a single formatted project card by ID.
    Raises 403 if the project does not belong to the authenticated user.
    Returns None if not found.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None

    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this project"
        )

    return _portfolio_service._format_project_card(project)


def get_portfolio_stats(user_id: int, include_hidden: bool = False) -> dict:
    """Return only the stats portion of the portfolio for the authenticated user."""
    projects = db_manager.get_all_projects(include_hidden=include_hidden, user_id=user_id)
    return _portfolio_service._calculate_portfolio_stats(projects)


def get_portfolio_summary(user_id: int, include_hidden: bool = False) -> dict:
    """Return only the summary portion of the portfolio for the authenticated user."""
    projects = db_manager.get_all_projects(include_hidden=include_hidden, user_id=user_id)
    return _portfolio_service._generate_portfolio_summary(projects)


def generate_portfolio(user_id: int, include_hidden: bool = False) -> dict:
    """
    Regenerate the portfolio from current DB state for the authenticated user,
    save it to user.portfolio, and return the fresh data.
    """
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    portfolio_data = _portfolio_service.get_portfolio_data(
        user_id=user_id,
        include_hidden=include_hidden
    )
    _save_portfolio_to_user(user_id, portfolio_data)
    return portfolio_data


def edit_portfolio_project(user_id: int, project_id: int, updates: Dict[str, Any]) -> Optional[dict]:
    """
    Edit a project's fields, regenerate and save the full portfolio,
    and return the updated formatted project card.
    Raises 403 if the project does not belong to the authenticated user.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None

    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this project"
        )

    db_manager.update_project(project_id, updates)

    updated = db_manager.get_project(project_id)
    if not updated:
        return None

    # Regenerate and persist the full portfolio to keep it in sync
    portfolio_data = _portfolio_service.get_portfolio_data(user_id=user_id)
    _save_portfolio_to_user(user_id, portfolio_data)

    return _portfolio_service._format_project_card(updated)