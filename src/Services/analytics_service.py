from collections import defaultdict
from itertools import combinations
from typing import Optional
from src.Databases.database import db_manager

from math import log

def get_skill_cooccurrence(user_id: Optional[int] = None):
    """
    Returns a list of skill pairs with:
    - count of projects they appear together in
    - project list
    Filtered by user's projects (or guest projects if not logged in)
    """
    # Filter projects by user
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()
    
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


# for skill analytics /produces deeper insight. This function gathers raw skills first
def get_raw_skills_with_projects(user_id: Optional[int] = None):
    """Get raw skills data filtered by user's projects"""
    skills_map = defaultdict(list)
    
    # Filter projects by user
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()

    for project in projects:
        for skill in project.skills or []:
            skills_map[skill].append({
                "project_id": project.id,
                "project_name": project.name
            })

    raw_skills = []
    for skill, project_list in skills_map.items():
        raw_skills.append({
            "skill": skill,
            "count": len(project_list),
            "projects": project_list
        })

    raw_skills.sort(key=lambda x: x["count"], reverse=True)
    return raw_skills

# this function generates the insights

def get_skill_insights(user_id: Optional[int] = None):
    """Generate skill insights from user's projects"""
    raw_skills = get_raw_skills_with_projects(user_id=user_id)
    co_occurrence = get_skill_cooccurrence(user_id=user_id)

    top_skills = raw_skills[:5]  # top 5 most common skills
    most_common_pair = co_occurrence[0] if co_occurrence else None

    # skill diversity: # of distinct skills / # of projects
    total_skills = len(raw_skills)
    
    # Count user's projects
    if user_id:
        total_projects = db_manager.count_projects_for_user(user_id)
    else:
        total_projects = db_manager.count_projects_for_user(None)
    
    skill_diversity = round(total_skills / total_projects, 3) if total_projects else 0

    return {
        "top_skills": top_skills,
        "most_common_pair": most_common_pair,
        "skill_diversity": skill_diversity
    }


# function gathers both to display to user.
def get_full_skill_analytics(user_id: Optional[int] = None):
    """Get complete skill analytics for user's projects"""
    raw = get_raw_skills_with_projects(user_id=user_id)
    insights = get_skill_insights(user_id=user_id)
    return {
        "raw": {
            "skills": raw,
            "co_occurrence": get_skill_cooccurrence(user_id=user_id)
        },
        "insights": insights
    }

