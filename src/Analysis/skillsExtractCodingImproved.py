from collections import defaultdict
from pathlib import Path
import re



# --- Top-level skill keywords ---
SKILL_KEYWORDS = {
    "Python": ["python"],
    # --- Web and App Development ---
    "Web Development": [
        "html", "css", "javascript", "typescript", "flask", "django",
        "express", "node", "php", "ruby on rails", "nextjs", "nuxt"
    ],
    "Frontend Development": [
        "react", "vue", "angular", "svelte", "bootstrap", "tailwind",
        "html", "css", "dom", "ui", "ux"
    ],
    "Backend Development": [
        "flask", "django", "express", "fastapi", "spring", "node",
        "api", "server", "microservices", "rest", "graphql"
    ],
     "API Development": [
        "rest", "graphql", "endpoint", "swagger", "postman", "jwt", "oauth"
    ],
    "Mobile Development": [
        "android", "ios", "flutter", "swift", "kotlin", "react native"
    ],

    # --- Databases ---
    "Relational Databases": [
        "sql", "mysql", "postgresql", "sqlite", "oracle", "mariadb",
        "schema", "foreign key", "join", "table"
    ],
    "Non-Relational Databases": [
        "nosql", "mongodb", "redis", "cassandra", "dynamodb",
        "couchdb", "neo4j", "graphdb", "document store"
    ],
    "Database Management": [
        "orm", "query", "database", "migration", "index", "data model"
    ],

    # --- Data & AI ---
    "Data Science": [
        "numpy", "pandas", "matplotlib", "scipy", "dataframe",
        "jupyter", "statistics", "data analysis"
    ],
    "Machine Learning": [
        "tensorflow", "keras", "pytorch", "sklearn", "xgboost",
        "regression", "classification", "model training"
    ],
    "Data Visualization": [
        "matplotlib", "seaborn", "plotly", "tableau", "dash", "ggplot"
    ],
    "Data Engineering": [
        "airflow", "spark", "hadoop", "etl", "data pipeline", "big data", "kafka"
    ],

    # --- DevOps / Cloud ---
    "DevOps": [
        "docker", "kubernetes", "jenkins", "ci/cd", "github actions",
        "pipeline", "automation", "monitoring"
    ],
    "Cloud Computing": [
        "aws", "azure", "gcp", "google cloud", "lambda", "s3",
        "cloud functions", "deployment", "infrastructure as code"
    ],

    # --- Software Engineering Practices ---
    "Testing & QA": [
        "pytest", "unittest", "selenium", "cypress", "mocha",
        "testcase", "assertion", "coverage", "jest"
    ],
    "Version Control": [
        "git", "github", "gitlab", "bitbucket", "commit", "branch", "merge"
    ],
    "Security & Cybersecurity": [
        "encryption", "hashing", "vulnerability", "penetration testing",
        "firewall", "jwt", "oauth", "authentication", "authorization"
    ],

    # --- Game and Graphics ---
    "Game Development": [
        "unity", "unreal", "godot", "game engine", "shader", "physics", "collision detection"
    ],
    "3D Rendering": [
        "webgl", "opengl", "three.js", "blender", "shader", "ray tracing", "lighting", "camera", "vertex", "fragment"
    ],
     "Computer Vision": [
        "opencv", "image processing", "object detection", "segmentation"
    ],

    # other
    
    "AI & Natural Language Processing": [
        "nlp", "transformer", "bert", "gpt", "tokenization", "embedding"
    ],
   
}
# --- Subskills / libraries per top-level skill (including multi-word) ---
SUBSKILL_KEYWORDS = {
    "Python": {
        "libraries": ["numpy", "pandas", "scipy", "matplotlib", "seaborn", "tensorflow",
                      "keras", "pytorch", "sklearn", "xgboost", "transformers", "randomforestclassifier"],
    },
    "Machine Learning": {
        "algorithms": ["regression", "classification", "clustering", "xgboost", "random forest", "RandomForestClassifier"],
        "libraries": ["tensorflow", "keras", "pytorch", "sklearn"]
    },
    "Data Science": {
        "tools": ["pandas", "numpy", "matplotlib", "seaborn", "jupyter"],
        "techniques": ["data cleaning", "data analysis", "statistics", "visualization"]
    },
    "Web Development": {
        "libraries": ["react", "vue", "angular", "bootstrap", "tailwind", "nextjs", "nuxt"],
        "multi_word": ["rest api", "webgl shader", "ruby on rails", "google cloud"]
    }
}

GENERIC_SKILLS = {
    "Web Development",
    "Backend Development",
    "Frontend Development",
    "API Development",
    "Database Management",
    "Testing & QA",
    "Version Control",
    "DevOps"
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
    skill_subskills = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    project_detected_skills = set()
    raw_skill_hits = defaultdict(int)

    for file in folder.rglob("*"):
        if not file.is_file():
            continue
        if file_extensions and file.suffix not in file_extensions:
            continue

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

        # 1️⃣ Top-level skills (ONLY if keyword appears)
        for skill, keywords in SKILL_KEYWORDS.items():
            for kw in keywords:
                pattern = r'\b' + re.escape(kw) + r'\b'
                matches = re.findall(pattern, text)
                if matches:
                    count = len(matches)
                    detected_skills.add(skill)
                    raw_skill_hits[skill] += count
                    skill_scores[skill] += count * folder_weight
                    skill_subskills[skill]["keywords"][kw] += count

        # 2️⃣ Subskills (ONLY if parent skill already detected)
        for skill, groups in SUBSKILL_KEYWORDS.items():
            if skill not in detected_skills:
                continue

            for group, keywords in groups.items():
                for kw in keywords:
                    pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                    matches = re.findall(pattern, text)
                    if matches:
                        count = len(matches)
                        raw_skill_hits[skill] += count
                        skill_subskills[skill][group][kw] += count

                        boost = 0.5 if kw.lower() in ADVANCED_KEYWORDS else 0.3
                        skill_scores[skill] += count * boost * folder_weight

        project_detected_skills.update(detected_skills)

    # 🚫 Nothing detected → safe return
    if not skill_scores:
        return {"skills": {}, "skill_combinations": {}}

    # 3️⃣ Filter weak skills
    MIN_RAW_COUNT = 8
    filtered_scores = {
        skill: score
        for skill, score in skill_scores.items()
        if raw_skill_hits[skill] >= MIN_RAW_COUNT
    }

    if not filtered_scores:
        return {"skills": {}, "skill_combinations": {}}

    # 4️⃣ Normalize
    total_score = sum(filtered_scores.values())
    normalized_scores = {
        skill: round(score / total_score, 3)
        for skill, score in filtered_scores.items()
    }

    # 5️⃣ Skill combinations
    combinations = defaultdict(float)
    skills = sorted(filtered_scores.keys())
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            combinations[(skills[i], skills[j])] += 1

    max_comb = max(combinations.values(), default=1)
    normalized_combinations = {
        pair: round(val / max_comb, 3)
        for pair, val in combinations.items()
    }

        # 6️⃣ Final output
    final_output = {}
    for skill, score in normalized_scores.items():
        if skill in GENERIC_SKILLS:
            continue  # Skip generic / descriptor skills

        final_output[skill] = {
            "score": score,
            "subskills": {
                group: dict(sorted(items.items(), key=lambda x: x[1], reverse=True))
                for group, items in skill_subskills[skill].items()
                if items
            }
        }

    return {
        "skills": dict(sorted(final_output.items(), key=lambda x: x[1]["score"], reverse=True)),
        "skill_combinations": dict(
            sorted(normalized_combinations.items(), key=lambda x: x[1], reverse=True)
        )
    }


