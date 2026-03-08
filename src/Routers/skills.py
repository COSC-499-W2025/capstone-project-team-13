from fastapi import APIRouter, Depends
from typing import Optional
from src.Services.auth_service import get_current_user_id
from src.Services.skills_service import get_skills, get_skill_detail

router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)

#get list of skills, with projects that contain each one.
@router.get("/")
def read_skills(user_id: Optional[int] = Depends(get_current_user_id)):
    return get_skills(user_id=user_id)


#get skills endpoint by name
@router.get("/{skill_name}")
def read_skill(skill_name: str, user_id: Optional[int] = Depends(get_current_user_id)):
    return get_skill_detail(skill_name, user_id=user_id)