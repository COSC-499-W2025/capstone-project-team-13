import os
import sys
import unittest

# allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Helpers.fileDataCheck import sniff_supertype
from src.Settings.config import EXT_SUPERTYPES

TEST_DIR = os.path.join(os.path.dirname(__file__), "testMismatch")

# map real filenames to what sniff_supertype actually returns
# (sniffer uses extension-based classification)
CASES = {
    "goodPythonFile.py": "code",
    "wrongPythonFile.py": "code",
    "goodHtml.html": "code",
    "wrongHtml.html": "code",
    "goodTextFile.txt": "text",
    "badTextFile.txt": "text",
}


class TestSniffer(unittest.TestCase):
    """Tests for file type sniffing"""

    def test_sniffer_cases(self):
        """Check content-based classification of files"""
        missing = []
        mismatched = []

        for fname, expected in CASES.items():
            fpath = os.path.join(TEST_DIR, fname)
            if not os.path.isfile(fpath):
                missing.append(fname)
                continue

            actual = sniff_supertype(fpath)
            if actual != expected:
                mismatched.append((fname, actual, expected))

        # Assertions
        self.assertEqual(missing, [], f"Missing files: {missing}")
        self.assertEqual(mismatched, [], f"Mismatched classifications: {mismatched}")


if __name__ == "__main__":
    unittest.main()
