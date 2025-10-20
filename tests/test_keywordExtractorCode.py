import sys
import os
import unittest
from pathlib import Path

# Ensure the src folder is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.keywordExtractorCode import extract_code_keywords_with_scores


class TestKeywordExtractorCode(unittest.TestCase):

    def test_basic_extraction(self):
        """Test that the function extracts some keywords from valid code comments."""
        code_text = """
        # This is a simple test function
        def add_numbers(a, b):
            '''Returns the sum of two numbers'''
            return a + b
        // Java style single line comment
        /* Multi-line
           comment explaining subtraction */
        """
        results = extract_code_keywords_with_scores(code_text)

        # Expect at least one keyword
        self.assertTrue(len(results) > 0, "No keywords were extracted from code comments")

        # Ensure each result is a tuple of (score, keyword)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertIsInstance(item[0], (int, float))
            self.assertIsInstance(item[1], str)

    def test_empty_input(self):
        """Test that empty code returns an empty list."""
        results = extract_code_keywords_with_scores("")
        self.assertEqual(results, [], "Empty input should return an empty list")

    def test_repeated_words(self):
        """Test that repeated words affect keyword scoring."""
        code_text = """
        # debug debug debug
        # check check
        """
        results = extract_code_keywords_with_scores(code_text)
        self.assertTrue(any("debug" in kw.lower() for _, kw in results),
                        "Expected 'debug' to appear in top keywords")
        self.assertTrue(any("check" in kw.lower() for _, kw in results),
                        "Expected 'check' to appear in top keywords")

if __name__ == "__main__":
    unittest.main()
