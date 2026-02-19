from fastapi import APIRouter
from src.Services.skills_service import get_skills

router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)

@router.get("/")
def read_skills():
    return get_skills()
