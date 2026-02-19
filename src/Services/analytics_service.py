from collections import defaultdict
from itertools import combinations
from src.Databases.database import db_manager

from math import log

def get_skill_cooccurrence():
    """
    Returns a list of skill pairs with:
    - count of projects they appear together in
    - project list
    """
    projects = db_manager.get_all_projects()
    pair_map = defaultdict(set)  # (skill_a, skill_b) -> set(project names)

    for project in projects:
        skills = project.skills or []

        # Only consider unique skills per project
        unique_skills = sorted(set(skills))

        # Create all pairs
        for skill_a, skill_b in combinations(unique_skills, 2):
            pair_map[(skill_a, skill_b)].add(project.name)

    # Format output
    result = []
    for (skill_a, skill_b), project_names in pair_map.items():
        result.append({
            "skill_1": skill_a,
            "skill_2": skill_b,
            "count": len(project_names),
            "projects": [{"project_name": name} for name in project_names]
        })

    # Sort by count descending
    result.sort(key=lambda x: x["count"], reverse=True)
    return result


# for skill analytics /produces deeper insight. 
def get_skill_analytics():
    projects = db_manager.get_all_projects()

    skill_counts = defaultdict(int)

    for project in projects:
        for skill in project.skills or []:
            skill_counts[skill] += 1

    co_occurrence = get_skill_cooccurrence()

    total_projects = len(projects)
    total_skills = len(skill_counts)

    top_skills = sorted(
        skill_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    diversity = round(total_skills / total_projects, 3) if total_projects else 0

    most_common_pair = co_occurrence[0] if co_occurrence else None

    return {
        "raw": {
            "skill_counts": [
                {"skill": s, "count": c}
                for s, c in skill_counts.items()
            ],
            "co_occurrence": co_occurrence
        },
        "insights": {
            "top_skills": [
                {"skill": s, "count": c}
                for s, c in top_skills
            ],
            "most_common_pair": most_common_pair,
            "skill_diversity": diversity
        }
    }

