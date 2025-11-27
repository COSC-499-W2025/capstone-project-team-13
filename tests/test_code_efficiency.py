import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from Analysis.codeEfficiency import grade_efficiency

def run_tests_from_sample_file():
    """
    Loads the contents of sample_test_code.py and runs grade_efficiency on it.
    """
    sample_path = os.path.join(
        os.path.dirname(__file__),
        "sample_test_code.py"
    )

    # Read code
    with open(sample_path, "r", encoding="utf-8") as f:
        code = f.read()

    print("\n--- Running Code Efficiency Test ---")
    print(f"Analyzing: {sample_path}")

    results = grade_efficiency(code, sample_path)

    print("\n--- Results ---")
    for key, value in results.items():
        if key == "notes":
            print(f"{key}:")
            for note in value:
                print(f"  - {note}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    run_tests_from_sample_file()
