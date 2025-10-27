"""
project_summarizer.py
------------------------------------
Analyzes and summarizes a user's projects into a balanced overview.

Implements:
 - normalization of numeric metrics (time_spent, success_score, contribution_score)
 - weighted overall score computation
 - greedy diversity-aware selection (approximate max-coverage for top-k)
 - human-readable summary generation
"""

from typing import List, Dict, Any, Optional
from copy import deepcopy


def _min_max_normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def summarize_projects(
    projects: List[Dict[str, Any]],
    top_k: int = 3,
    weights: Optional[Dict[str, float]] = None,
    diversity_alpha: float = 0.1,
) -> Dict[str, Any]:
    """
    Summarize a list of project dicts into a balanced overview.
    """
    if weights is None:
        weights = {"time": 0.4, "success": 0.3, "contribution": 0.3}

    items = deepcopy(projects)
    for p in items:
        p.setdefault("project_name", "<unnamed>")
        p.setdefault("time_spent", 0.0)
        p.setdefault("success_score", 0.0)
        p.setdefault("contribution_score", 0.0)
        p.setdefault("skills", [])
        p["skills"] = list(dict.fromkeys([str(s).strip() for s in p["skills"] if s]))

    if not items:
        return {
            "selected_projects": [],
            "all_projects_scored": [],
            "unique_skills": [],
            "average_score": 0.0,
            "summary": "No projects provided. No summary generated."
        }

    # --- Normalize numeric metrics ---
    t_norm = _min_max_normalize([p["time_spent"] for p in items])
    s_norm = _min_max_normalize([p["success_score"] for p in items])
    c_norm = _min_max_normalize([p["contribution_score"] for p in items])

    for i, p in enumerate(items):
        p["_time_norm"], p["_success_norm"], p["_contrib_norm"] = t_norm[i], s_norm[i], c_norm[i]
        score = (
            weights["time"] * t_norm[i]
            + weights["success"] * s_norm[i]
            + weights["contribution"] * c_norm[i]
        )
        p["_overall_score"] = max(0.0, min(1.0, score))

    all_skills = set(s for p in items for s in p["skills"])
    total_skill_count = len(all_skills) or 1

    remaining = sorted(items, key=lambda x: (x["_overall_score"], x["project_name"]), reverse=True)
    selected, covered = [], set()

    for _ in range(min(top_k, len(items))):
        best_idx, best_val = None, -float("inf")
        for i, cand in enumerate(remaining):
            new_skills = set(cand["skills"]) - covered
            diversity = len(new_skills) / total_skill_count
            val = cand["_overall_score"] + diversity_alpha * diversity
            if val > best_val:
                best_val, best_idx = val, i
        if best_idx is None:
            break
        chosen = remaining.pop(best_idx)
        selected.append(chosen)
        covered.update(chosen["skills"])

    unique_skills = sorted(covered)
    avg_score = round(sum(p["_overall_score"] for p in selected) / max(1, len(selected)), 4)

    # --- Summary text ---
    if not selected:
        summary = "No projects selected."
    else:
        summary = (
            f"Across {len(selected)} key project{'s' if len(selected) != 1 else ''}, "
            f"the user demonstrates balanced strengths in effort, impact, and collaboration. "
            f"The selected projects showcase {len(unique_skills)} distinct skill"
            f"{'s' if len(unique_skills) != 1 else ''}"
            f"{'' if not unique_skills else ': ' + ', '.join(unique_skills)}. "
            f"The average project score is {avg_score:.2f}, reflecting consistent performance "
            f"and broad skill coverage."
        )

    # --- Output ---
    return {
        "selected_projects": [
            {
                "project_name": p["project_name"],
                "overall_score": round(p["_overall_score"], 4),
                "skills": p["skills"],
                "time_spent": p["time_spent"],
                "success_score": p["success_score"],
                "contribution_score": p["contribution_score"]
            }
            for p in selected
        ],
        "all_projects_scored": items,
        "unique_skills": unique_skills,
        "average_score": avg_score,
        "summary": summary
    }
