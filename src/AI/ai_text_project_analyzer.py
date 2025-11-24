import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.AI.ai_service import get_ai_service, AIService
    from src.Databases.database import db_manager
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    sys.exit(1)


class AITextProjectAnalyzer:
    """
    AI-powered analyzer for text projects (Word, PDF, plain text),
    following the same structure + naming style as the coding project analyzer.

    Produces:
    - extracted_skills (includes writing insights)
    - ai_description (2–3 sentences)
    - contribution_score (numeric 1–10)

    Supports:
    - caching
    - single-project analysis
    - batch analysis
    - database update logic
    - CLI entrypoint
    """

    DESCRIPTION_PROMPT = """
    Write a concise, professional 2–3 sentence description for this text-based project.
    Highlight its purpose, key topics, depth, and any notable writing attributes.

    Project name: {project_name}
    Word count: {word_count}
    File type: {file_type}
    Skills/Insights: {skills}

    Description:
    """

    SKILLS_PROMPT = """
    Analyze the following text project and extract the main writing/author skills,
    topics, and structural or stylistic strengths.

    Return them as a comma-separated list.

    Project: {project_name}
    Content sample: {content}

    Skills:
    """

    CONTRIBUTION_PROMPT = """
    Estimate the contributor's effort level for this text project (1–10 scale).
    Base this on word count, depth, and writing complexity.

    Project name: {project_name}
    Word count: {word_count}
    Skills: {skills}

    Score:
    """

    def __init__(self):
        self.ai_service: AIService = get_ai_service()
        self.cache_dir = Path("data/ai_text_project_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hits = 0

    # ----------- CACHE HELPERS -------------------

    def _get_cache_path(self, project_name: str, key: str) -> Path:
        safe = project_name.replace(" ", "_").lower()
        return self.cache_dir / f"{safe}_{key}.json"

    def _load_cache(self, project_name: str, key: str) -> Optional[Any]:
        path = self._get_cache_path(project_name, key)
        if path.exists():
            try:
                with open(path, "r") as f:
                    self.cache_hits += 1
                    return json.load(f)
            except Exception:
                return None
        return None

    def _save_cache(self, project_name: str, key: str, data: Any):
        path = self._get_cache_path(project_name, key)
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")


    # ----------- SKILLS EXTRACTION ---------------

    def extract_skills(self, project_dict: Dict[str, Any]) -> List[str]:
        project_name = project_dict["project_name"]
        cached = self._load_cache(project_name, "skills")

        if cached:
            return cached["skills"]

        prompt = self.SKILLS_PROMPT.format(
            project_name=project_name,
            content=project_dict.get("content", "")[:2000]
        )

        result = self.ai_service.generate_text(prompt, temperature=0.2, max_tokens=150)
        skills = [x.strip() for x in result.split(",") if x.strip()]

        self._save_cache(project_name, "skills", {"skills": skills})
        return skills


    # ----------- DESCRIPTION GENERATION ----------


    def generate_description(self, project_dict: Dict[str, Any], skills: List[str]) -> str:
        project_name = project_dict["project_name"]
        cached = self._load_cache(project_name, "description")

        if cached:
            return cached["description"]

        prompt = self.DESCRIPTION_PROMPT.format(
            project_name=project_name,
            word_count=project_dict.get("word_count", "Unknown"),
            file_type=project_dict.get("file_type", "Unknown"),
            skills=", ".join(skills[:6])
        )

        description = self.ai_service.generate_text(prompt, temperature=0.6, max_tokens=180).strip()

        self._save_cache(project_name, "description", {"description": description})
        return description


    # ----------- CONTRIBUTION ESTIMATION ---------
   

    def estimate_contribution(self, project_dict: Dict[str, Any], skills: List[str]) -> float:
        project_name = project_dict["project_name"]
        cached = self._load_cache(project_name, "contribution")

        if cached:
            return cached["score"]

        prompt = self.CONTRIBUTION_PROMPT.format(
            project_name=project_name,
            word_count=project_dict.get("word_count", "Unknown"),
            skills=", ".join(skills[:5])
        )

        raw = self.ai_service.generate_text(prompt, temperature=0.0, max_tokens=20)

        import re
        match = re.search(r"\d+(\.\d+)?", raw)
        score = float(match.group(0)) if match else 0.0

        self._save_cache(project_name, "contribution", {"score": score})
        return score


    # ----------- COMPLETE ANALYSIS ---------------


    def analyze_project_complete(self, project_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mirrors the coding analyzer: extract skills, description, and score.
        """
        project_name = project_dict.get("project_name", "Unnamed Text Project")
        print(f"🔎 Running complete analysis for: {project_name}")

        # Skills
        skills = self.extract_skills(project_dict)
        project_dict["extracted_skills"] = skills

        # Description
        description = self.generate_description(project_dict, skills)
        project_dict["ai_description"] = description

        # Contribution score
        score = self.estimate_contribution(project_dict, skills)
        project_dict["contribution_score"] = score

        return project_dict

    # ----------- BATCH ANALYSIS ------------------

    def analyze_batch(self, project_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mirrors coding analyzer batch processing.
        """
        results = []
        for proj in project_list:
            results.append(self.analyze_project_complete(proj))
        return results

    # ----------- DATABASE UPDATE -----------------

    def analyze_and_update_db(self, project_dict: Dict[str, Any]):
        """
        Matches coding analyzer behavior:
        - Analyze
        - Save into DB's project row (if exists)
        """
        analyzed = self.analyze_project_complete(project_dict)

        # Try to update DB if project exists
        try:
            projects = db_manager.get_all_projects()
            for p in projects:
                if p.name == project_dict["project_name"]:
                    update_data = {
                        "ai_description": analyzed.get("ai_description"),
                        "skills": ", ".join(analyzed.get("extracted_skills", [])),
                        "contribution_score": analyzed.get("contribution_score")
                    }
                    db_manager.update_project(p.id, update_data)
                    print(f"💾 Updated DB entry for project '{p.name}'")
                    break
        except Exception as e:
            print(f"⚠️ Database update failed: {e}")

        return analyzed


# --------------------- CLI ENTRY --------------------------

def analyze_text_project_cli():
    print(" TEXT PROJECT ANALYZER (AI)")
    project_name = input("Project name: ").strip()
    content = input("Paste project text content: ").strip()

    analyzer = AITextProjectAnalyzer()
    word_count = len(content.split())

    project = {
        "project_name": project_name,
        "content": content,
        "word_count": word_count,
        "file_type": "text"
    }

    result = analyzer.analyze_project_complete(project)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    analyze_text_project_cli()
