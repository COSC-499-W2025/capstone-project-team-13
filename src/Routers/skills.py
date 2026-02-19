from fastapi import APIRouter
from src.Services.skills_service import get_skills, get_skill_detail

router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)

#get list of skills, with projects that contain each one.
@router.get("/")
def read_skills():
    return get_skills()


#get skills endpoint by name
@router.get("/{skill_name}")
def read_skill(skill_name: str):
    return get_skill_detail(skill_name)

