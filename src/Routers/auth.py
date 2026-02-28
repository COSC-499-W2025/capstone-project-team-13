"""
Authentication Routes
====================
API endpoints for user signup, login, and profile access.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.Databases.database import db_manager
from src.Services.auth_service import hash_password, verify_password, create_access_token, require_auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Models
class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "password": "securepassword123"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "jane@example.com",
                "password": "securepassword123"
            }
        }


class AuthResponse(BaseModel):
    user: dict
    token: str


# Endpoints
@router.post("/signup", response_model=AuthResponse)
def signup(body: SignupRequest):
    """
    Create a new user account.
    
    Returns user info and authentication token.
    """
    # Validation
    if len(body.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )
    
    # Check if email already exists
    existing = db_manager.get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create user
    try:
        user = db_manager.create_user({
            'first_name': body.first_name,
            'last_name': body.last_name,
            'email': body.email,
            'password_hash': hash_password(body.password)
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )
    
    # Generate token
    token = create_access_token(user.id)
    
    return {
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        },
        "token": token
    }


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    """
    Login with email and password.
    
    Returns user info and authentication token.
    """
    # Find user
    user = db_manager.get_user_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_access_token(user.id)
    
    return {
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        },
        "token": token
    }


@router.get("/me")
def get_current_user(user_id: int = Depends(require_auth)):
    """
    Get current authenticated user's profile.
    
    Requires valid authentication token.
    """
    user = db_manager.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Get counts
    education_count = len(db_manager.get_education_for_user(user_id))
    work_count = len(db_manager.get_work_history_for_user(user_id))
    project_count = db_manager.count_projects_for_user(user_id)
    
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "education_count": education_count,
        "work_history_count": work_count,
        "project_count": project_count,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.get("/guest/projects/count")
def get_guest_project_count():
    """
    Get count of guest projects (no authentication required).
    
    Useful for showing "You have N unsaved projects" messages.
    """
    count = db_manager.count_projects_for_user(None)
    return {
        "count": count,
        "message": "Sign up to save your projects permanently" if count > 0 else "No guest projects"
    }