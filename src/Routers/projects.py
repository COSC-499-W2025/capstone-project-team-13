from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid

from src.Services.project_upload_service import process_uploaded_path

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_project(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    project_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{project_id}_{file.filename}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        result = process_uploaded_path(str(file_path))
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal processing error")
