"""
Incremental Skill Updater

Detects newly introduced libraries from import statements
in newly added or modified Python files and merges them into
existing project skills.
"""

from pathlib import Path
from typing import List, Set

from src.Databases.database import db_manager


SUPPORTED_CODE_EXTENSIONS = {".py"}

# Map import names to canonical skill names
IMPORT_TO_SKILL = {
    "numpy": "NumPy",
    "pandas": "Pandas",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "django": "Django",
    "flask": "Flask",
}


def _extract_imports_from_python(file_path: Path) -> Set[str]:
    """Extract top-level imported modules from a Python file."""
    imports = set()

    try:
        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()

            # import numpy as np
            if line.startswith("import "):
                parts = line.replace("import", "").split(",")
                for p in parts:
                    module = p.strip().split(" ")[0]
                    imports.add(module)

            # from numpy import array
            elif line.startswith("from "):
                module = line.replace("from", "").split("import")[0].strip()
                imports.add(module)

    except Exception as e:
        print(f"⚠️ Failed to parse imports from {file_path}: {e}")

    return imports


def update_skills_incremental(project_id: int, new_files: List[Path]) -> None:
    if not new_files:
        return

    detected_skills: Set[str] = set()

    for file in new_files:
        if file.suffix.lower() not in SUPPORTED_CODE_EXTENSIONS:
            continue

        imported_modules = _extract_imports_from_python(file)

        for module in imported_modules:
            skill = IMPORT_TO_SKILL.get(module.lower())
            if skill:
                detected_skills.add(skill)

    if not detected_skills:
        return

    project = db_manager.get_project(project_id)
    existing_skills = set(project.skills or [])

    merged_skills = sorted(existing_skills.union(detected_skills))

    db_manager.update_project(project_id, {
        "skills": merged_skills
    })

    print(f"✓ Incremental skills updated: {', '.join(detected_skills)}")
