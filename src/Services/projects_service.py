# src/services/project_upload_service.py

from pathlib import Path
from datetime import datetime, timezone
import os
import hashlib

from typing import Optional

from src.Helpers.fileDataCheck import sniff_supertype
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Databases.database import db_manager


def _hash_directory(path: str) -> str:
    """
    Produce a stable hash for a directory by hashing the sorted list of
    (relative_path, file_size) tuples. Fast and UUID-path-independent.
    """
    entries = []
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            try:
                rel = os.path.relpath(fpath, path)
                size = os.path.getsize(fpath)
                entries.append(f"{rel}:{size}")
            except OSError:
                pass
    digest = hashlib.sha256("\n".join(entries).encode()).hexdigest()
    return digest


def _hash_file(path: str) -> str:
    """SHA-256 of a single file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def process_uploaded_path(path: str, user_id: Optional[int] = None):
    """
    Core logic used by BOTH:
    - CLI (old main.py)
    - FastAPI (new endpoints)
    """

    path = os.path.abspath(path)

    # -- Duplicate detection ---------------------------------------------------
    # 1. Exact path match (fast, catches re-uploads of same extracted folder)
    existing = db_manager.get_project_by_path(path)
    if existing:
        return {
            "status": "exists",
            "project_id": existing.id,
            "project_name": existing.name,
        }

    # 2. Content hash match (catches same zip uploaded under a new UUID filename)
    try:
        if os.path.isdir(path):
            content_hash = _hash_directory(path)
        else:
            content_hash = _hash_file(path)

        existing_by_hash = db_manager.get_project_by_content_hash(content_hash)
        if existing_by_hash:
            return {
                "status": "exists",
                "project_id": existing_by_hash.id,
                "project_name": existing_by_hash.name,
            }
    except Exception:
        content_hash = None  # non-fatal -- proceed with upload

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
            "reason": "No supported files found in uploaded path",
        }

    project = db_manager.get_project(project_id)

    # Store content hash on the new project so future uploads can match it
    if content_hash:
        try:
            db_manager.update_project(project_id, {"content_hash": content_hash})
        except Exception:
            pass  # column may not exist yet -- non-fatal

    return {
        "status": "created",
        "project_id": project.id,
        "project_name": project.name,
        "project_type": project.project_type,
        "file_count": project.file_count,
    }


VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}


def upload_project_thumbnail(
    project_id: int, thumbnail_path: str, user_id: Optional[int] = None
) -> Optional[dict]:
    """
    Update a project's thumbnail path.
    Raises ValueError for invalid image format, PermissionError if user doesn't own the project.
    Pass thumbnail_path=None to remove the thumbnail.
    """
    project = db_manager.get_project(project_id)
    if not project:
        return None

    if user_id is not None and project.user_id != user_id:
        raise PermissionError("You don't have permission to edit this project")

    if thumbnail_path is not None:
        file_ext = os.path.splitext(thumbnail_path)[1].lower()
        if file_ext not in VALID_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Invalid image format '{file_ext}'. Supported: {', '.join(VALID_IMAGE_EXTENSIONS)}"
            )

    db_manager.update_project(project_id, {"thumbnail_path": thumbnail_path})

    updated = db_manager.get_project(project_id)
    return updated.to_dict()