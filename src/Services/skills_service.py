from collections import defaultdict
from typing import Optional
from src.Databases.database import db_manager

def get_skills(user_id: Optional[int] = None):
    """Get skills aggregated from user's projects (or guest projects if not logged in)"""
    # Filter projects by user
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()

    skill_map = defaultdict(lambda: {
        "count": 0,
        "projects": []
    })

    for project in projects:
        # project.skills is list
        if not project.skills:
            continue

        for skill in project.skills:
            skill_map[skill]["count"] += 1
            skill_map[skill]["projects"].append({
                "project_id": project.id,
                "project_name": project.name,
                "project_type": project.project_type
            })

    return {
        "skills": [
            {
                "name": skill,
                "count": data["count"],
                "projects": data["projects"]
            }
            for skill, data in sorted(
                skill_map.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )
        ]
    }

def get_skill_detail(skill_name: str, user_id: Optional[int] = None):
    """Get projects containing a specific skill, filtered by user"""
    # Filter projects by user
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()

    matching_projects = []

    for project in projects:
        if not project.skills:
            continue

        if skill_name in project.skills:
            matching_projects.append({
                "project_id": project.id,
                "project_name": project.name,
                "project_type": project.project_type,
                "file_count": project.file_count
            })

    if not matching_projects:
        return {
            "skill": skill_name,
            "project_count": 0,
            "projects": []
        }

    return {
        "skill": skill_name,
        "project_count": len(matching_projects),
        "projects": matching_projects
    }
