# from pydoc import text
import sys
import os
import unittest

# Ensure the src folder is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.Extraction.keywordExtractorText import extract_keywords_with_scores


class TestKeywordExtractor(unittest.TestCase):

    def test_basic_extraction(self):
        """Test that the function extracts some keywords from valid text."""
        text = (
            "Artificial intelligence and machine learning are transforming industries. "
            "AI systems are becoming more capable of solving complex problems."
        )
        results = extract_keywords_with_scores(text)

        # Expect at least one keyword
        self.assertTrue(len(results) > 0, "No keywords were extracted")

        # Ensure each result is a tuple of (score, keyword)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertIsInstance(item[0], (int, float))
            self.assertIsInstance(item[1], str)

        # Check that the scores are in descending order
        scores = [score for score, _ in results]
        self.assertEqual(scores, sorted(scores, reverse=True), "Scores are not sorted descending")

    def test_empty_text(self):
        """Test that empty input returns an empty list."""
        results = extract_keywords_with_scores("")
        self.assertEqual(results, [], "Empty input should return an empty list")

    def test_repeated_words(self):
        """Test that repeated words affect keyword scoring."""
        text = "Python Python Python programming language for data science."
        results = extract_keywords_with_scores(text)

        self.assertTrue(any("python" in kw.lower() for _, kw in results),
                        "Expected 'Python' to appear in top keywords")

    def test_no_long_sentence_phrases(self):
        text = (
        "Future improvements may include machine learning based skill classification."
        )
        results = extract_keywords_with_scores(text)

        self.assertTrue(
        all(len(keyword.split()) <= 4 for _, keyword in results),
        "Extractor should not return long sentence-like phrases"
       )

    def test_technical_terms_are_extracted(self):
        text = "This project uses Python, NumPy, and Pandas for data analysis."
        results = extract_keywords_with_scores(text)

        extracted = [kw.lower() for _, kw in results]

        self.assertIn("python", extracted)
        self.assertIn("numpy", extracted)
        self.assertIn("pandas", extracted)

if __name__ == "__main__":
    unittest.main()
