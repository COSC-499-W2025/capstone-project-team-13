import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.AI.ai_service import get_ai_service, AIService
    from src.Databases.database import db_manager
except ImportError:
    try:
        from AI.ai_service import get_ai_service, AIService
        from Databases.database import db_manager
    except ImportError as e:
        raise ImportError(f"Cannot import AI/DB modules: {e}")


def _extract_text_from_file(file_path: str, max_chars: int = 4000) -> str:
    """Extract readable text from .txt, .md, .pdf, or .docx files."""
    p = Path(file_path)
    if not p.is_file():
        return ""
    ext = p.suffix.lower()

    try:
        if ext in {".txt", ".md", ".rst", ".tex", ".csv"}:
            return p.read_text(encoding="utf-8", errors="ignore")[:max_chars]

        if ext == ".pdf":
            try:
                import PyPDF2
                with open(p, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = []
                    for page in reader.pages:
                        pages.append(page.extract_text() or "")
                        if sum(len(t) for t in pages) >= max_chars:
                            break
                return "\n".join(pages)[:max_chars]
            except Exception as e:
                print(f"  PDF read error: {e}")
                return ""

        if ext in {".docx", ".doc"}:
            try:
                import docx
                doc = docx.Document(str(p))
                text = "\n".join(para.text for para in doc.paragraphs)
                return text[:max_chars]
            except Exception as e:
                print(f"  DOCX read error: {e}")
                return ""
    except Exception:
        pass
    return ""


class AITextProjectAnalyzer:
    """
    AI-powered analyzer for text projects (Word, PDF, plain text).
    Uses a single comprehensive prompt with real extracted content.
    """

    ANALYSIS_PROMPT = """You are analyzing a text/writing project for a portfolio. Extract meaningful insights.

Project name: {project_name}
File type: {file_type}
Word count: {word_count}
Content sample:
\"\"\"
{content}
\"\"\"

Return ONLY valid JSON (no markdown, no explanation) with exactly these fields:
{{
  "ai_description": "<2-3 sentence professional description of what this document is about, its purpose, and what makes it notable>",
  "extracted_skills": ["<skill1>", "<skill2>", "<skill3>", "<skill4>", "<skill5>"],
  "contribution_score": <number 1-10 based on length, depth, and complexity>
}}

For extracted_skills, include writing skills, subject matter expertise, document type skills, and stylistic strengths evident from the content."""

    def __init__(self):
        self.ai_service: AIService = get_ai_service()
        self.cache_dir = Path("data/ai_text_project_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, project_name: str) -> Path:
        safe = re.sub(r"[^\w]", "_", project_name.lower())[:60]
        return self.cache_dir / f"{safe}_analysis.json"

    def _load_cache(self, project_name: str) -> Optional[Dict]:
        path = self._get_cache_path(project_name)
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _save_cache(self, project_name: str, data: Dict):
        path = self._get_cache_path(project_name)
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")

    def analyze_project_complete(self, project_dict: Dict[str, Any]) -> Dict[str, Any]:
        project_name = project_dict.get("project_name") or project_dict.get("name") or "Untitled"
        print(f"🔎 Running complete analysis for: {project_name}")

        cached = self._load_cache(project_name)
        if cached:
            print(f"  ✓ Loaded from cache")
            project_dict.update(cached)
            return project_dict

        # Extract real text content from the file
        file_path = project_dict.get("file_path", "")
        content = _extract_text_from_file(file_path) if file_path else ""
        if not content:
            content = project_dict.get("ai_description", "") or "(no content available)"

        word_count = project_dict.get("word_count") or (len(content.split()) if content else 0)
        file_type = Path(file_path).suffix.lstrip(".").upper() if file_path else "document"

        prompt = self.ANALYSIS_PROMPT.format(
            project_name=project_name,
            file_type=file_type or "document",
            word_count=word_count or "unknown",
            content=content[:3500],
        )

        raw = self.ai_service.generate_text(prompt, temperature=0.4, max_tokens=700)
        if not raw:
            print("  ✗ No response from AI")
            project_dict["extracted_skills"] = []
            project_dict["ai_description"] = ""
            project_dict["contribution_score"] = 0.0
            return project_dict

        # Parse JSON response
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text.strip())
        except Exception:
            # Fallback: try to extract fields individually
            result = {}
            desc_match = re.search(r'"ai_description"\s*:\s*"([^"]+)"', raw)
            if desc_match:
                result["ai_description"] = desc_match.group(1)
            score_match = re.search(r'"contribution_score"\s*:\s*(\d+(?:\.\d+)?)', raw)
            if score_match:
                result["contribution_score"] = float(score_match.group(1))

        ai_data = {
            "ai_description": result.get("ai_description", ""),
            "extracted_skills": result.get("extracted_skills", []),
            "contribution_score": float(result.get("contribution_score", 0) or 0),
        }

        self._save_cache(project_name, ai_data)
        project_dict.update(ai_data)
        return project_dict

    # Keep batch + DB helpers
    def analyze_batch(self, project_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.analyze_project_complete(p) for p in project_list]

    def analyze_and_update_db(self, project_dict: Dict[str, Any]):
        analyzed = self.analyze_project_complete(project_dict)
        try:
            projects = db_manager.get_all_projects()
            for p in projects:
                if p.name == project_dict.get("project_name"):
                    db_manager.update_project(p.id, {
                        "ai_description": analyzed.get("ai_description"),
                        "skills": ", ".join(analyzed.get("extracted_skills", [])),
                        "contribution_score": analyzed.get("contribution_score"),
                    })
                    break
        except Exception as e:
            print(f"⚠️ Database update failed: {e}")
        return analyzed
