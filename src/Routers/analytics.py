from fastapi import APIRouter
from src.Services.analytics_service import get_skill_cooccurrence

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/co-occurrence")
def skill_cooccurrence(min_count: int = 1):
    return {
        "pairs": get_skill_cooccurrence(min_count)
    }
