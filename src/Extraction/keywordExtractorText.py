from rake_nltk import Rake
import nltk
# from pathlib import Path
# from typing import Union



#Adding helper functions to inscrease accuracy of keyword extraction
# ---------------------------
# Keyword post-processing helpers
# ---------------------------

GENERIC_PHRASES = {
    "future improvements",
    "challenges included",
    "general descriptive language",
    "goal of the system"
}

TECH_TERMS = {
    
    "python", "javascript", "sql", "git", "numpy", "pandas"
}


def filter_by_phrase_length(keywords, max_words=4):
    """Remove overly long keyword phrases."""
    return [
        (score, phrase)
        for score, phrase in keywords
        if len(phrase.split()) <= max_words
    ]


def filter_generic_phrases(keywords):
    """Remove generic academic or descriptive phrases."""
    filtered = []
    for score, phrase in keywords:
        lowered = phrase.lower()
        if not any(generic in lowered for generic in GENERIC_PHRASES):
            filtered.append((score, phrase))
    return filtered


def normalize_keywords(keywords):
    """
    Normalize keywords by extracting core technical terms
    from longer phrases and boosting their scores.
    """
    normalized = []
    for score, phrase in keywords:
        words = phrase.lower().split()
        replaced = False

        for term in TECH_TERMS:
            if term in words:
                normalized.append((score + 5, term.title()))
                replaced = True
                break

        if not replaced:
            normalized.append((score, phrase))

    return normalized


def boost_repeated_technical_terms(text, keywords):
    """
    Detect repeated technical terms in the text and ensure they appear in results.
    This handles cases where RAKE doesn't extract single repeated words well.
    """
    text_lower = text.lower()
    found_terms = {}
    
    # Count occurrences of each technical term
    for term in TECH_TERMS:
        count = text_lower.count(term)
        if count > 0:
            found_terms[term] = count
    
    # Add technical terms that appeared but weren't extracted
    extracted_lower = {kw.lower() for _, kw in keywords}
    
    for term, count in found_terms.items():
        if term not in extracted_lower:
            # Score based on frequency (minimum 3 to ensure visibility)
            score = max(3, count * 2)
            keywords.append((score, term.title()))
    
    return keywords



# Ensure necessary NLTK data is available
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    print(f"NLTK download failed — {e}")

def extract_keywords_with_scores(text: str):
    """
    Extracts keywords and their scores from a text string using RAKE (NLTK),
    with post-processing to improve precision and relevance.
    
    Args:
        text (str): Input text to analyze.

    Returns:
        List[Tuple[float, str]]: A list of (score, keyword) pairs, sorted by importance.
    """
    if not text.strip():
        return []
    
    r = Rake()  # Uses default English stopwords
    r.extract_keywords_from_text(text)
    keywords = r.get_ranked_phrases_with_scores()

    # Post-processing steps (YOUR contribution)
    keywords = filter_by_phrase_length(keywords)
    keywords = filter_generic_phrases(keywords)
    keywords = normalize_keywords(keywords)
    keywords = boost_repeated_technical_terms(text, keywords)

    return sorted(keywords, reverse=True)


