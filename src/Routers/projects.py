"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import zipfile
import shutil
from src.Databases.database import db_manager

from src.Services.projects_service import process_uploaded_path

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# post upload projects endpoint
@router.post("/upload")
async def upload_project(file: UploadFile = File(...)):
    project_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"{project_id}_{file.filename}"

    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # If ZIP, extract
    if upload_path.suffix == ".zip":
        extract_dir = UPLOAD_DIR / project_id
        extract_dir.mkdir()

        with zipfile.ZipFile(upload_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        process_path = extract_dir
    else:
        process_path = upload_path

    result = process_uploaded_path(str(process_path))
    return result

# get projects endpoint

@router.get("")
def list_projects():
    projects = db_manager.get_all_projects()

    return [p.to_dict() for p in projects]



# get project by id endpoint
@router.get("/{project_id}")
def get_project(project_id: int):
    project = db_manager.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project.to_dict(include_counts=True)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
from typing import Optional
import uuid
import zipfile
import shutil
from src.Databases.database import db_manager
from src.Services.projects_service import process_uploaded_path
from src.Services.auth_service import get_current_user_id

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_project(
    file: UploadFile = File(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """
    Upload and scan a project file or ZIP archive.
    
    - **file**: Project file or ZIP containing project files
    - **Authorization header**: Optional Bearer token for authenticated users
    
    Returns scanned project details.
    """
    project_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"{project_id}_{file.filename}"

    # Save uploaded file
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # If ZIP, extract
    if upload_path.suffix == ".zip":
        extract_dir = UPLOAD_DIR / project_id
        extract_dir.mkdir()

        with zipfile.ZipFile(upload_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        process_path = extract_dir
    else:
        process_path = upload_path

    # Process with user_id
    result = process_uploaded_path(str(process_path), user_id=user_id)
    return result


@router.get("")
def list_projects(user_id: Optional[int] = Depends(get_current_user_id)):
    """
    Get all projects for current user (or guest projects if not authenticated).
    
    - **Authorization header**: Optional Bearer token
    
    Returns list of projects filtered by user ownership.
    """
    # Filter by user
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()
    
    return [p.to_dict() for p in projects]


@router.get("/{project_id}")
def get_project(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """
    Get a single project by ID.
    
    - **project_id**: Project database ID
    - **Authorization header**: Optional Bearer token
    
    Returns project details if user owns it, 403 otherwise.
    """
    project = db_manager.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify ownership
    if project.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this project"
        )
    
    return project.to_dict(include_counts=True)