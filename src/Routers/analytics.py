from fastapi import APIRouter, Depends
from typing import Optional
from src.Services.auth_service import get_current_user_id
from src.Services.analytics_service import get_skill_cooccurrence, get_full_skill_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/co-occurrence")
def skill_cooccurrence(user_id: Optional[int] = Depends(get_current_user_id)):
    """
    Returns skill co-occurrence across projects with project names
    """
    return {
        "pairs": get_skill_cooccurrence(user_id=user_id)
    }


@router.get("/skills")
def skills_analytics(user_id: Optional[int] = Depends(get_current_user_id)):
    """
    Returns raw skill data with projects and co-occurrence,
    plus insights like top skills and diversity
    """
    return get_full_skill_analytics(user_id=user_id)