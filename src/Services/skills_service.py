from collections import defaultdict
from typing import Optional
from src.Databases.database import db_manager


def _display_name(project) -> str:
    return project.custom_description or project.name or f"Project {project.id}"


def get_skills(user_id: Optional[int] = None):
    projects = db_manager.get_all_projects(user_id=user_id)

    skill_map = defaultdict(lambda: {"count": 0, "projects": []})

    for project in projects:
        if not project.skills:
            continue
        for skill in project.skills:
            skill_map[skill]["count"] += 1
            skill_map[skill]["projects"].append({
                "project_id": project.id,
                "project_name": _display_name(project),
                "project_type": project.project_type,
            })

    return {
        "skills": [
            {"name": skill, "count": data["count"], "projects": data["projects"]}
            for skill, data in sorted(
                skill_map.items(), key=lambda x: x[1]["count"], reverse=True
            )
        ]
    }


def get_skill_detail(skill_name: str, user_id: Optional[int] = None):
    projects = db_manager.get_all_projects(user_id=user_id)

    matching_projects = []
    for project in projects:
        if not project.skills:
            continue
        if skill_name in project.skills:
            matching_projects.append({
                "project_id": project.id,
                "project_name": _display_name(project),
                "project_type": project.project_type,
                "file_count": project.file_count,
            })

    return {
        "skill": skill_name,
        "project_count": len(matching_projects),
        "projects": matching_projects,
    }


def get_skills_timeline(user_id: Optional[int] = None):
    """
    Returns skills with date ranges derived from project activity,
    showing when each skill was first and last used across all projects.
    """
    projects = db_manager.get_all_projects(user_id=user_id)

    skill_map = defaultdict(lambda: {
        "first_seen": None,
        "last_seen": None,
        "project_count": 0,
        "projects": [],
    })

    for project in projects:
        if not project.skills:
            continue

        first_date, last_date, duration_days = db_manager.get_project_duration(project.id)

        for skill in project.skills:
            entry = skill_map[skill]
            entry["project_count"] += 1
            entry["projects"].append({
                "project_id": project.id,
                "project_name": _display_name(project),
                "project_type": project.project_type,
                "first_activity_date": first_date.isoformat() if first_date else None,
                "last_activity_date": last_date.isoformat() if last_date else None,
                "duration_days": duration_days,
            })

            if first_date:
                if entry["first_seen"] is None or first_date < entry["first_seen"]:
                    entry["first_seen"] = first_date
            if last_date:
                if entry["last_seen"] is None or last_date > entry["last_seen"]:
                    entry["last_seen"] = last_date

    timeline = []
    for skill, data in skill_map.items():
        timeline.append({
            "name": skill,
            "first_seen": data["first_seen"].isoformat() if data["first_seen"] else None,
            "last_seen": data["last_seen"].isoformat() if data["last_seen"] else None,
            "project_count": data["project_count"],
            "projects": data["projects"],
        })

    timeline.sort(key=lambda x: (x["first_seen"] or ""))
    return {"skills": timeline}