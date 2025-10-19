from rake_nltk import Rake
import nltk

# Ensure necessary NLTK data is available
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')

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

# Example usage
if __name__ == "__main__":
    sample_text = """
    Artificial intelligence and machine learning are transforming the world.
    They are applied in healthcare, finance, and transportation to optimize outcomes.
    """

    results = extract_keywords_with_scores(sample_text)

    print("Extracted Keywords (with scores):\n")
    for score, phrase in results:
        print(f"{score:.2f}  -  {phrase}")
