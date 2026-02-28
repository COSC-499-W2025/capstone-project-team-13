"""
Portfolio Service
================
Business logic for portfolio API endpoints.
Wraps the existing PortfolioService class and database operations.
"""

from typing import Optional, Dict, Any
from src.Databases.database import db_manager
from src.Portfolio.portfolioFormatter import PortfolioFormatter

_portfolio_service = PortfolioFormatter()

def get_portfolio(include_hidden: bool = False, user_id: Optional[int] = None) -> dict:
    """Return the full portfolio with all projects, stats, and summary filtered by user."""
    # Get user-specific projects
    if user_id:
        projects = db_manager.get_projects_for_user(user_id, include_hidden=include_hidden)
    else:
        projects = db_manager.get_guest_projects(include_hidden=include_hidden)
    
    # Generate portfolio from filtered projects
    return {
        "projects": [_portfolio_service._format_project_card(p) for p in projects],
        "stats": _portfolio_service._calculate_portfolio_stats(projects),
        "summary": _portfolio_service._generate_portfolio_summary(projects)
    }


def get_portfolio_project(project_id: int, user_id: Optional[int] = None) -> Optional[dict]:
    """Return a single formatted project card by ID. Returns None if not found or unauthorized."""
    project = db_manager.get_project(project_id)
    if not project:
        return None
    
    # Verify ownership
    if project.user_id != user_id:
        return None  # User doesn't own this project
    
    return _portfolio_service._format_project_card(project)


def get_portfolio_stats(include_hidden: bool = False, user_id: Optional[int] = None) -> dict:
    """Return only the stats portion of the portfolio filtered by user."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id, include_hidden=include_hidden)
    else:
        projects = db_manager.get_guest_projects(include_hidden=include_hidden)
    
    return _portfolio_service._calculate_portfolio_stats(projects)


def get_portfolio_summary(include_hidden: bool = False, user_id: Optional[int] = None) -> dict:
    """Return only the summary portion of the portfolio filtered by user."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id, include_hidden=include_hidden)
    else:
        projects = db_manager.get_guest_projects(include_hidden=include_hidden)
    
    return _portfolio_service._generate_portfolio_summary(projects)


def generate_portfolio(include_hidden: bool = False, user_id: Optional[int] = None) -> dict:
    """
    Generate a portfolio from all user's projects and return the full data.
    """
    return get_portfolio(include_hidden=include_hidden, user_id=user_id)


def edit_portfolio_project(project_id: int, updates: Dict[str, Any], user_id: Optional[int] = None) -> Optional[dict]:
    """
    Edit a project's fields and return the updated formatted project card.
    Only allows editing if user owns the project.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None
    
    # Verify ownership
    if project.user_id != user_id:
        return None  # User doesn't own this project

    db_manager.update_project(project_id, updates)

    updated = db_manager.get_project(project_id)
    if not updated:
        return None

    return _portfolio_service._format_project_card(updated)

