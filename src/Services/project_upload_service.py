# src/services/project_upload_service.py

from pathlib import Path
from datetime import datetime, timezone
import os

from src.Helpers.fileDataCheck import sniff_supertype
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Databases.database import db_manager


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

    supertype = sniff_supertype(path)

    if supertype == "code":
        project_id = scan_coding_project(path)
    elif supertype == "text":
        project_id = scan_text_document(path, single_file=True)
    elif supertype == "media":
        project_id = scan_media_project(path)
    else:
        raise ValueError("Unsupported project type")

    project = db_manager.get_project(project_id)

    return {
        "status": "created",
        "project_id": project.id,
        "project_name": project.name,
        "project_type": project.project_type,
        "file_count": project.file_count
    }
