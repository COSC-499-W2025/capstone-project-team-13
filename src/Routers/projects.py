from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/upload")
def upload_project(file: UploadFile = File(...)):
    return {"message": "Project uploaded"}

@router.get("")
def get_projects():
    return {"projects": []}

@router.get("/{id}")
def get_project(id: int):
    return {"project_id": id}
