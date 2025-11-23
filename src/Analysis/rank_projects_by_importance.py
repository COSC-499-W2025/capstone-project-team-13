# src/Databases/project_extract.py

from typing import Dict, Any, List
from datetime import datetime
from src.Databases.database import db_manager, Project   # adjust import if needed


# ---------------------------------------------
# Helper: Safely serialize datetime to ISO
# ---------------------------------------------
def _safe_date(dt: datetime):
    return dt.isoformat() if isinstance(dt, datetime) else None


# ---------------------------------------------
# Extract the fields relevant to ranking/scoring
# ---------------------------------------------
def extract_project_fields(project: Project) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy Project into a lightweight dictionary containing
    the fields needed for ranking, scoring, and analytics.
    """
    
    return {
        "id": project.id,
        "name": project.name,

        # --- Dates ---
        "date_created": _safe_date(project.date_created),
        "date_modified": _safe_date(project.date_modified),
        "date_scanned": _safe_date(project.date_scanned),

        # --- Metrics ---
        "lines_of_code": project.lines_of_code,
        "word_count": project.word_count,
        "file_count": project.file_count,
        "total_size_bytes": project.total_size_bytes,

        # --- Classification ---
        "project_type": project.project_type,
        "collaboration_type": project.collaboration_type,

        # --- Ranking ---
        "importance_score": project.importance_score,
        "user_rank": project.user_rank,
        "is_featured": project.is_featured,
        "is_hidden": project.is_hidden,

        # --- Success Evidence ---
        "success_evidence": project.success_metrics,  # already parsed JSON

        # --- Languages / Frameworks / Tags ---
        "languages": project.languages,
        "frameworks": project.frameworks,
        "skills": project.skills,
        "tags": project.tags,

        # --- User Customizations ---
        "user_role": project.user_role,
        "custom_description": project.custom_description,
    }


# ---------------------------------------------
# Extract all projects into structured dictionaries
# ---------------------------------------------
def extract_all_projects() -> List[Dict[str, Any]]:
    """
    Read all projects from the database and return a list of dictionaries
    containing only the fields used for importance/productivity scoring.
    """
    projects = db_manager.get_all_projects(include_hidden=True)
    return [extract_project_fields(p) for p in projects]


# ---------------------------------------------
# Placeholder for your scoring function
# ---------------------------------------------
def calculate_importance_score(project_data: Dict[str, Any]) -> float:
    """
    Example placeholder scoring function.
    Fill this in with your real algorithm later.
    """

    # Example scoring logic — customize later
    score = 0.0

    # Recency
    if project_data["date_modified"]:
        # More recent = higher score
        age_days = (datetime.now() - datetime.fromisoformat(project_data["date_modified"])).days
        score += max(0, 50 - age_days * 0.5)

    # Size
    score += min(project_data.get("lines_of_code", 0) / 1000, 20)

    # Success evidence weighting
    if project_data["success_evidence"]:
        score += 10

    # User rank weighting
    if project_data["user_rank"]:
        score += max(0, 20 - project_data["user_rank"] * 2)

    return round(score, 2)


# ---------------------------------------------
# Extract all projects *with* calculated scores
# ---------------------------------------------
def extract_projects_with_scores() -> List[Dict[str, Any]]:
    all_projects = extract_all_projects()

    for p in all_projects:
        p["calculated_importance_score"] = calculate_importance_score(p)

    return all_projects
