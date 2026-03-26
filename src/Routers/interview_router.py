from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src.Services.auth_service import require_auth
from src.Databases.database import db_manager
from src.AI.ai_service import get_ai_service
import json
import re

router = APIRouter(prefix="/interview", tags=["Interview"])


class InterviewRequest(BaseModel):
    target_role: Optional[str] = "Software Engineer"
    project_ids: Optional[List[int]] = None   # None = use all projects


class STARAnswer(BaseModel):
    question: str
    situation: str
    task: str
    action: str
    result: str
    project_name: str
    project_type: str


@router.post("/generate")
def generate_interview_answers(
    body: InterviewRequest,
    user_id: int = Depends(require_auth)
):
    # Fetch user projects
    all_projects = db_manager.get_projects_for_user(user_id)
    if not all_projects:
        raise HTTPException(status_code=404, detail="No projects found. Upload some projects first.")

    # Filter to selected projects if specified
    if body.project_ids:
        projects = [p for p in all_projects if p.id in body.project_ids][:5]
    else:
        projects = all_projects[:5]   # cap at 5 to keep prompt reasonable

    if not projects:
        raise HTTPException(status_code=404, detail="No matching projects found.")

    # Build project summaries for the prompt
    project_summaries = []
    for p in projects:
        desc = (p.ai_description or p.description or "")[:300]
        # Match frontend projectName() priority: display_name > custom_description > name (skip UUIDs)
        raw_name = (p.name or "").strip()
        if re.match(r'^[0-9a-f-]{30,}$', raw_name, re.IGNORECASE):
            raw_name = ""
        display = (getattr(p, "display_name", None) or getattr(p, "custom_description", None) or "").strip()
        best_name = display or raw_name or (p.ai_description or "")[:40] or "Untitled"
        summary = {
            "name": best_name,
            "type": p.project_type or "general",
            "description": desc,
            "role": (p.user_role or "")[:100],
            "evidence": (p.success_evidence or "")[:200],
            "skills": [],
            "metrics": {},
        }
        # Add skills/tech from ai_analysis if available
        if p.ai_analysis:
            try:
                analysis = json.loads(p.ai_analysis) if isinstance(p.ai_analysis, str) else p.ai_analysis
                summary["skills"] = analysis.get("tech_stack", []) or analysis.get("languages", [])
            except Exception:
                pass
        # Add metrics
        if hasattr(p, "lines_of_code") and p.lines_of_code:
            summary["metrics"]["loc"] = p.lines_of_code
        if hasattr(p, "file_count") and p.file_count:
            summary["metrics"]["files"] = p.file_count

        project_summaries.append(summary)

    # Build prompt
    project_text = "\n\n".join([
        f"Project: {s['name']}\n"
        f"Type: {s['type']}\n"
        f"Description: {s['description'] or 'N/A'}\n"
        f"My role: {s['role'] or 'contributor'}\n"
        f"Evidence/outcome: {s['evidence'] or 'N/A'}\n"
        f"Skills/tech: {', '.join(s['skills']) if s['skills'] else 'N/A'}\n"
        f"Metrics: {s['metrics'] if s['metrics'] else 'N/A'}"
        for s in project_summaries
    ])

    prompt = f"""You are a professional career coach preparing a candidate for behavioral interviews.

Target role: {body.target_role}

Here are the candidate's projects:

{project_text}

Generate exactly 4 behavioral interview questions and STAR-format answers using ONLY the project details above.
Adapt your language to the project type — for code projects use technical language, for media/creative projects use production/creative language, for research/writing use academic language.
Keep each STAR section concise (2-3 sentences max).

Return ONLY a valid JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "question": "Tell me about a time you ...",
    "situation": "...",
    "task": "...",
    "action": "...",
    "result": "...",
    "project_name": "...",
    "project_type": "..."
  }}
]

Cover these 4 themes (one each):
1. A challenging technical or creative problem you solved
2. A project you are most proud of
3. A time you took initiative or led something
4. A time you had to learn something new quickly

Use specific details and outcomes from the projects. Do not invent details not present above."""

    ai = get_ai_service()
    raw = ai.generate_text(prompt, temperature=0.7)

    # Parse JSON from response
    try:
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        answers = json.loads(text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")

    return {"answers": answers, "target_role": body.target_role}
