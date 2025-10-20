from rake_nltk import Rake
import nltk
from pathlib import Path
from typing import Union

# Ensure necessary NLTK data is available
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    print(f"NLTK download failed — {e}")

def extract_keywords_with_scores(text: str):
    """
    Extracts keywords and their scores from a text string using RAKE (NLTK).
    
    Args:
        text (str): Input text to analyze.

    Returns:
        List[Tuple[float, str]]: A list of (score, keyword) pairs, sorted by importance.
    """
    r = Rake()  # Uses default English stopwords
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases_with_scores()

