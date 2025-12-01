import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.AI.ai_service import get_ai_service, AIService
    from src.Databases.database import db_manager
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    sys.exit(1)


class AIMediaProjectAnalyzer:
    
    """
    AI-powered analyzer for DIGITAL VISUAL MEDIA projects.
    Mirrors the structure of AITextProjectAnalyzer.

    Supports:
    - video, graphics, images, illustrations, motion graphics, UI mockups
    - skills extraction (visual + technical)
    - description generation
    - contribution score estimation
    - caching
    - batch analysis
    - database update
    """

    # ---------- PROMPTS -----------------------------------

    SKILLS_PROMPT = """
    Analyze this digital media project and extract the key production skills,
    artistic techniques, and technical competencies visible from its description.

    Focus on:
    - editing skills
    - composition and color
    - visual storytelling
    - graphic design or illustration techniques
    - technical workflow knowledge (e.g., Premiere, Blender, Photoshop)
    - creative decisions

    Return skills as a comma-separated list.

    Project name: {project_name}
    Media type: {media_type}
    Details: {details}

    Skills:
    """

    DESCRIPTION_PROMPT = """
    Write a concise 2–3 sentence description of this digital media project.
    Highlight:
    - purpose and style
    - notable visual elements (composition, color, motion, layout)
    - creative intent or storytelling aspects
    - tools or techniques if implied

    Project name: {project_name}
    Media type: {media_type}
    Details: {details}
    Skills: {skills}

    Description:
    """

    CONTRIBUTION_PROMPT = """
    Estimate the contributor's effort level for this media project (1–10 scale).
    Consider:
    - project complexity
    - visual detail
    - editing/rendering effort
    - creativity and technical skill implied

    Project name: {project_name}
    Media type: {media_type}
    Skills: {skills}

    Score:
    """

    # ---------- INIT + CACHING -----------------------------

    def __init__(self):
        self.ai_service: AIService = get_ai_service()
        self.cache_dir = Path("data/ai_media_project_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hits = 0

    def _path(self, project_name: str, key: str) -> Path:
        safe = project_name.replace(" ", "_").lower()
        return self.cache_dir / f"{safe}_{key}.json"

    def _load(self, name: str, key: str):
        p = self._path(name, key)
        if p.exists():
            try:
                self.cache_hits += 1
                with open(p, "r") as f:
                    return json.load(f)

            except:
                return None

    def _save(self, name: str, key: str, data: Any):
        p = self._path(name, key)
        try:
            with open(p, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"⚠️ Cache write error: {e}")

    # ---------- SKILLS EXTRACTION --------------------------

    def extract_skills(self, project_dict: Dict[str, Any]) -> List[str]:
        project_name = project_dict["project_name"]
        cached = self._load(project_name, "skills")

        if cached:
            return cached["skills"]

        prompt = self.SKILLS_PROMPT.format(
            project_name=project_name,
            media_type=project_dict.get("media_type", "Unknown"),
            details=project_dict.get("details", "")[:2000]
        )

        raw = self.ai_service.generate_text(prompt, temperature=0.2, max_tokens=200)
        skills = [x.strip() for x in raw.split(",") if x.strip()]

        self._save(project_name, "skills", {"skills": skills})
        return skills

    # ---------- DESCRIPTION GENERATION ----------------------

    def generate_description(self, project_dict: Dict[str, Any], skills: List[str]) -> str:
        project_name = project_dict["project_name"]
        cached = self._load(project_name, "description")

        if cached:
            return cached["description"]

        prompt = self.DESCRIPTION_PROMPT.format(
            project_name=project_name,
            media_type=project_dict.get("media_type", "Unknown"),
            details=project_dict.get("details", "")[:1500],
            skills=", ".join(skills[:6])
        )

        description = self.ai_service.generate_text(prompt, temperature=0.6, max_tokens=200).strip()

        self._save(project_name, "description", {"description": description})
        return description

    # ---------- CONTRIBUTION ESTIMATION ---------------------

    def estimate_contribution(self, project_dict: Dict[str, Any], skills: List[str]) -> float:
        project_name = project_dict["project_name"]
        cached = self._load(project_name, "contribution")

        if cached:
            return cached["score"]

        prompt = self.CONTRIBUTION_PROMPT.format(
            project_name=project_name,
            media_type=project_dict.get("media_type", "Unknown"),
            skills=", ".join(skills[:5])
        )

        raw = self.ai_service.generate_text(prompt, temperature=0.0, max_tokens=20)

        import re
        match = re.search(r"\d+(\.\d+)?", raw)
        score = float(match.group()) if match else 0

        self._save(project_name, "contribution", {"score": score})
        return score

    # ---------- COMPLETE ANALYSIS ---------------------------

    def analyze_project_complete(self, project_dict: Dict[str, Any]) -> Dict[str, Any]:
        name = project_dict.get("project_name", "Unnamed Media Project")
        print(f"🎨 Analyzing media project: {name}")

        skills = self.extract_skills(project_dict)
        project_dict["extracted_skills"] = skills

        description = self.generate_description(project_dict, skills)
        project_dict["ai_description"] = description

        score = self.estimate_contribution(project_dict, skills)
        project_dict["contribution_score"] = score

        return project_dict

    # ---------- BATCH PROCESSING ----------------------------

    def analyze_batch(self, project_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.analyze_project_complete(p) for p in project_list]

    # ---------- DB UPDATE -----------------------------------

    def analyze_and_update_db(self, project_dict: Dict[str, Any]):
        analyzed = self.analyze_project_complete(project_dict)

        try:
            projects = db_manager.get_all_projects()
            for p in projects:
                if p.name == project_dict["project_name"]:
                    db_manager.update_project(
                        p.id,
                        {
                            "ai_description": analyzed["ai_description"],
                            "skills": ", ".join(analyzed["extracted_skills"]),
                            "contribution_score": analyzed["contribution_score"]
                        }
                    )
                    print(f"💾 Updated DB for media project: {p.name}")
                    break
        except Exception as e:
            print(f"⚠️ Database update failed: {e}")

        return analyzed


# ---------- CLI ENTRY --------------------------------------

def analyze_media_project_cli():
    print(" DIGITAL MEDIA PROJECT ANALYZER (AI)")
    project_name = input("Project name: ").strip()
    media_type = input("Media type (video, image, graphic, animation, etc.): ").strip()
    details = input("Describe the media project: ").strip()

    analyzer = AIMediaProjectAnalyzer()

    project = {
        "project_name": project_name,
        "media_type": media_type,
        "details": details
    }

    result = analyzer.analyze_project_complete(project)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    analyze_media_project_cli()
