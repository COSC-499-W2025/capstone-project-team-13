import os
import sys
import pandas as pd
import re
import math
from math import sqrt
import numpy as np
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores
from src.Analysis.skillsExtractCoding import extract_skills_with_scores

def technical_density(file_path):
    """
    Calculates the technical density of a code file based on file size and keyword extraction.
    Technical Density (raw) = total_keyword_score / file_size_in_kb
    Normalized Density (0–1) = min(log10(raw_density + 1) / 2, 1)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path) / 1024
    if file_size == 0:
        raise ValueError("File is empty or size is zero bytes")
    
    keyword_results = extract_code_keywords_with_scores(file_path)
    total_keyword_score = sum(score for score, _ in keyword_results)
    
    # Raw density value
    technical_density_value = total_keyword_score / file_size
    
    # Normalize density to 0–1 scale
    # - log scale keeps large values from dominating
    # - divide by 2 so typical code (log10 ≈ 1–2) stays in 0.3–0.6 range
    normalized_density = min(math.log10(technical_density_value + 1) / 2, 1.0)

    return {
        "file_path": file_path,
        "file_size": round(file_size, 2),
        "total_keyword_score": round(total_keyword_score, 2),
        "technical_density_raw": round(technical_density_value, 3),
        "technical_density": round(normalized_density, 3)
    }

def keyword_clustering(file_path):
    """
    Returns weighted keyword scores per cluster for a given code file,
    normalized so that total weights sum to 1.00. 'Uncategorized' is
    always included at the end if present.

    Args:
        file_path (str): Path to code file.

    Returns:
        pd.DataFrame: Columns ['Cluster', 'Score'] with normalized weights.
    """
    keyword_results = extract_code_keywords_with_scores(file_path)
    cluster_scores = {}

    for score, phrase in keyword_results:
        phrase_lower = phrase.lower()
        matched = False

        for cluster, terms in SKILL_KEYWORDS.items():
            for term in terms:
                if term in phrase_lower:
                    cluster_scores[cluster] = cluster_scores.get(cluster, 0.0) + score
                    matched = True
                    break

        if not matched:
            cluster_scores["Uncategorized"] = cluster_scores.get("Uncategorized", 0.0) + score

    # Normalization
    total = sum(cluster_scores.values())
    if total > 0:
        normalized = {k: v / total for k, v in cluster_scores.items()}
    else:
        normalized = cluster_scores

    # Round and adjust for rounding drift
    rounded = {k: round(v, 2) for k, v in normalized.items()}
    diff = round(1.0 - sum(rounded.values()), 2)
    if diff != 0 and len(rounded) > 0:
        max_key = max(rounded, key=rounded.get)
        rounded[max_key] = round(rounded[max_key] + diff, 2)

    # Convert to DataFrame
    df = pd.DataFrame(
    [{"Cluster": k, "Keywords": v} for k, v in rounded.items()]
    )

    # Separate Uncategorized
    uncategorized = df[df["Cluster"] == "Uncategorized"]
    categorized = df[df["Cluster"] != "Uncategorized"]

    # Sort categorized clusters by Keywords descending
    categorized = categorized.sort_values(by="Keywords", ascending=False).reset_index(drop=True)

    # Append Uncategorized at the end
    df_sorted = pd.concat([categorized, uncategorized], ignore_index=True)

    return df_sorted

def calculate_final_score(file_path, folder_path=None, weight_density=0.2, weight_alignment=0.8):
    """
    Calculates a final technical quality score (1–100%) for a code file.

    Combines:
        - Technical density (complexity/effort measure)
        - Skill alignment (keyword and skill overlap)
    """

    # Step 1: Technical Density (already normalized to 0–1)
    density_result = technical_density(file_path)
    tech_density = density_result["technical_density"]
    density_norm = min(max(tech_density, 0), 1.0)

    # Step 2: Keyword Clustering
    cluster_df = keyword_clustering(file_path)
    cluster_dict = dict(zip(cluster_df["Cluster"], cluster_df["Keywords"]))

    # Step 3: Skill Extraction (from folder or same file)
    if folder_path:
        skill_scores = extract_skills_from_folder(folder_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        skill_scores = extract_skills_with_scores(text)

    # Step 4: Alignment Score Calculation
    cluster_keys = list(cluster_dict.keys())
    skill_keys = list(skill_scores.keys())

    if not cluster_keys or not skill_keys:
        alignment_score = 0.0
    else:
        # 1️⃣ Base presence score — reward for existing in both sets
        matching_clusters = set(cluster_keys) & set(skill_keys)
        presence_score = len(matching_clusters) / len(skill_keys)

        # 2️⃣ Positional proximity score — reward if clusters appear in similar order
        rank_score = 0.0
        for k in matching_clusters:
            rank_cluster = cluster_keys.index(k)
            rank_skill = skill_keys.index(k)
            rank_diff = abs(rank_cluster - rank_skill)
            # Rank proximity drops as difference increases
            rank_score += max(0, 1 - (rank_diff / max(len(cluster_keys), len(skill_keys))))
        rank_score = rank_score / len(matching_clusters) if matching_clusters else 0.0

        # Weighted combination: 70% presence, 30% order similarity
        alignment_score = (0.7 * presence_score + 0.3 * rank_score)

    alignment_score = min(max(alignment_score, 0.0), 1.0)

    # Step 5: Weighted Final Combination
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