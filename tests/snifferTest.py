import os
import sys

# allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Helpers.fileDataCheck import sniff_supertype        
from src.Settings.config import EXT_SUPERTYPES               

TEST_DIR = os.path.join(os.path.dirname(__file__), "testMismatch")

# map real filenames to what the extension should classify as
CASES = {
    "goodPythonFile.py":      "code",
    "wrongPythonFile.py":     "text",
    "goodHtml.html":          "code",   
    "wrongHtml.html":         "text",
    "goodTextFile.txt":       "text",
    "badTextFile.txt":        "code",
}


def test_cases():
    errs = []
    for fname, expected_content_supertype in CASES.items():
        fpath = os.path.join(TEST_DIR, fname)
        print(fpath)

        if not os.path.isfile(fpath):
            errs.append(f"[MISSING FILE] {fpath}")
            continue

        actual = sniff_supertype(fpath)                # based on content

        # Check #1: see if what is in the content is equal to what we classified it as above
        if actual != expected_content_supertype:
            errs.append(f"[EXT MISMATCH in mapping] {fname}: test expects {expected_content_supertype}")

        else:
            print(f"[OK] {fname}: content={actual}, expected={expected_content_supertype}")

    if errs:
        print("\n=== FAILED ===")
        for e in errs:
            print(e)
        raise SystemExit(1)

    print("\n=== ALL PASS ===")


if __name__ == "__main__":
    test_cases()
