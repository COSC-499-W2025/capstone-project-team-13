from src.Databases.database import db_manager
from src.Analysis.summarizeProjects import summarize_projects

def fetch_projects_for_summary():
    """Convert database Project objects into summarizer-ready dicts."""
    projects = db_manager.get_all_projects()
    project_dicts = []

    for p in projects:
        contributors = db_manager.get_contributors_for_project(p.id)
        total_commits = sum(c.commit_count or 0 for c in contributors)
        num_contributors = len(contributors)

        # Map DB fields → summarizer fields
        project_dicts.append({
            "project_name": p.name,
            "time_spent": max(p.lines_of_code or 0, 1),  # proxy for effort
            "success_score": min(1.0, (p.file_count or 0) / 50),  # proxy for success
            "contribution_score": min(1.0, total_commits / 20) if num_contributors else 0.5,
            "skills": list(set(p.languages + p.frameworks))
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
