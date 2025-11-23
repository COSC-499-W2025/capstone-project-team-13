# src/Analysis/importance_scoring.py

from src.Databases.database import db_manager

# ------------------------
#  YOUR SCORING FORMULA
# ------------------------
def calculate_importance_score(project):
    """
    Stub scoring function — replace with your actual logic.
    """
    score = 0

    # Example starter logic – replace this:
    score += (project.lines_of_code or 0) * 0.001
    score += (project.word_count or 0) * 0.002
    score += (project.file_count or 0) * 0.5

    return round(score, 2)


# ------------------------
# APPLY SCORES TO THE DB
# ------------------------
def assign_importance_scores():
    """
    Loads all projects, computes score for each,
    and saves the score back to the database.
    """
    projects = db_manager.get_all_projects()

    if not projects:
        print("No projects found.")
        return []

    results = []

    for p in projects:
        score = calculate_importance_score(p)

        # Save score back into DB
        db_manager.update_project(
            p.id,
            {"importance_score": score}
        )

        results.append((p, score))

    return results


if __name__ == "__main__":
    # Allow this file to be run directly
    scored = assign_importance_scores()
    for p, s in scored:
        print(f"[{p.id}] {p.name} → {s}")
