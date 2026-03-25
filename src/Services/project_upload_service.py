# src/services/project_upload_service.py

from pathlib import Path
from datetime import datetime, timezone
import os

from src.Helpers.fileDataCheck import sniff_supertype
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Analysis.multiProjectZip import identifyProjectType
from src.Databases.database import db_manager


def _resolve_supertype(path: str) -> str:
    """
    Return 'code', 'text', or 'media' for the given path.

    For directories, sniff_supertype() tries to open() the path as a file,
    which always fails and falls back to 'media'. Instead, use
    identifyProjectType() which walks the directory and counts file types.
    """
    if os.path.isdir(path):
        info = identifyProjectType(path)
        # identifyProjectType returns 'code', 'media', 'text', 'mixed', or 'unknown'
        ptype = info.get("type", "unknown")
        if ptype in ("code", "mixed"):   # mixed projects contain code — use coding scanner
            return "code"
        if ptype == "text":
            return "text"
        if ptype == "media":
            return "media"
        # unknown or no recognised files — fall back to coding scanner so the
        # user at least gets a project entry rather than a hard error
        return "code"
    return sniff_supertype(path)


def process_uploaded_path(path: str):
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

    supertype = _resolve_supertype(path)
    if supertype == "code":
        project_id = scan_coding_project(path)
    elif supertype == "text":
        project_id = scan_text_document(path, single_file=True)
    elif supertype == "media":
        project_id = scan_media_project(path)
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
