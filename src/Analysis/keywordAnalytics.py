import os
import sys
import pandas as pd
import re
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores


def technical_density(file_path):
    """
    Calculates the technical density of a code file based on file size and keyword extraction.
    Technical Density = total_keyword_score / file_size_in_kb
    """    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path) / 1024
    if file_size == 0:
        raise ValueError("File is empty or size is zero bytes")
    
    keyword_results = extract_code_keywords_with_scores(file_path)
    total_keyword_score = sum(score for score, _ in keyword_results)
    
    technical_density_value = total_keyword_score / file_size

    return {
        "file_path": file_path,
        "file_size": round(file_size, 2),
        "total_keyword_score": round(total_keyword_score, 2),
        "technical_density": round(technical_density_value, 3)
    }

def keyword_clustering(file_path):
    """
    Returns counts of keywords per cluster for a given code file,
    with 'Uncategorized' always at the end.

    Args:
        file_path (str): Path to code file.

    Returns:
        pd.DataFrame: Columns ['Cluster', 'Keywords'] with counts.
    """
    keyword_results = extract_code_keywords_with_scores(file_path)
    cluster_counts = {}

    for score, phrase in keyword_results:
        phrase_lower = phrase.lower()
        matched = False

        for cluster, terms in SKILL_KEYWORDS.items():
            for term in terms:
                if term in phrase_lower:
                    cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1
                    matched = True
                    break

        if not matched:
            cluster_counts["Uncategorized"] = cluster_counts.get("Uncategorized", 0) + 1

    # Convert to DataFrame
    df = pd.DataFrame(
        [{"Cluster": k, "Keywords": v} for k, v in cluster_counts.items()]
    )

    # Separate Uncategorized
    uncategorized = df[df["Cluster"] == "Uncategorized"]
    categorized = df[df["Cluster"] != "Uncategorized"]

    # Sort categorized clusters by Keywords descending
    categorized = categorized.sort_values(by="Keywords", ascending=False).reset_index(drop=True)

    # Append Uncategorized at the end
    df_sorted = pd.concat([categorized, uncategorized], ignore_index=True)

    return df_sorted


# TODO: Once PR containing SKILL_KEYWORDS is merged, import from there instead
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