from collections import defaultdict
from pathlib import Path
import re

# Skill categories and keywords 
SKILL_KEYWORDS = {
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
# Extract skills from all text files in a folder
def extract_skills_from_folder(folder_path, file_extensions=None):
    
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(f"{folder_path} is not a valid folder")

    all_text = ""
    for file in folder.rglob("*"):  # recursively include subfolders
        if file.is_file() and (file_extensions is None or file.suffix in file_extensions):
            try:
                all_text += file.read_text(encoding="utf-8") + "\n"
            except UnicodeDecodeError:
                pass  # skip non-text files

    return extract_skills_with_scores(all_text)

# weighted skill scoring
def extract_skills_with_scores(text):
    text = text.lower()
    scores = defaultdict(float)

    # Tokenize to avoid partial matches (ex. nosql vs sql)
    for skill, keywords in SKILL_KEYWORDS.items():
        for kw in keywords:
            kw_lower = kw.lower()
            # Use regex to match whole words (multi-word keywords are handled too)
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            matches = re.findall(pattern, text)
            if matches:
                scores[skill] += len(matches)

    # normalizing score
    total = sum(scores.values())
    if total == 0:
        return {}

    if total > 0:
        normalized = {k: (v / total) for k, v in scores.items()}

        # Round to 2 decimals and ensure total = 1.00
        rounded = {k: round(v, 2) for k, v in normalized.items()}
        diff = round(1.0 - sum(rounded.values()), 2)

        if diff != 0:
            # Adjust the skill with the largest score to absorb rounding drift
            max_key = max(rounded, key=rounded.get)
            rounded[max_key] = round(rounded[max_key] + diff, 2)

    return dict(sorted(rounded.items(), key=lambda x: x[1], reverse=True))
