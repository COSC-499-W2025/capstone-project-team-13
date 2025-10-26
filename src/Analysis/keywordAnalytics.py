import os
import sys
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
    
    file_size_kb = os.path.getsize(file_path) / 1024
    if file_size_kb == 0:
        raise ValueError("File is empty or size is zero bytes")
    
    keyword_results = extract_code_keywords_with_scores(file_path)
    total_keyword_score = sum(score for score, _ in keyword_results)
    
    technical_density_value = total_keyword_score / file_size_kb

    return {
        "file_path": file_path,
        "file_size_kb": round(file_size_kb, 2),
        "total_keyword_score": round(total_keyword_score, 2),
        "technical_density": round(technical_density_value, 3)
    }
