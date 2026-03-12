from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
from typing import Optional
import uuid
import zipfile
import shutil
from src.Databases.database import db_manager
from src.Services.projects_service import process_uploaded_path, upload_project_thumbnail
from src.Services.auth_service import get_current_user_id, require_auth
from src.UserPrompts.config_integration import has_ai_consent

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

@router.post("/{project_id}/analyze")
def analyze_project_with_ai(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id),
):
    """
    Generate an AI description for a project and persist it.

    Requires AI consent to be granted (via Settings -> Consent).
    Returns the updated project with the new ai_description field.
    """
    if not has_ai_consent():
        raise HTTPException(
            status_code=403,
            detail="AI consent not granted. Enable AI consent in Settings first.",
        )

    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Optional ownership check (non-fatal for guest projects)
    if user_id and project.user_id and project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        from src.AI.ai_project_analyzer import AIProjectAnalyzer

        analyzer = AIProjectAnalyzer()
        results = analyzer.analyze_project_complete(project_id)

        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])

        # Persist ai_description to the database
        analyzer.update_database_with_analysis(project_id, results)

        # Return refreshed project
        updated = db_manager.get_project(project_id)
        return {
            "message": "AI analysis complete",
            "ai_description": results.get("overview", ""),
            "project": updated.to_dict() if updated else {},
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/{project_id}/thumbnail")
async def upload_thumbnail(
    project_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(require_auth)
):
    """
    Upload a thumbnail image for an existing project.
    
    - **project_id**: Project database ID
    - **file**: Image file (.jpg, .jpeg, .png, .gif, .webp, .bmp, .svg)
    - **Authorization header**: Optional Bearer token
    """
    thumbnail_path = UPLOAD_DIR / f"thumb_{project_id}_{file.filename}"

    with open(thumbnail_path, "wb") as f:
        f.write(await file.read())

    try:
        result = upload_project_thumbnail(project_id, str(thumbnail_path), user_id=user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    return result