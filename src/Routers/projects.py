from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import zipfile
import shutil

from src.Services.project_upload_service import process_uploaded_path

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

