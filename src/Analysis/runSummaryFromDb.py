from src.Databases.database import db_manager
from src.Analysis.summarizeProjects import summarize_projects
from datetime import datetime

def _infer_activity_type_and_time(p):
    """
    Map Project → (activity_type, time_spent)
    - code  → lines_of_code
    - text  → word_count
    - media → total_size_bytes
    Fallback to heuristics if project_type is missing.
    """
    ptype = (p.project_type or "").lower() if p.project_type else ""

    # Use explicit project_type if set (from detect_project_type)
    if ptype == "code":
        activity_type = "code"
        time_spent = p.lines_of_code or 0
    elif ptype == "text":
        activity_type = "text"
        time_spent = p.word_count or 0
    elif ptype == "media":
        activity_type = "media"
        time_spent = p.total_size_bytes or 0
    else:
        # Heuristic fallback
        if p.lines_of_code and p.lines_of_code > 0:
            activity_type = "code"
            time_spent = p.lines_of_code
        elif p.word_count and p.word_count > 0:
            activity_type = "text"
            time_spent = p.word_count
        elif p.total_size_bytes and p.total_size_bytes > 0:
            activity_type = "media"
            time_spent = p.total_size_bytes
        else:
            activity_type = "unknown"
            time_spent = 0

    return activity_type, max(time_spent, 1)  # avoid 0 for normalization


def _compute_success_score(p, activity_type: str) -> float:
    """
    Return a normalized success score in [0, 1].
    Preference order:
    1) Stored success_score attribute (if present)
    2) success_metrics evidence (test coverage + README badges)
    3) Heuristic based on project size
    """
    # 1) Stored success_score (if it exists on the model)
    raw = getattr(p, "success_score", None)
    if raw is not None:
        try:
            raw_val = float(raw)
            return raw_val / 100.0 if raw_val > 1 else raw_val
        except (TypeError, ValueError):
            pass

    # 2) Evidence-based score from success_metrics (if available)
    metrics = getattr(p, "success_metrics", None)
    if isinstance(metrics, dict) and metrics:
        score = 0.0
        tc = metrics.get("test_coverage")
        if tc:
            score += float(tc) * 0.6
        badges = metrics.get("readme_badges")
        if badges:
            score += min(len(badges) * 10, 40)
        if score > 0:
            return min(score, 100.0) / 100.0

    # 3) Heuristic fallback by project type/size
    files = p.file_count or 0
    if activity_type == "code":
        loc = p.lines_of_code or 0
        return min(100.0, (files * 5) + (loc / 200.0)) / 100.0
    if activity_type == "text":
        words = p.word_count or 0
        return min(100.0, (files * 5) + (words / 500.0)) / 100.0
    if activity_type == "media":
        size_mb = (p.total_size_bytes or 0) / (1024 * 1024)
        return min(100.0, (files * 5) + (size_mb * 2.0)) / 100.0

    return min(100.0, files * 5) / 100.0

def fetch_projects_for_summary():
    """Convert database Project objects into summarizer-ready dicts."""
    projects = db_manager.get_all_projects()
    project_dicts = []

    for p in projects:
        contributors = db_manager.get_contributors_for_project(p.id)
        total_commits = sum(c.commit_count or 0 for c in contributors)
        num_contributors = len(contributors)

        activity_type, time_spent = _infer_activity_type_and_time(p)
        success_score = _compute_success_score(p, activity_type)

        start_dt = p.date_created or p.date_scanned
        end_dt = p.date_modified or p.date_scanned or start_dt

        if start_dt and end_dt:
            start_date = start_dt.date() if hasattr(start_dt, "date") else start_dt
            end_date = end_dt.date() if hasattr(end_dt, "date") else end_dt
            duration_days = (end_date - start_date).days + 1
        else:
            duration_days = 0


        # Map DB fields → summarizer fields
        project_dicts.append({
            "project_name": p.name,
            "activity_type": activity_type,
            "time_spent": time_spent,
            "success_score": success_score,
            "contribution_score": min(1.0, total_commits / 20) if num_contributors else 0.5,
            "skills": list(set(p.languages + p.frameworks)),
            "first_activity_date": start_dt,
            "last_activity_date": end_dt,
            "duration_days": duration_days,  

        })
    return project_dicts


def main():
    projects_data = fetch_projects_for_summary()
    if not projects_data:
        print("No projects found in the database.")
        return

    result = summarize_projects(projects_data, top_k=3)
    print("\nSUMMARY:\n", result["summary"])
    print("\nTOP PROJECTS:")
    for proj in result["selected_projects"]:
        print(f" - {proj['project_name']} ({proj['overall_score']}) → {', '.join(proj['skills'])}")


if __name__ == "__main__":
    main()

# ------------------------------------------------------------
# SUMMARY OF LOGIC:
# This module connects to the local SQLite database (projects_data.db)
# via DatabaseManager, retrieves stored project records, and formats
# their key metadata into the input structure required by
# summarize_projects(). It then calls the summarizer to compute
# top-ranked projects and prints or returns the resulting metrics
# and summary. Essentially, this file acts as the integration layer
# between database-stored project data and the summarization engine.
# ------------------------------------------------------------
