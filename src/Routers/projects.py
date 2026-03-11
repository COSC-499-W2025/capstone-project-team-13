from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import uuid
import zipfile
import os
from datetime import datetime, timezone
from src.Databases.database import db_manager
from src.Services.projects_service import process_uploaded_path, upload_project_thumbnail
from src.Services.auth_service import get_current_user_id, require_auth
from src.Analysis.multiProjectZip import processZipFile
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.incrementalZipHandler import detect_project_type
from src.Analysis.projectcollabtype import identify_project_type
from src.Analysis.roleAttribution import get_role_from_contribution
from src.Analysis.file_hasher import compute_file_hash

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class RoleAssignmentRequest(BaseModel):
    contributor: Optional[str] = None
    contribution_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    role_type: str = "Developer"


def _assert_project_access(project_id: int, user_id: Optional[int]):
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this project")
    return project


def _store_uploaded_file(file: UploadFile, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "wb") as f:
        f.write(file.file.read())
    return destination


def _get_project_analysis_path(project_id: int, user_id: Optional[int]) -> tuple[object, str]:
    project = _assert_project_access(project_id, user_id)
    path = os.path.abspath(os.path.expanduser(project.file_path))
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Path not found for project {project_id}: {path}")
    return project, path


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


@router.post("/upload/multi-zip")
async def upload_multi_zip(
    file: UploadFile = File(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    project_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"{project_id}_{file.filename}"
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    try:
        results = processZipFile(str(upload_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process ZIP: {e}")

    return {
        "status": "processed",
        "count": len(results) if results else 0,
        "projects": results or [],
        "user_id": user_id,
    }


@router.post("/{project_id}/upload/files")
async def add_files_to_project(
    project_id: int,
    files: list[UploadFile] = File(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    project = _assert_project_access(project_id, user_id)

    saved = []
    target_dir = UPLOAD_DIR / f"project_{project_id}"
    for upload in files:
        file_path = _store_uploaded_file(upload, target_dir / upload.filename)
        file_hash = compute_file_hash(str(file_path))

        if db_manager.file_exists_in_project(project_id, file_hash):
            continue

        stat = file_path.stat()
        db_manager.add_file_to_project({
            "project_id": project_id,
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_type": file_path.suffix.lower(),
            "file_size": stat.st_size,
            "file_created": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            "file_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            "file_hash": file_hash,
        })
        saved.append(file_path.name)

    if saved:
        db_manager.update_project(project_id, {"file_count": (project.file_count or 0) + len(saved)})

    return {
        "status": "updated",
        "project_id": project_id,
        "files_added": len(saved),
        "added_files": saved,
    }


@router.post("/{project_id}/upload/zip")
async def add_zip_to_project(
    project_id: int,
    file: UploadFile = File(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    _assert_project_access(project_id, user_id)

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    request_id = str(uuid.uuid4())
    zip_path = UPLOAD_DIR / f"{request_id}_{file.filename}"
    with open(zip_path, "wb") as f:
        f.write(await file.read())

    extract_dir = UPLOAD_DIR / f"extract_{request_id}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ZIP archive: {e}")

    file_payloads = []
    for root, _, names in os.walk(extract_dir):
        for name in names:
            path_obj = Path(root) / name
            stat = path_obj.stat()
            file_hash = compute_file_hash(str(path_obj))
            if db_manager.file_exists_in_project(project_id, file_hash):
                continue
            db_manager.add_file_to_project({
                "project_id": project_id,
                "file_path": str(path_obj),
                "file_name": path_obj.name,
                "file_type": path_obj.suffix.lower(),
                "file_size": stat.st_size,
                "file_created": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
                "file_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                "file_hash": file_hash,
            })
            file_payloads.append(path_obj.name)

    if file_payloads:
        project = db_manager.get_project(project_id)
        db_manager.update_project(project_id, {"file_count": (project.file_count or 0) + len(file_payloads)})

    return {
        "status": "updated",
        "project_id": project_id,
        "files_added": len(file_payloads),
        "added_files": file_payloads,
    }


@router.post("/{project_id}/analyze/detect-type")
def analyze_detect_type(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    _, path = _get_project_analysis_path(project_id, user_id)
    return detect_project_type(path)


@router.post("/{project_id}/analyze/coding")
def analyze_coding_project(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    _, path = _get_project_analysis_path(project_id, user_id)
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Path must be a directory")
    project_id = scan_coding_project(path, user_id=user_id)
    if not project_id:
        return {"status": "skipped", "reason": "No code files found"}
    project = db_manager.get_project(project_id)
    return {
        "status": "created",
        "project_id": project.id,
        "project_name": project.name,
        "project_type": project.project_type,
    }


@router.post("/{project_id}/analyze/media")
def analyze_media_project(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    _, path = _get_project_analysis_path(project_id, user_id)
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Path must be a directory")
    project_id = scan_media_project(path, user_id=user_id)
    if not project_id:
        return {"status": "skipped", "reason": "No media files found"}
    project = db_manager.get_project(project_id)
    return {
        "status": "created",
        "project_id": project.id,
        "project_name": project.name,
        "project_type": project.project_type,
    }


@router.post("/{project_id}/analyze/text")
def analyze_text_project(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    _, path = _get_project_analysis_path(project_id, user_id)
    project_id = scan_text_document(path, single_file=True, user_id=user_id)
    if not project_id:
        return {"status": "skipped", "reason": "No text content found"}
    project = db_manager.get_project(project_id)
    return {
        "status": "created",
        "project_id": project.id,
        "project_name": project.name,
        "project_type": project.project_type,
    }


@router.get("/{project_id}/roles")
def get_project_roles(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    project = _assert_project_access(project_id, user_id)
    contributors = db_manager.get_contributors_for_project(project_id)
    return {
        "project_id": project.id,
        "project_name": project.name,
        "user_role": project.user_role,
        "user_contribution_percent": project.user_contribution_percent,
        "contributors": [
            {
                "name": c.name,
                "identifier": c.contributor_identifier,
                "contribution_percent": c.contribution_percent,
                "commit_count": c.commit_count,
            }
            for c in contributors
        ],
    }


@router.post("/{project_id}/roles")
def assign_project_role(
    project_id: int,
    payload: RoleAssignmentRequest = Body(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    project = _assert_project_access(project_id, user_id)

    collaboration_type = identify_project_type(project.file_path, {"files": []})
    is_collaborative = collaboration_type == "Collaborative Project"

    contribution_percent = payload.contribution_percent
    if contribution_percent is None:
        contribution_percent = 0.0
        if payload.contributor:
            contributors = db_manager.get_contributors_for_project(project_id)
            target = payload.contributor.lower()
            for c in contributors:
                if (c.name and c.name.lower() == target) or (
                    c.contributor_identifier and c.contributor_identifier.lower() == target
                ):
                    contribution_percent = c.contribution_percent or 0.0
                    break

    role = get_role_from_contribution(
        contribution_percent=contribution_percent,
        is_collaborative=is_collaborative,
        role_type=payload.role_type,
    )

    updated = db_manager.update_project(project_id, {
        "collaboration_type": collaboration_type,
        "user_contribution_percent": contribution_percent,
        "user_role": role,
    })

    return {
        "project_id": project_id,
        "project_name": updated.name,
        "collaboration_type": collaboration_type,
        "user_contribution_percent": contribution_percent,
        "user_role": role,
    }

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