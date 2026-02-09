from fastapi import APIRouter

router = APIRouter(tags=["Meta"])

@router.post("/privacy-consent")
def privacy_consent():
    return {"consent": "recorded"}

@router.get("/skills")
def get_skills():
    return {"skills": []}
