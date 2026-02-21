"""
Portfolio Service
================
Business logic for portfolio API endpoints.
Wraps the existing PortfolioService class and database operations.
"""

from typing import Optional
from src.Databases.database import db_manager
from src.Portfolio.portfolioFormatter import PortfolioFormatter

_portfolio_service = PortfolioFormatter()

def get_portfolio(include_hidden: bool = False) -> dict:
    """Return the full portfolio with all projects, stats, and summary."""
    return _portfolio_service.get_portfolio_data(include_hidden=include_hidden)


def get_portfolio_project(project_id: int) -> Optional[dict]:
    """Return a single formatted project card by ID. Returns None if not found."""
    project = db_manager.get_project(project_id)
    if not project:
        return None
    return _portfolio_service._format_project_card(project)


def update_portfolio_project(project_id: int, updates: dict) -> dict:
    """Update portfolio-specific fields for a project."""
    project = db_manager.get_project(project_id)
    if not project:
        return {"success": False, "error": f"Project {project_id} not found"}

    try:
        db_manager.update_project(project_id, updates)
        updated_project = db_manager.get_project(project_id)
        return {
            "success": True,
            "project_id": project_id,
            "project_name": updated_project.name,
            "is_featured": updated_project.is_featured,
            "is_hidden": updated_project.is_hidden,
            "user_rank": updated_project.user_rank,
            "user_role": updated_project.user_role,
            "user_contribution_percent": updated_project.user_contribution_percent,
            "custom_description": updated_project.custom_description,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_portfolio_stats(include_hidden: bool = False) -> dict:
    """Return only the stats portion of the portfolio."""
    projects = db_manager.get_all_projects(include_hidden=include_hidden)
    return _portfolio_service._calculate_portfolio_stats(projects)


def get_portfolio_summary(include_hidden: bool = False) -> dict:
    """Return only the summary portion of the portfolio."""
    projects = db_manager.get_all_projects(include_hidden=include_hidden)
    return _portfolio_service._generate_portfolio_summary(projects)