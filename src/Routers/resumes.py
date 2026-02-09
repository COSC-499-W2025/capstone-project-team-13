from fastapi import APIRouter

router = APIRouter(prefix="/resume", tags=["Resume"])

@router.get("/{id}")
def get_resume(id: int):
    return {"resume_id": id}

@router.post("/generate")
def generate_resume():
    return {"message": "Resume generated"}

@router.post("/{id}/edit")
def edit_resume(id: int):
    return {"message": f"Resume {id} updated"}
