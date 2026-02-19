from fastapi import APIRouter
from src.Services.analytics_service import get_skill_cooccurrence, get_skill_analytics

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
    return get_skill_analytics()
