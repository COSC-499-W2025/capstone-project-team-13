from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.Databases.database import db_manager
from src.Services.auth_service import get_current_user_id, require_auth

router = APIRouter(prefix="/user", tags=["User"])

class GithubUsernameRequest(BaseModel):
    github_username: str

@router.post("/github-username")
def set_github_username(
    body: GithubUsernameRequest,
    user_id: int = Depends(require_auth)
):
    session = db_manager.get_session()
    try:
        user = session.query(db_manager.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.github_username = body.github_username
        session.commit()
        return {"success": True, "github_username": user.github_username}
    finally:
        session.close()

@router.get("/github-username")
def get_github_username(user_id: int = Depends(require_auth)):
    session = db_manager.get_session()
    try:
        user = session.query(db_manager.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"github_username": user.github_username}
    finally:
        session.close()
