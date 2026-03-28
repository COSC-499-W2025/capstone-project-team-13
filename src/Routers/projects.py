from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
import uuid
import zipfile
import json

from src.Databases.database import db_manager
from src.Services.projects_service import process_uploaded_path, upload_project_thumbnail
from src.Services.auth_service import get_current_user_id, require_auth
from src.UserPrompts.config_integration import has_ai_consent, has_basic_consent

router = APIRouter(prefix="/projects", tags=["Projects"])

UPLOAD_DIR = Path("evidence/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Guest analyze (no account required, no data saved) ────────────────────────

@router.post("/guest-analyze")
async def guest_analyze(file: UploadFile = File(...)):
    """Analyze a file for a guest user. Results are returned immediately and NOT saved to the database."""
    display_name = Path(file.filename).stem  # capture clean name before UUID rename
    uid = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"guest_{uid}_{file.filename}"

    with open(upload_path, "wb") as f:
        f.write(await file.read())

    if upload_path.suffix.lower() == ".zip":
        extract_dir = UPLOAD_DIR / f"guest_{uid}"
        extract_dir.mkdir()
        with zipfile.ZipFile(upload_path, 'r') as zf:
            zf.extractall(extract_dir)
        process_path = extract_dir
    else:
        process_path = upload_path

    try:
        result = process_uploaded_path(str(process_path), user_id=None)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        # Clean up temp files regardless of outcome
        import shutil
        if upload_path.exists():
            upload_path.unlink(missing_ok=True)
        if upload_path.suffix.lower() == ".zip" and (UPLOAD_DIR / f"guest_{uid}").exists():
            shutil.rmtree(UPLOAD_DIR / f"guest_{uid}", ignore_errors=True)

    # If a project was created, read its data then immediately delete it
    project_id = result.get("project_id")
    if project_id:
        project = db_manager.get_project(project_id)
        analysis = {
            "status": "analyzed",
            "name": display_name,
            "project_type": project.project_type if project else result.get("project_type"),
            "file_count": project.file_count if project else result.get("file_count", 0),
            "lines_of_code": project.lines_of_code if project else 0,
            "languages": project.languages if project else [],
            "frameworks": project.frameworks if project else [],
            "skills": project.skills if project else [],
            "description": (project.description or project.ai_description or "") if project else "",
            "importance_score": round(project.importance_score or 0, 2) if project else 0,
        }
        db_manager.delete_project(project_id)
        return analysis

    return {"status": result.get("status", "skipped"), "detail": result.get("reason", "No supported files found")}


# ── Request models ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    analysis_type: Optional[str] = "overview"

class RankRequest(BaseModel):
    target_skills: Optional[List[str]] = None
    top_k: Optional[int] = 3

class BatchAnalyzeRequest(BaseModel):
    analysis_types: Optional[List[str]] = ["overview"]


# ── Helper: display name (prefer custom_description over UUID name) ────────────

def _display_name(project) -> str:
    """Return the best human-readable name for a project."""
    cd = (project.custom_description or "").strip()
    if cd:
        return cd
    name = (project.name or "").strip()
    # If name looks like a UUID (contains multiple hyphens and is long), use description or type
    import re
    if re.match(r'^[0-9a-f-]{30,}', name, re.IGNORECASE):
        return project.description or project.ai_description or f"{project.project_type or 'Project'} {project.id}"
    return name


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_project(
    file: UploadFile = File(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Upload and scan a project file or ZIP archive."""
    if not has_basic_consent():
        raise HTTPException(
            status_code=403,
            detail="File access requires consent. Please grant file access in the Upload page."
        )

    original_stem = Path(file.filename).stem  # capture before UUID rename
    uid = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"{uid}_{file.filename}"

    with open(upload_path, "wb") as f:
        f.write(await file.read())

    if upload_path.suffix.lower() == ".zip":
        extract_dir = UPLOAD_DIR / uid
        extract_dir.mkdir()
        with zipfile.ZipFile(upload_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        process_path = extract_dir
    else:
        process_path = upload_path

    result = process_uploaded_path(str(process_path), user_id=user_id)

    # Store original filename as custom_description so we never show UUIDs
    if isinstance(result, dict) and result.get("project_id"):
        pid = result["project_id"]
        proj = db_manager.get_project(pid)
        if proj and not proj.custom_description:
            db_manager.update_project(pid, {"custom_description": original_stem})

    return result


# ── Incremental upload to existing project ─────────────────────────────────────

@router.post("/{project_id}/upload")
async def incremental_upload(
    project_id: int,
    file: UploadFile = File(...),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Add files from a ZIP to an existing project (incremental update)."""
    if not has_basic_consent():
        raise HTTPException(
            status_code=403,
            detail="File access requires consent. Please grant file access in the Upload page."
        )

    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user_id is not None and project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your project")

    uid = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"inc_{uid}_{file.filename}"
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    try:
        from src.Analysis.incrementalZipHandler import IncrementalZipHandler
        handler = IncrementalZipHandler()
        result = handler.add_zip_to_existing_project(project_id, str(upload_path))
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Incremental upload failed"))

        # --- Populate Git contributors for this project ---
        try:
            from src.Helpers.gitContributorExtraction import populate_contributors_for_project
            # Refresh project object in case path changed
            project = db_manager.get_project(project_id)
            if project:
                populate_contributors_for_project(project)
        except Exception as e:
            # Log but do not fail the upload if contributor extraction fails
            print(f"[WARN] Failed to populate Git contributors: {e}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incremental upload failed: {str(e)}")


# ── List / Get ─────────────────────────────────────────────────────────────────

@router.get("")
def list_projects(user_id: Optional[int] = Depends(get_current_user_id)):
    """Get all projects for the current user (or guest projects)."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()
    result = []
    for p in projects:
        d = p.to_dict()
        d["display_name"] = _display_name(p)
        result.append(d)
    return result


@router.get("/timeline")
def get_timeline(user_id: Optional[int] = Depends(get_current_user_id)):
    """Return all projects sorted chronologically."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id, include_hidden=True)
    else:
        projects = db_manager.get_guest_projects(include_hidden=True)
    projects_sorted = sorted(
        projects,
        key=lambda p: p.date_created or p.date_scanned or p.created_at,
    )
    return [
        {
            "id": p.id,
            "name": _display_name(p),
            "project_type": p.project_type,
            "date_created": p.date_created.isoformat() if p.date_created else None,
            "date_modified": p.date_modified.isoformat() if p.date_modified else None,
            "date_scanned": p.date_scanned.isoformat() if p.date_scanned else None,
            "importance_score": p.importance_score,
        }
        for p in projects_sorted
    ]


@router.get("/shared-files")
def shared_files_report(user_id: Optional[int] = Depends(get_current_user_id)):
    """Return projects that share files with other projects."""
    try:
        from src.deletion_manager import DeletionManager
        manager = DeletionManager()
        if user_id:
            projects = db_manager.get_projects_for_user(user_id, include_hidden=True)
        else:
            projects = db_manager.get_guest_projects(include_hidden=True)
        report = []
        for p in projects:
            shared = manager.get_shared_files(p.id)
            if shared:
                report.append({
                    "project_id": p.id,
                    "project_name": _display_name(p),
                    "shared_files": shared,
                })
        return report
    except ImportError:
        return []


@router.get("/cache-stats")
def cache_stats():
    """Return AI cache statistics."""
    try:
        from src.deletion_manager import DeletionManager
        manager = DeletionManager()
        return manager.get_cache_statistics()
    except Exception:
        return {"total_cache_files": 0, "total_cache_size_bytes": 0}


@router.get("/{project_id}")
def get_project(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Get a single project by ID."""
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to access this project")
    d = project.to_dict(include_counts=True)
    d["display_name"] = _display_name(project)
    return d


# ── Delete ─────────────────────────────────────────────────────────────────────

@router.delete("/ai-insights/all")
def delete_all_ai_insights(user_id: Optional[int] = Depends(get_current_user_id)):
    """Delete ALL AI insights for all projects."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id, include_hidden=True)
    else:
        projects = db_manager.get_guest_projects(include_hidden=True)
    for p in projects:
        db_manager.update_project(p.id, {"ai_description": None, "ai_analysis": None})
    # Also clear cache files if they exist
    cache_deleted = 0
    try:
        import shutil
        from pathlib import Path
        for cache_dir in [Path("data/ai_cache"), Path("data/ai_text_project_cache"), Path("data/ai_project_analysis_cache")]:
            if cache_dir.exists():
                cache_deleted += len(list(cache_dir.glob("*.json")))
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return {"projects_updated": len(projects), "cache_files_deleted": cache_deleted}


@router.delete("/cache")
def clear_cache():
    """Clear all AI analysis cache files."""
    import shutil
    from pathlib import Path
    deleted = 0
    for cache_dir in [Path("data/ai_cache"), Path("data/ai_text_project_cache"), Path("data/ai_project_analysis_cache")]:
        if cache_dir.exists():
            count = len(list(cache_dir.glob("*.json")))
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            deleted += count
    return {"cache_files_deleted": deleted}


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Safely delete a project. Protects files shared with other projects."""
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user_id is not None and project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your project")

    try:
        from src.deletion_manager import DeletionManager
        manager = DeletionManager()
        result = manager.delete_project_safely(project_id, delete_shared_files=False)
        if not result.get("project_deleted"):
            raise HTTPException(status_code=500, detail=result.get("error", "Deletion failed"))
        return {"deleted": True, "project_id": project_id, "files_protected": result.get("files_protected", 0)}
    except ImportError:
        # Fallback: basic delete without shared-file protection
        success = db_manager.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=500, detail="Deletion failed")
        return {"deleted": True, "project_id": project_id}


# ── Thumbnail ──────────────────────────────────────────────────────────────────

@router.post("/{project_id}/thumbnail")
async def upload_thumbnail(
    project_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(require_auth)
):
    """Upload a thumbnail image for a project."""
    filename = f"thumb_{project_id}_{file.filename}"
    thumbnail_disk_path = UPLOAD_DIR / filename
    with open(thumbnail_disk_path, "wb") as f:
        f.write(await file.read())
    try:
        # Store only the filename so frontend builds: /uploads/<filename>
        result = upload_project_thumbnail(project_id, filename, user_id=user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return result


@router.delete("/{project_id}/thumbnail")
def remove_thumbnail(
    project_id: int,
    user_id: int = Depends(require_auth)
):
    """Remove the thumbnail from a project."""
    try:
        result = upload_project_thumbnail(project_id, None, user_id=user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return {"removed": True, "project_id": project_id}


# ── AI Analysis ────────────────────────────────────────────────────────────────

@router.post("/{project_id}/analyze")
def analyze_project(
    project_id: int,
    body: AnalyzeRequest = Body(default=AnalyzeRequest()),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Run AI analysis on a single project."""
    # ── Consent gate ──────────────────────────────────────────────────────────
    if not has_ai_consent():
        raise HTTPException(
            status_code=403,
            detail="AI analysis requires consent. Please enable AI features in Settings."
        )

    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user_id is not None and project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your project")

    analysis_type = body.analysis_type or "overview"

    try:
        import json as _json
        ptype = (project.project_type or "code").lower()

        if ptype == "text":
            from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer
            analyzer = AITextProjectAnalyzer()
            project_dict = {k: v for k, v in project.__dict__.items() if not k.startswith("_")}
            project_dict["project_name"] = project.name or "Unnamed Project"
            results = analyzer.analyze_project_complete(project_dict)
            updates = {}
            if results.get("ai_description"):
                updates["ai_description"] = results["ai_description"]
            if results.get("extracted_skills"):
                updates["skills"] = ", ".join(results["extracted_skills"])
            safe = {k: v for k, v in results.items() if v is not None}
            updates["ai_analysis"] = _json.dumps(safe)
        elif ptype in ("media", "image", "video", "audio"):
            from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer
            analyzer = AIMediaProjectAnalyzer()
            project_dict = {k: v for k, v in project.__dict__.items() if not k.startswith("_")}
            project_dict["project_name"] = project.name or "Unnamed Project"
            results = analyzer.analyze_project_complete(project_dict)
            updates = {}
            if results.get("ai_description"):
                updates["ai_description"] = results["ai_description"]
            safe = {k: v for k, v in results.items() if v is not None}
            updates["ai_analysis"] = _json.dumps(safe)
        else:
            from src.AI.ai_project_analyzer import AIProjectAnalyzer
            analyzer = AIProjectAnalyzer()
            results = analyzer.analyze_project_complete(project_id)
            updates = {}
            if results and "overview" in results:
                overview = results["overview"]
                if isinstance(overview, str) and overview.strip():
                    updates["ai_description"] = overview.strip()
                elif isinstance(overview, dict):
                    desc = overview.get("summary") or overview.get("description") or ""
                    if desc:
                        updates["ai_description"] = desc
            if results:
                safe = {k: v for k, v in results.items()
                        if k not in ("cache_stats",) and v is not None}
                updates["ai_analysis"] = _json.dumps(safe)

        if updates:
            db_manager.update_project(project_id, updates)
        return {"project_id": project_id, "analysis_type": analysis_type, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/batch")
def batch_analyze(
    body: BatchAnalyzeRequest = Body(default=BatchAnalyzeRequest()),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Run AI analysis on all projects."""
    # ── Consent gate ──────────────────────────────────────────────────────────
    if not has_ai_consent():
        raise HTTPException(
            status_code=403,
            detail="AI analysis requires consent. Please enable AI features in Settings."
        )

    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()

    if not projects:
        return {"analyzed": 0, "results": []}

    results = []
    import json as _json
    for p in projects:
        try:
            ptype = (p.project_type or "code").lower()
            updates = {}

            if ptype == "text":
                from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer
                analyzer = AITextProjectAnalyzer()
                project_dict = {k: v for k, v in p.__dict__.items() if not k.startswith("_")}
                project_dict["project_name"] = p.name or "Unnamed Project"
                r = analyzer.analyze_project_complete(project_dict)
                if r.get("ai_description"):
                    updates["ai_description"] = r["ai_description"]
                if r.get("extracted_skills"):
                    updates["skills"] = ", ".join(r["extracted_skills"])
            elif ptype in ("media", "image", "video", "audio"):
                from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer
                analyzer = AIMediaProjectAnalyzer()
                project_dict = {k: v for k, v in p.__dict__.items() if not k.startswith("_")}
                project_dict["project_name"] = p.name or "Unnamed Project"
                r = analyzer.analyze_project_complete(project_dict)
                if r.get("ai_description"):
                    updates["ai_description"] = r["ai_description"]
            else:
                from src.AI.ai_project_analyzer import AIProjectAnalyzer
                analyzer = AIProjectAnalyzer()
                r = analyzer.analyze_project_complete(p.id)
                if r and "overview" in r:
                    overview = r["overview"]
                    if isinstance(overview, str) and overview.strip():
                        updates["ai_description"] = overview.strip()
                    elif isinstance(overview, dict):
                        desc = overview.get("summary") or overview.get("description") or ""
                        if desc:
                            updates["ai_description"] = desc

            if updates:
                db_manager.update_project(p.id, updates)
            results.append({"project_id": p.id, "name": _display_name(p), "success": True})
        except Exception as e:
            results.append({"project_id": p.id, "name": _display_name(p), "success": False, "error": str(e)})

    return {"analyzed": len(results), "results": results}


# ── Importance Scores ──────────────────────────────────────────────────────────

@router.post("/compute-importance")
def compute_importance(user_id: Optional[int] = Depends(get_current_user_id)):
    """Compute and save importance scores for all projects."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id, include_hidden=True)
    else:
        projects = db_manager.get_guest_projects(include_hidden=True)

    if not projects:
        return {"updated": 0, "scores": []}

    try:
        from src.Analysis.importanceScores import calculate_importance_score
        scores = []
        for p in projects:
            score = calculate_importance_score(p)
            db_manager.update_project(p.id, {"importance_score": score})
            scores.append({"project_id": p.id, "name": _display_name(p), "importance_score": round(score, 4)})
        scores.sort(key=lambda x: x["importance_score"], reverse=True)
        return {"updated": len(scores), "scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


# ── AI Ranking ────────────────────────────────────────────────────────────────

@router.post("/rank")
def rank_projects(
    body: RankRequest = Body(default=RankRequest()),
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """AI-powered project ranking with optional skill prioritization."""
    if user_id:
        projects = db_manager.get_projects_for_user(user_id)
    else:
        projects = db_manager.get_guest_projects()

    if not projects:
        return {"selected": [], "summary": "No projects found."}

    # Build project dicts for ranker
    project_dicts = []
    for p in projects:
        project_dicts.append({
            "project_id": p.id,
            "project_name": _display_name(p),
            "time_spent": p.file_count or 1,
            "success_score": float(p.importance_score or 0),
            "contribution_score": float(p.user_contribution_percent or 50),
            "skills": p.skills or [],
            "languages": p.languages or [],
            "project_type": p.project_type or "unknown",
            "importance_score": float(p.importance_score or 0),
        })

    try:
        from src.AI.ai_project_ranker import AIProjectRanker
        ranker = AIProjectRanker()
        result = ranker.rank(
            project_dicts,
            target_skills=body.target_skills,
            top_k=body.top_k or 3,
        )
        # Clean up internal scoring keys before returning
        for proj in result.get("selected", []):
            proj.pop("_rank_score_raw", None)
        return result
    except Exception as e:
        # Fallback: simple importance-score ranking
        sorted_projects = sorted(project_dicts, key=lambda x: x["importance_score"], reverse=True)
        top = sorted_projects[:body.top_k or 3]
        return {
            "selected": [{"project_name": p["project_name"], "project_id": p["project_id"], "_rank_score": p["importance_score"], "skills": p["skills"]} for p in top],
            "summary": f"Ranked by importance score (AI unavailable: {str(e)})",
        }


# ── AI Insights deletion ───────────────────────────────────────────────────────

@router.delete("/{project_id}/ai-insights")
def delete_ai_insights(
    project_id: int,
    user_id: Optional[int] = Depends(get_current_user_id)
):
    """Delete AI insights (description + cache) for a single project."""
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user_id is not None and project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your project")

    try:
        from src.deletion_manager import DeletionManager
        result = DeletionManager().delete_ai_insights_for_project(project_id)
        return result
    except ImportError:
        db_manager.update_project(project_id, {"ai_description": None})
        return {"success": True, "cache_deleted": 0}

@router.get("/{project_id}/contributors")
def get_project_contributors(project_id: int):
    """Return all contributors for a given project ID."""
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    contributors = db_manager.get_contributors_for_project(project_id)
    # Return as list of dicts
    return [
        {
            "name": c.name,
            "email": c.contributor_identifier,
            "commit_count": c.commit_count,
            "lines_added": c.lines_added,
            "lines_deleted": c.lines_deleted,
            "contribution_percent": c.contribution_percent,
        }
        for c in contributors
    ]