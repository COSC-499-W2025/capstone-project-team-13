import sys
import os
import unittest
from pathlib import Path

# Ensure the src folder is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.keywordExtractorCode import extract_code_keywords_with_scores


class TestKeywordExtractorCode(unittest.TestCase):

    def setUp(self):
        """Create a small test code file."""
        self.test_file_path = Path(os.path.join(os.path.dirname(__file__), 'test_code.py'))
        self.test_code = """\
# This is a Python test function
def add(a, b):
    # Adds two numbers
    return a + b

# Another comment
"""
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(self.test_code)

    def tearDown(self):
        """Clean up test file."""
        if self.test_file_path.exists():
            self.test_file_path.unlink()

    def test_extract_from_text(self):
        """Test extracting keywords from raw code text."""
        results = extract_code_keywords_with_scores(self.test_code)
        keywords = [kw for _, kw in results]

        # Expect some keywords from comments
        self.assertTrue(any("adds" in kw.lower() for kw in keywords), "Expected 'adds' in keywords")
        self.assertTrue(any("numbers" in kw.lower() for kw in keywords), "Expected 'numbers' in keywords")

    def test_extract_from_file(self):
        """Test extracting keywords from a code file."""
        results = extract_code_keywords_with_scores(self.test_file_path)
        keywords = [kw for _, kw in results]

        self.assertTrue(any("adds" in kw.lower() for kw in keywords), "Expected 'adds' in keywords")
        self.assertTrue(any("numbers" in kw.lower() for kw in keywords), "Expected 'numbers' in keywords")

    def test_invalid_input(self):
        """Test passing an invalid input type raises TypeError."""
        with self.assertRaises(TypeError):
            extract_code_keywords_with_scores(None)  # None is invalid


if __name__ == "__main__":
    unittest.main()
