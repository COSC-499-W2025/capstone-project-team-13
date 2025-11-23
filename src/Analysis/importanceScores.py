# src/Analysis/importance_scoring.py

from src.Databases.database import db_manager, Project
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload

# ------------------------
#  YOUR SCORING FORMULA
# ------------------------
def calculate_importance_score(project):
    """
    Returns a percentage-based importance score (0-100)
    factoring in size, recency, engagement, and metadata richness.
    """

    # -----------------------------
    # 1. Recency: more recent → higher
    # -----------------------------
    now = datetime.now(timezone.utc)
    date_modified = project.date_modified
    if date_modified:
        if date_modified.tzinfo is None:
            # assume UTC if naive
            date_modified = date_modified.replace(tzinfo=timezone.utc)
        days_since_update = (now - date_modified).days
        recency_score = max(0, min(1, (365 - days_since_update) / 365)) * 100
    else:
        recency_score = 0

    # -----------------------------
    # 2. Size / Depth
    # -----------------------------
    loc_score = min(project.lines_of_code / 10000, 1) * 100
    word_score = min(project.word_count / 5000, 1) * 100
    file_score = min(project.file_count / 100, 1) * 100
    size_score = (loc_score * 0.4 + word_score * 0.3 + file_score * 0.3)

    # -----------------------------
    # 3. Engagement / contributions
    # -----------------------------
    contrib_count = len(project.contributors) if project.contributors else 0
    keyword_count = len(project.keywords) if project.keywords else 0
    file_count_actual = len(project.files) if project.files else 0

    contrib_score = min(contrib_count / 20, 1) * 100
    keyword_score = min(keyword_count / 50, 1) * 100
    file_count_score = min(file_count_actual / 100, 1) * 100
    engagement_score = (contrib_score * 0.4 + keyword_score * 0.3 + file_count_score * 0.3)

    # -----------------------------
    # 4. Metadata richness
    # -----------------------------
    skills_score = min(len(project.skills) / 10, 1) * 100
    languages_score = min(len(project.languages) / 5, 1) * 100
    tags_score = min(len(project.tags) / 10, 1) * 100
    metadata_score = (skills_score * 0.4 + languages_score * 0.3 + tags_score * 0.3)

    # -----------------------------
    # Final weighted score
    # -----------------------------
    total_score = (
        recency_score * 0.10 +
        size_score * 0.25 +
        engagement_score * 0.30 +
        metadata_score * 0.35
    )

    return round(total_score, 2)


# ------------------------
# APPLY SCORES TO THE DB
# ------------------------
def assign_importance_scores():
    """
    Loads all projects with contributors, files, and keywords eagerly loaded,
    computes score for each, and saves the score back to the database.
    """
    session = db_manager.get_session()
    try:
        projects = session.query(Project).options(
            joinedload(Project.contributors),
            joinedload(Project.files),
            joinedload(Project.keywords)
        ).all()

        if not projects:
            print("No projects found.")
            return []

        results = []

        for p in projects:
            score = calculate_importance_score(p)

            # Save score back into DB
            p.importance_score = score
            session.add(p)

            results.append((p, score))

        session.commit()
        return results
    finally:
        session.close()


if __name__ == "__main__":
    scored = assign_importance_scores()
    for p, s in scored:
        print(f"[{p.id}] {p.name} → {s}")
