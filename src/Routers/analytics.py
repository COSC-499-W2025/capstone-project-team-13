from fastapi import APIRouter
from src.Services.analytics_service import get_skill_cooccurrence, get_full_skill_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/co-occurrence")
def skill_cooccurrence():
    """
    Returns skill co-occurrence across projects with project names
    """
    return {
        "pairs": get_skill_cooccurrence()
    }


@router.get("/skills")
def skills_analytics():
    """
    Returns raw skill data with projects and co-occurrence,
    plus insights like top skills and diversity
    """
    return get_full_skill_analytics()
