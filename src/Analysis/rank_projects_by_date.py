# src/Analysis/rank_projects_by_date.py
from datetime import datetime
from src.Databases.database import db_manager  

def load_project_metadata_from_db():
    """
    Fetch real project metadata from the database.
    Returns a list of dictionaries with name, created_at, and updated_at.
    """
    projects = db_manager.get_all_projects()
    project_dicts = []

    for p in projects:
        pd = p.to_dict()
        project_dicts.append({
            "name": pd.get("name"),
            # These fields may be stored as datetime or string — handle both
            "created_at": pd.get("created_at") or pd.get("date_created"),
            "updated_at": pd.get("updated_at") or pd.get("date_modified"),
        })
    return project_dicts


def parse_date(date_value):
    """Safely parse a date (supports both datetime objects and ISO strings)."""
    if isinstance(date_value, datetime):
        return date_value
    try:
        return datetime.fromisoformat(date_value)
    except Exception:
        return datetime.min


def rank_projects_chronologically(projects):
    """Sort projects by creation date (oldest → newest)."""
    return sorted(projects, key=lambda x: parse_date(x.get("created_at", "")))


def format_project_timeline(projects):
    """Format project info for display."""
    from datetime import datetime
    
    lines = []
    for idx, p in enumerate(projects, start=1):
        name = p.get("name", "Unnamed Project")
        created = p.get("created_at", "Unknown")
        updated = p.get("updated_at", "Unknown")
        
        # Format dates nicely
        if created != "Unknown":
            try:
                created_dt = datetime.fromisoformat(created)
                created = created_dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
        if updated != "Unknown":
            try:
                updated_dt = datetime.fromisoformat(updated)
                updated = updated_dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
        lines.append(
            f"{idx}. {name}\n"
            f"    Created: {created}\n"
            f"    Last Updated: {updated}\n"
        )
    return "\n".join(lines)


def get_ranked_timeline_from_db():
    """
    High-level function:
    Loads real metadata from the database,
    sorts projects chronologically,
    and returns a formatted timeline string.
    """
    projects = load_project_metadata_from_db()
    sorted_projects = rank_projects_chronologically(projects)
    return format_project_timeline(sorted_projects)


# Optional: quick standalone test
if __name__ == "__main__":
    print("=== Project Timeline (Real Metadata) ===\n")
    print(get_ranked_timeline_from_db())
