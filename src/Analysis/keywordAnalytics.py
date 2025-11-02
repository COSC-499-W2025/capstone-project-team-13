import os
import sys
import pandas as pd
import re
from math import sqrt
import numpy as np
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores
from src.Analysis.skillsExtractCoding import extract_skills_with_scores

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

def calculate_final_score(file_path, folder_path=None, weight_density=0.5, weight_alignment=0.5):
    """
    Calculates a final technical quality score (1-100%) for a code file.

    Combines:
        - Technical density (complexity/effort measure)
        - Skill alignment (how well keyword clusters match detected skills)
    
    Args:
        file_path (str): Path to the target code file.
        folder_path (str, optional): Folder for global skill extraction.
        weight_density (float): Weight for technical density (default=0.5)
        weight_alignment (float): Weight for skill alignment (default=0.5)

    Returns:
        dict: {
            "file_path": str,
            "technical_density": float,
            "alignment_score": float,
            "final_score": float
        }
    """
    # --- Step 1: Compute Technical Density ---
    density_result = technical_density(file_path)
    tech_density = density_result["technical_density"]

    # Normalize technical density to a 0–1 scale (capped)
    density_norm = min(tech_density / 10, 1.0)

    # --- Step 2: Get Keyword Clusters ---
    cluster_df = keyword_clustering(file_path)
    cluster_dict = dict(zip(cluster_df["Cluster"], cluster_df["Keywords"]))
    
    # Normalize keyword cluster frequencies
    total_keywords = sum(cluster_dict.values())
    if total_keywords == 0:
        return {
            "file_path": file_path,
            "technical_density": round(tech_density, 3),
            "alignment_score": 0,
            "final_score": 0
        }
    cluster_norm = {k: v / total_keywords for k, v in cluster_dict.items()}

    # --- Step 3: Compute Skill Scores ---
    if folder_path:
        skill_scores = extract_skills_from_folder(folder_path)
    else:
        # fallback: extract from same file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        skill_scores = extract_skills_with_scores(text)

    # --- Step 4: Compute Alignment (Cosine Similarity) ---
    all_keys = set(cluster_norm.keys()).union(skill_scores.keys())
    v1 = np.array([cluster_norm.get(k, 0.0) for k in all_keys])
    v2 = np.array([skill_scores.get(k, 0.0) for k in all_keys])

    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        alignment_score = 0.0
    else:
        alignment_score = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    # --- Step 5: Combine into Final Score ---
    final_score = (density_norm * weight_density + alignment_score * weight_alignment) * 100

    return {
        "file_path": file_path,
        "technical_density": round(tech_density, 3),
        "alignment_score": round(alignment_score, 3),
        "final_score": round(final_score, 2)
    }


# TODO: Once PR containing SKILL_KEYWORDS is merged (#82), import from there instead
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