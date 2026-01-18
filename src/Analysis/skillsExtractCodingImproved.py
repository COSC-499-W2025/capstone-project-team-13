from collections import defaultdict
from pathlib import Path
import re

# --- Top-level skill keywords ---
SKILL_KEYWORDS = {
    "Python": ["python"],
    "Web Development": ["html", "css", "javascript", "typescript", "flask", "django",
                        "express", "node", "php", "ruby on rails", "nextjs", "nuxt"],
    "Frontend Development": ["react", "vue", "angular", "svelte", "bootstrap", "tailwind",
                             "html", "css", "dom", "ui", "ux"],
    "Backend Development": ["flask", "django", "express", "fastapi", "spring", "node",
                            "api", "server", "microservices", "rest", "graphql"],
    "Machine Learning": [
        "tensorflow", "keras", "pytorch", "sklearn", "xgboost",
        "regression", "classification", "model training"
    ],
    "Data Science": ["data science", "data analysis", "dataframe", "statistics"],
    "SQL": ["sql", "mysql", "postgresql", "sqlite"],
}

# --- Subskills / libraries per top-level skill (including multi-word) ---
SUBSKILL_KEYWORDS = {
    "Python": {
        "libraries": ["numpy", "pandas", "scipy", "matplotlib", "seaborn", "tensorflow",
                      "keras", "pytorch", "sklearn", "xgboost", "transformers", "randomforestclassifier"],
        "language_features": ["async", "await", "decorator", "context manager", "generator"]
    },
    "Machine Learning": {
        "algorithms": ["regression", "classification", "clustering", "xgboost", "random forest", "RandomForestClassifier"],
        "libraries": ["tensorflow", "keras", "pytorch", "sklearn"]
    },
    "Data Science": {
        "tools": ["pandas", "numpy", "matplotlib", "seaborn", "jupyter"],
        "techniques": ["data cleaning", "data analysis", "statistics", "visualization"]
    },
    "SQL": {
        "commands": ["join", "select", "insert", "update", "delete", "group by", "foreign key"]
    },
    "Web Development": {
        "libraries": ["react", "vue", "angular", "bootstrap", "tailwind", "nextjs", "nuxt"],
        "multi_word": ["rest api", "webgl shader", "ruby on rails", "google cloud"]
    }
}

# --- Advanced coding keywords for boosting ---
ADVANCED_KEYWORDS = [
    "async", "await", "decorator", "pipeline", "architecture", "microservice", "orm"
]

# --- Core vs Peripheral folders ---
CORE_FOLDERS = ["src", "app", "main"]
PERIPHERAL_FOLDERS = ["tests", "docs", "scripts"]

# --- Helper to match multi-word keywords first ---
def find_keywords(text, keywords):
    """Return list of keywords found in text."""
    found = []
    for kw in keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text):
            found.append(kw)
    return found

# --- Main skill analyzer ---
def analyze_coding_skills_refined(folder_path, file_extensions=None):
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"{folder_path} is not a valid folder")

    skill_scores = defaultdict(float)
    skill_subskills = defaultdict(lambda: defaultdict(set))
    project_detected_skills = set()  # project-wide skills for co-occurrence

    for file in folder.rglob("*"):
        if file.is_file() and (file_extensions is None or file.suffix in file_extensions):
            try:
                text = file.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError:
                continue

            parts = [p.lower() for p in file.parts]
            if any(cf in parts for cf in CORE_FOLDERS):
                folder_weight = 1.5
            elif any(pf in parts for pf in PERIPHERAL_FOLDERS):
                folder_weight = 0.8
            else:
                folder_weight = 1.0

            detected_skills = set()

            # --- Detect top-level keywords ---
            for skill, keywords in SKILL_KEYWORDS.items():
                if find_keywords(text, keywords):
                    detected_skills.add(skill)

            # --- Detect subskills and trigger top-level if needed ---
            for skill, subcats in SUBSKILL_KEYWORDS.items():
                skill_found = False
                for subcat, subkeys in subcats.items():
                    found_subskills = find_keywords(text, subkeys)
                    if found_subskills:
                        skill_subskills[skill][subcat].update(found_subskills)
                        skill_scores[skill] += sum(
                            0.5 if sk in ADVANCED_KEYWORDS else 0.2 for sk in found_subskills
                        ) * folder_weight
                        skill_found = True
                if skill_found:
                    detected_skills.add(skill)

            # --- Top-level keyword scoring ---
            for skill in detected_skills:
                skill_scores[skill] += 1 * folder_weight

            # --- Track project-wide skills ---
            project_detected_skills.update(detected_skills)

    # --- Normalize skill scores ---
    total_score = sum(skill_scores.values())
    normalized_scores = {k: round(v / total_score, 3) for k, v in skill_scores.items()} if total_score > 0 else {}

    # --- Project-wide skill combinations ---
    combinations = defaultdict(float)
    skills_list = sorted(project_detected_skills)
    for i in range(len(skills_list)):
        for j in range(i + 1, len(skills_list)):
            pair = (skills_list[i], skills_list[j])
            combinations[pair] += 1

    max_comb = max(combinations.values(), default=1)
    normalized_combinations = {k: round(v / max_comb, 3) for k, v in combinations.items()}

    # --- Build final nested output ---
    nested_output = {}
    for skill, score in normalized_scores.items():
        nested_output[skill] = {
            "score": score,
            "subskills": {k: list(v) for k, v in skill_subskills.get(skill, {}).items()}
        }

    return {
        "skills": nested_output,
        "skill_combinations": dict(sorted(normalized_combinations.items(), key=lambda x: x[1], reverse=True))
    }
