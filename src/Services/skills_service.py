from collections import defaultdict
from src.Databases.database import db_manager

def get_skills():
    projects = db_manager.get_all_projects()

    skill_map = defaultdict(lambda: {
        "count": 0,
        "projects": []
    })

    for project in projects:
        # If skills are stored as JSON/list → this works directly
        for skill in project.skills:
            skill_map[skill]["count"] += 1
            skill_map[skill]["projects"].append({
                "project_id": project.id,
                "project_name": project.name
            })

    return {
        "skills": [
            {
                "name": skill,
                "count": data["count"],
                "projects": data["projects"]
            }
            for skill, data in skill_map.items()
        ]
    }
