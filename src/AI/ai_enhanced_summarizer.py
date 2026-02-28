"""
AI-Enhanced Project Summarizer
================================
Enhances project summaries and resume bullets using the Gemini AI service.

Two bullet-generation paths:
  - generate_bullets_for_project(project, num_bullets)
      Accepts a Project ORM object. Uses the project-type-specific
      bullet generators as a base, then optionally enriches them with
      AI rewriting. Integrates with the ATS scorer and persists results
      via db_manager.  This is the primary path used by the Resume API.

  - generate_resume_bullets(project_dict, num_bullets)  [kept for backward compat]
      Accepts a plain dict (legacy summarizer pipeline).

Summarizer path:
  - summarize_projects_with_ai(projects, ...) wraps the original
    summarize_projects scorer and optionally enriches top-k results
    with AI descriptions and a portfolio narrative.
"""

import re
import sys
import os
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from src.Analysis.summarizeProjects import summarize_projects as _original_summarize
    from src.AI.ai_service import get_ai_service
    from src.Databases.database import db_manager
    from src.Resume.codeBulletGenerator import CodeBulletGenerator
    from src.Resume.mediaBulletGenerator import MediaBulletGenerator
    from src.Resume.textBulletGenerator import TextBulletGenerator
    from src.Resume.resumeAnalytics import score_all_bullets
except ImportError as e:  # pragma: no cover
    raise ImportError(f"ai_enhanced_summarizer: missing dependency – {e}") from e


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Map project type strings to their generator class *names* in this module's
# namespace. Looking up the name at call time (rather than storing the class
# directly) means unittest.mock.patch can replace the class and _get_generator
# will pick up the patched version.
_GENERATOR_MAP = {
    "code": "CodeBulletGenerator",
    "visual_media": "MediaBulletGenerator",
    "text": "TextBulletGenerator",
}


def _get_generator(project_type: str):
    """Return the matching bullet generator instance, or raise ValueError."""
    import sys
    cls_name = _GENERATOR_MAP.get(project_type)
    if cls_name is None:
        raise ValueError(
            f"No bullet generator for project type '{project_type}'. "
            f"Supported: {list(_GENERATOR_MAP)}"
        )
    # Resolve the class from this module so patches applied via
    # unittest.mock.patch are honoured at call time.
    module = sys.modules[__name__]
    cls = getattr(module, cls_name)
    return cls()


# Preamble phrases the AI sometimes outputs instead of bullets.
# Lines starting with these are skipped by the parser.
_PREAMBLE_PREFIXES = (
    "here are", "below are", "the following", "these are",
    "sure", "certainly", "of course", "i have", "i've",
    "note:", "please", "based on",
)


def _parse_bullets_from_text(text: str, expected: int) -> List[str]:
    """
    Extract bullet strings from raw AI text.

    Handles numbered lists (1. / 1) ), dash/bullet lists, and plain lines.
    Skips preamble sentences ("Here are three bullet points…") and lines
    shorter than 15 characters.
    Returns up to `expected` clean bullet strings.
    """
    bullets: List[str] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        # Strip leading list markers: "1.", "1)", "-", "•", "*"
        cleaned = re.sub(r"^\s*(?:\d+[.)\-]|[-•*])\s*", "", line).strip()
        if len(cleaned) < 15:
            continue
        # Skip preamble / meta sentences
        if cleaned.lower().startswith(_PREAMBLE_PREFIXES):
            continue
        bullets.append(cleaned)
        if len(bullets) >= expected:
            break
    return bullets


def _ai_rewrite_bullets(bullets: List[str], project_name: str, skills: List[str]) -> List[str]:
    """
    Ask the AI to rewrite/polish a list of bullets.

    The prompt is strictly formatted so the AI returns only numbered lines —
    no preamble, no explanation. Falls back to original bullets on any error.
    """
    ai = get_ai_service()
    numbered = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(bullets))
    n = len(bullets)
    prompt = (
        f"You are a resume writing assistant. Rewrite the {n} bullet points below "
        f"to be more achievement-focused and quantified where possible.\n\n"
        f"RULES:\n"
        f"- Output ONLY the {n} rewritten bullet points, numbered 1 to {n}.\n"
        f"- Do NOT include any introduction, explanation, or closing remarks.\n"
        f"- Each bullet must start with a strong past-tense action verb.\n"
        f"- Each bullet must be 10-20 words long.\n\n"
        f"Project: {project_name}\n"
        f"Technologies: {', '.join(skills[:6])}\n\n"
        f"Original bullets:\n{numbered}\n\n"
        f"Rewritten bullets (numbered list only):"
    )
    try:
        response = ai.generate_text(prompt, temperature=0.4, max_tokens=400)
        if response:
            rewritten = _parse_bullets_from_text(response, n)
            if len(rewritten) == n:
                return rewritten
            # Count mismatch — AI didn't return the right number of bullets.
            # Fall through to the safe fallback below.
    except Exception as exc:  # pragma: no cover
        print(f"⚠️  AI rewrite failed for '{project_name}': {exc}")
    return bullets  # safe fallback


def _get_cached_ai_description(project_name: str) -> Optional[str]:
    """Return a cached AI description from the database, if available."""
    try:
        for p in db_manager.get_all_projects():
            if p.name == project_name:
                desc = getattr(p, "ai_description", None)
                if desc:
                    return desc
    except Exception:
        pass
    return None


def _cache_ai_description(project_name: str, description: str) -> None:
    """Persist an AI description to the matching database project."""
    try:
        for p in db_manager.get_all_projects():
            if p.name == project_name:
                db_manager.update_project(p.id, {"ai_description": description})
                break
    except Exception as exc:  # pragma: no cover
        print(f"⚠️  Cache write warning: {exc}")


# ---------------------------------------------------------------------------
# Primary public API: ORM-based bullet generation
# ---------------------------------------------------------------------------

def generate_bullets_for_project(
    project,
    num_bullets: int = 3,
    use_ai: bool = True,
    persist: bool = True,
) -> Dict[str, Any]:
    """
    Generate resume bullets for a Project ORM object.

    Steps:
      1. Use the project-type-specific generator to produce base bullets.
      2. Optionally rewrite them with AI for richer language.
      3. Score with the ATS scorer.
      4. Optionally persist to the database.

    Args:
        project:     A Project ORM instance (must have .id, .name,
                     .project_type, .skills, etc.)
        num_bullets: Number of bullets to generate (2–5).
        use_ai:      Whether to AI-rewrite the base bullets.
        persist:     Whether to save results via db_manager.

    Returns:
        {
            "success": bool,
            "project_id": int,
            "project_name": str,
            "header": str,
            "bullets": List[str],
            "ats_score": float,
            "ai_enhanced": bool,
            "error": str   # only present on failure
        }
    """
    if num_bullets < 2 or num_bullets > 5:
        return {"success": False, "error": "num_bullets must be between 2 and 5"}

    try:
        generator = _get_generator(project.project_type)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    try:
        bullets: List[str] = generator.generate_resume_bullets(project, num_bullets)
        header: str = generator.generate_project_header(project)
    except Exception as exc:
        return {"success": False, "error": f"Base generation failed: {exc}"}

    ai_enhanced = False
    if use_ai:
        skills = getattr(project, "skills", []) or []
        rewritten = _ai_rewrite_bullets(bullets, project.name, skills)
        if rewritten != bullets:
            bullets = rewritten
            ai_enhanced = True

    scoring = score_all_bullets(bullets, project.project_type)
    ats_score: float = scoring.get("overall_score", 0.0)

    if persist:
        db_manager.save_resume_bullets(
            project_id=project.id,
            bullets=bullets,
            header=header,
            ats_score=ats_score,
        )

    return {
        "success": True,
        "project_id": project.id,
        "project_name": project.name,
        "header": header,
        "bullets": bullets,
        "ats_score": ats_score,
        "ai_enhanced": ai_enhanced,
    }


# ---------------------------------------------------------------------------
# Legacy API: dict-based bullet generation (backward compat)
# ---------------------------------------------------------------------------

def generate_resume_bullets(project: Dict[str, Any], num_bullets: int = 3) -> List[str]:
    """
    Generate resume bullets from a plain project dict (legacy pipeline).

    Used by summarize_projects_with_ai demo flow. Does NOT persist to DB.
    """
    ai = get_ai_service()
    skills = project.get("skills", [])
    name = project.get("project_name", "Project")
    context = project.get("ai_description", "")

    prompt = (
        f"Generate exactly {num_bullets} resume bullet points for this project.\n"
        f"Start each with a number and period (1. 2. 3.).\n\n"
        f"Project: {name}\n"
        f"Technologies: {', '.join(skills[:6])}\n"
        f"Context: {context}\n\n"
        f"Resume Bullets:"
    )
    try:
        response = ai.generate_text(prompt, temperature=0.6, max_tokens=250)
        if response:
            parsed = _parse_bullets_from_text(response, num_bullets)
            if parsed:
                return parsed[:num_bullets]
    except Exception as exc:
        print(f"⚠️  Resume bullet generation failed: {exc}")

    # Fallback
    fallback_skills = ", ".join(skills[:3]) or "various technologies"
    return [
        f"Developed {name} using {fallback_skills}",
        f"Implemented core features for {name}",
        f"Contributed to {name} project development",
    ][:num_bullets]


# ---------------------------------------------------------------------------
# AI project description enrichment
# ---------------------------------------------------------------------------

def ai_enhance_project_summary(
    project_dict: Dict[str, Any],
    ai_service=None,
    include_technical_depth: bool = False,
) -> Dict[str, Any]:
    """
    Enrich a project dict in-place with an AI-generated description.

    Args:
        project_dict:            Dict with at least 'project_name' and 'skills'.
        ai_service:              Optional pre-initialised AIService instance.
        include_technical_depth: If True, also add 'technical_insights'.

    Returns:
        The same dict, now containing 'ai_description' (and optionally
        'technical_insights').
    """
    if ai_service is None:
        ai_service = get_ai_service()

    name = project_dict.get("project_name", "Unnamed Project")
    skills_str = ", ".join(project_dict.get("skills", [])[:5])
    prompt = (
        f"Write a 2-3 sentence professional description for this project "
        f"suitable for a portfolio or resume.\n"
        f"Focus on purpose, key technologies, and complexity/scope.\n\n"
        f"Project: {name}\n"
        f"Technologies: {skills_str}\n"
        f"Scope: {project_dict.get('file_count', '?')} files, "
        f"{project_dict.get('lines_of_code', '?')} lines\n\n"
        f"Description:"
    )
    try:
        description = ai_service.generate_text(prompt, temperature=0.7, max_tokens=150)
        if description:
            project_dict["ai_description"] = description.strip()
    except Exception as exc:
        print(f"⚠️  AI enhancement failed for '{name}': {exc}")
        project_dict["ai_description"] = (
            f"A {', '.join(project_dict.get('skills', ['software'])[:2])} project."
        )

    if include_technical_depth:
        tech_prompt = (
            f"Briefly identify key technical concepts in this project (1-2 sentences).\n"
            f"Look for OOP, data structures, algorithms, design patterns.\n\n"
            f"Project: {name}\nTechnologies: {skills_str}\n\nTechnical Concepts:"
        )
        try:
            tech = ai_service.generate_text(tech_prompt, temperature=0.3, max_tokens=100)
            if tech:
                project_dict["technical_insights"] = tech.strip()
        except Exception:
            pass

    return project_dict


# ---------------------------------------------------------------------------
# Portfolio-level summariser
# ---------------------------------------------------------------------------

def summarize_projects_with_ai(
    projects: List[Dict[str, Any]],
    top_k: int = 3,
    use_ai: bool = True,
    enhance_all: bool = False,
    include_technical_depth: bool = False,
    weights: Optional[Dict[str, float]] = None,
    diversity_alpha: float = 0.1,
) -> Dict[str, Any]:
    """
    Rank projects with the original scorer, then optionally enrich with AI.

    Args:
        projects:                List of project dicts (legacy format).
        top_k:                   Number of top projects to surface.
        use_ai:                  Enrich with AI descriptions if True.
        enhance_all:             Enhance every project, not just top-k.
        include_technical_depth: Add 'technical_insights' to each project.
        weights:                 Scorer weight overrides.
        diversity_alpha:         Diversity factor for the scorer.

    Returns:
        Scored summary dict, optionally with 'ai_summary' and per-project
        'ai_description' / 'technical_insights' fields.
    """
    result = _original_summarize(
        projects=projects,
        top_k=top_k,
        weights=weights,
        diversity_alpha=diversity_alpha,
    )

    if not use_ai:
        return result

    ai_service = get_ai_service()
    pool = result["all_projects_scored"] if enhance_all else result["selected_projects"]

    for project in pool:
        name = project.get("project_name", "")
        cached = _get_cached_ai_description(name)
        if cached:
            project["ai_description"] = cached
        else:
            ai_enhance_project_summary(project, ai_service, include_technical_depth)
            if "ai_description" in project:
                _cache_ai_description(name, project["ai_description"])

    # Portfolio-level narrative
    top = result["selected_projects"]
    summaries = "\n".join(
        f"- {p['project_name']}: {p.get('ai_description', ', '.join(p.get('skills', [])[:3]))}"
        for p in top
    )
    all_skills = ", ".join(result.get("unique_skills", [])[:15])
    portfolio_prompt = (
        f"Create a professional 3-4 sentence portfolio summary based on these projects.\n"
        f"Write in third person. Focus on breadth of skills and technical capability.\n\n"
        f"Projects:\n{summaries}\n\nAll Skills: {all_skills}\n\nPortfolio Summary:"
    )
    try:
        narrative = ai_service.generate_text(portfolio_prompt, temperature=0.7, max_tokens=200)
        if narrative:
            result["ai_summary"] = narrative.strip()
    except Exception:
        result["ai_summary"] = result.get("summary", "")

    return result