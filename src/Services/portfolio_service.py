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

def get_portfolio(include_hidden: bool = False) -> dict:
    """Return the full portfolio with all projects, stats, and summary."""
    return _portfolio_service.get_portfolio_data(include_hidden=include_hidden)


def get_portfolio_project(project_id: int) -> Optional[dict]:
    """Return a single formatted project card by ID. Returns None if not found."""
    project = db_manager.get_project(project_id)
    if not project:
        return None
    return _portfolio_service._format_project_card(project)




def get_portfolio_stats(include_hidden: bool = False) -> dict:
    """Return only the stats portion of the portfolio."""
    projects = db_manager.get_all_projects(include_hidden=include_hidden)
    return _portfolio_service._calculate_portfolio_stats(projects)


def get_portfolio_summary(include_hidden: bool = False) -> dict:
    """Return only the summary portion of the portfolio."""
    projects = db_manager.get_all_projects(include_hidden=include_hidden)
    return _portfolio_service._generate_portfolio_summary(projects)


def generate_portfolio(include_hidden: bool = False) -> dict:
    """
    Generate a portfolio from all projects and return the full data.
    """
    return _portfolio_service.get_portfolio_data(include_hidden=include_hidden)



def edit_portfolio_project(project_id: int, updates: Dict[str, Any]) -> Optional[dict]:
    """
    Edit a project's fields and return the updated formatted project card.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None

    db_manager.update_project(project_id, updates)

    updated = db_manager.get_project(project_id)
    if not updated:
        return None

    return _portfolio_service._format_project_card(updated)