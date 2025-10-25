from collections import defaultdict
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
    if total > 0:
        for skill in scores:
            scores[skill] = round(scores[skill] / total, 2)

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
