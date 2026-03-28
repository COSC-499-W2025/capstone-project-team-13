from fastapi import APIRouter, HTTPException
from src.Databases.database import db_manager, User

router = APIRouter(prefix="/public", tags=["Public Portfolios"])


@router.get("/portfolios")
def list_public_portfolios():
    """List all users who have opted to make their portfolio public."""
    session = db_manager.get_session()
    try:
        users = session.query(User).filter(User.portfolio_public == True).all()  # noqa: E712
        result = []
        for u in users:
            portfolio = u.portfolio or {}
            projects = portfolio.get("projects", [])
            visible = [p for p in projects if not p.get("is_hidden", False)]
            all_skills = []
            for p in visible:
                all_skills.extend(p.get("skills", []))
                all_skills.extend(p.get("languages", p.get("tech_stack", [])))
            unique_skills = list(dict.fromkeys(all_skills))[:8]
            result.append({
                "user_id": u.id,
                "display_name": f"{u.first_name} {u.last_name}",
                "project_count": len(visible),
                "top_skills": unique_skills,
                "summary": portfolio.get("summary_text", ""),
            })
        return {"portfolios": result, "total": len(result)}
    finally:
        session.close()


@router.get("/portfolios/{user_id}")
def get_public_portfolio(user_id: int):
    """Get a specific user's public portfolio. Returns 404 if not public."""
    user = db_manager.get_user(user_id)
    if user is None or not getattr(user, "portfolio_public", False):
        raise HTTPException(status_code=404, detail="Portfolio not found or not public")
    portfolio = user.portfolio or {}
    projects = portfolio.get("projects", [])
    visible = [p for p in projects if not p.get("is_hidden", False)]
    return {
        "user_id": user.id,
        "display_name": f"{user.first_name} {user.last_name}",
        "projects": visible,
        "stats": portfolio.get("stats", {}),
        "summary_text": portfolio.get("summary_text", ""),
    }
