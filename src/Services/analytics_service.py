from collections import defaultdict
from itertools import combinations
from src.Databases.database import db_manager

def get_skill_cooccurrence(min_count: int = 1):
    projects = db_manager.get_all_projects()
    pair_counts = defaultdict(int)

    for project in projects:
        skills = project.skills or []

        # Ensure consistency
        unique_skills = sorted(set(skills))

        for skill_a, skill_b in combinations(unique_skills, 2):
            pair_counts[(skill_a, skill_b)] += 1

    results = []
    for (a, b), count in pair_counts.items():
        if count >= min_count:
            results.append({
                "skill_1": a,
                "skill_2": b,
                "count": count
            })

    # Most common pairs first
    results.sort(key=lambda x: x["count"], reverse=True)

    return results
