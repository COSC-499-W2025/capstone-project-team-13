# src/Analysis/importance_ranking.py

from src.Databases.database import Project, db_manager

def get_ranked_projects():
    """
    Returns a list of Project objects sorted by their importance_score
    from highest → lowest.
    """
    session = db_manager.get_session()
    try:
        ranked = (
            session.query(Project)
            .order_by(Project.importance_score.desc())
            .all()
        )
        return ranked
    finally:
        session.close()


if __name__ == "__main__":
    ranked = get_ranked_projects()
    for p in ranked:
        print(f"[{p.id}] {p.name} – {p.importance_score}")
