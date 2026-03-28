from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.Helpers import gitContributorExtraction

router = APIRouter(prefix="/contributors", tags=["Contributors"])

@router.post("/populate/all")
def populate_all_contributors(
    since_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    until_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    try:
        gitContributorExtraction.populate_all_projects(since_date, until_date)
        return {"success": True, "message": "Contributors populated for all projects."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/populate/project")
def populate_project_contributors(
    project_name: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    since_date: Optional[str] = Query(None),
    until_date: Optional[str] = Query(None)
):
    if not project_name and not project_id:
        raise HTTPException(status_code=400, detail="Must provide project_name or project_id.")
    try:
        gitContributorExtraction.populate_specific_project(project_name, project_id, since_date, until_date)
        return {"success": True, "message": "Contributors populated for project."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verify-git-stats")
def verify_git_stats(
    project_path: str = Query(..., description="Path to the Git repository"),
    since_date: Optional[str] = Query(None),
    until_date: Optional[str] = Query(None)
):
    try:
        gitContributorExtraction.verify_git_stats(project_path, since_date, until_date)
        return {"success": True, "message": "Git stats verified. See server logs for details."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
