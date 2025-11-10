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
    AI-powered analyzer for text projects (Word, PDF, plain text), following the same
    structure as the coding project analyzer.

    Features:
    - Extract skills/topics (including style/structure insights)
    - Estimate contribution score
    - Smart caching to minimize API calls
    """

    SKILLS_PROMPT_TEMPLATE = """
    Analyze the following text project and extract the main writing/author skills, topics, or key concepts.
    Include writing style and structural insights as part of the skills.

    Project: {project_name}
    Content (first 2000 chars): {content_snippet}

    Skills/Topics (comma-separated):
    """

    CONTRIBUTION_PROMPT_TEMPLATE = """
    Estimate the contributor's level of effort and impact on this text project (1-10 scale).
    Provide a single numeric score.

    Project: {project_name}
    Word count: {word_count}
    Skills/Topics: {skills}
    """

    def __init__(self):
        self.ai_service: AIService = get_ai_service()
        self.cache_dir = Path("data/ai_text_project_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hits = 0
        self.analysis_count = 0

    def _get_cache_file(self, project_name: str, analysis_type: str) -> Path:
        """Generate path to cached JSON file."""
        filename = f"{project_name}_{analysis_type}.json".replace(" ", "_")
        return self.cache_dir / filename

    def _load_cache(self, project_name: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        """Return cached analysis if exists."""
        cache_file = self._get_cache_file(project_name, analysis_type)
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                self.cache_hits += 1
                return data
            except Exception:
                return None
        return None

    def _save_cache(self, project_name: str, analysis_type: str, data: Dict[str, Any]):
        """Save analysis to cache."""
        cache_file = self._get_cache_file(project_name, analysis_type)
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")

    def extract_skills(self, project_dict: Dict[str, Any]) -> List[str]:
        """Extract skills/topics including writing style insights."""
        project_name = project_dict.get("project_name", "Unnamed Text Project")

        # Check cache first
        cached = self._load_cache(project_name, "skills")
        if cached:
            return cached.get("extracted_skills", [])

        # Prompt AI
        content_snippet = project_dict.get("content", "")[:2000]
        prompt = self.SKILLS_PROMPT_TEMPLATE.format(
            project_name=project_name,
            content_snippet=content_snippet
        )

        skills_text = self.ai_service.generate_text(prompt, temperature=0.3, max_tokens=150)
        extracted_skills = [s.strip() for s in skills_text.split(",") if s.strip()]

        # Cache results
        self.analysis_count += 1
        self._save_cache(project_name, "skills", {"extracted_skills": extracted_skills})

        return extracted_skills

    def estimate_contribution(self, project_dict: Dict[str, Any], skills: List[str]) -> float:
        """Estimate contributor's effort and impact (1-10 scale)."""
        project_name = project_dict.get("project_name", "Unnamed Text Project")

        cached = self._load_cache(project_name, "contribution")
        if cached:
            return cached.get("contribution_score", 0.0)

        prompt = self.CONTRIBUTION_PROMPT_TEMPLATE.format(
            project_name=project_name,
            word_count=project_dict.get("word_count", "Unknown"),
            skills=", ".join(skills[:5])
        )

        contribution_text = self.ai_service.generate_text(prompt, temperature=0.0, max_tokens=10)

        import re
        match = re.search(r"\d+(\.\d+)?", contribution_text)
        score = float(match.group(0)) if match else 0.0

        self.analysis_count += 1
        self._save_cache(project_name, "contribution", {"contribution_score": score})

        return score

    def analyze_project(self, project_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full AI analysis on a text project."""
        project_name = project_dict.get("project_name", "Unnamed Text Project")
        print(f"🔎 Analyzing project: {project_name}")

        # Extract skills (including writing insights)
        skills = self.extract_skills(project_dict)
        project_dict["extracted_skills"] = skills

        # Estimate contribution
        contribution_score = self.estimate_contribution(project_dict, skills)
        project_dict["contribution_score"] = contribution_score

        return project_dict


# CLI
def analyze_text_project_cli():
    """Command-line interface to analyze a single text project."""
    import json

    project_name = input("Enter project name: ").strip()
    content = input("Paste text content or file content here: ").strip()
    word_count = len(content.split())

    analyzer = AITextProjectAnalyzer()
    project_dict = {"project_name": project_name, "content": content, "word_count": word_count}
    result = analyzer.analyze_project(project_dict)

    print("\n✅ Analysis Result:\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    analyze_text_project_cli()
