from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.Services.resume_service import get_resume, generate_resume, edit_resume

router = APIRouter(prefix="/resume", tags=["Resume"])


class GenerateRequest(BaseModel):
    project_id: int
    num_bullets: int = 3


class EditRequest(BaseModel):
    bullets: List[str]
    header: Optional[str] = None


@router.post("/generate")
def generate_resume_endpoint(body: GenerateRequest):
    result = generate_resume(body.project_id, body.num_bullets)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/{project_id}")
def get_resume_endpoint(project_id: int):
    result = get_resume(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return result


@router.post("/{project_id}/edit")
def edit_resume_endpoint(project_id: int, body: EditRequest):
    result = edit_resume(project_id, body.bullets, body.header)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result