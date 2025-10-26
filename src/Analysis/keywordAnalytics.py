import os
import re
import sys
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores

def technical_density(file_path):
    """
    Calculates the technical density of a code file based on file size and keyword extraction.
    Technical Density = total_keywords / file_size_in_kb
    """    

    # Ensure the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get the file size in kilobytes
    file_size = os.path.getsize(file_path) / 1024
    if file_size == 0:
        raise ValueError("File is empty or size is zero bytes")
    
    # Extract keywords using your existing extractor
    keyword_results = extract_code_keywords_with_scores(file_path)

    total_keywords_score = sum(keyword_results)

    # Calculate technical density
    technical_density = total_keywords / file_size_kb    

    return {
        "file_path": file_path,
        "file_size_kb": round(file_size_kb, 2),
        "total_keywords": total_keywords,
        "technical_density": round(technical_density, 3)
    }