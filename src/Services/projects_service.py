# src/services/project_upload_service.py

from importlib.resources import path
from pathlib import Path
from datetime import datetime, timezone
import os

from typing import Optional

from src.Helpers.fileDataCheck import sniff_supertype
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Databases.database import db_manager


def process_uploaded_path(path: str, user_id: Optional[int] = None):
    """
    Core logic used by BOTH:
    - CLI (old main.py)
    - FastAPI (new endpoints)
    """

    path = os.path.abspath(path)

    # Avoid duplicates
    existing = db_manager.get_project_by_path(path)
    if existing:
        return {
            "status": "exists",
            "project_id": existing.id,
            "project_name": existing.name
        }

    supertype = sniff_supertype(path)
    if supertype == "code":
        project_id = scan_coding_project(path, user_id=user_id)
    elif supertype == "text":
        project_id = scan_text_document(path, single_file=True, user_id=user_id)
    elif supertype == "media":
        project_id = scan_media_project(path, user_id=user_id)
    else:
        raise ValueError("Unsupported project type")

    if not project_id:
        return {
            "status": "skipped",
            "reason": "No supported files found in uploaded path"
        }
    project = db_manager.get_project(project_id)

    return {
        "status": "created",
        "project_id": project.id,
        "project_name": project.name,
        "project_type": project.project_type,
        "file_count": project.file_count
    }

VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}

def upload_project_thumbnail(project_id: int, thumbnail_path: str, user_id: Optional[int] = None) -> Optional[dict]:
    """
    Update a project's thumbnail path.
    Raises ValueError for invalid image format, PermissionError if user doesn't own the project.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None

    # Check ownership
    if user_id is not None and project.user_id != user_id:
        raise PermissionError("You don't have permission to edit this project")

    file_ext = os.path.splitext(thumbnail_path)[1].lower()
    if file_ext not in VALID_IMAGE_EXTENSIONS:
        raise ValueError(f"Invalid image format '{file_ext}'. Supported: {', '.join(VALID_IMAGE_EXTENSIONS)}")

    db_manager.update_project(project_id, {'thumbnail_path': thumbnail_path})

    updated = db_manager.get_project(project_id)
    return updated.to_dict()