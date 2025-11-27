# src/tests/test_code_efficiency.py
import sys
import os
import tempfile

# Add src folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from Analysis.codeEfficiency import grade_efficiency

# --------------------------
# Python snippets (interpreted)
# --------------------------
python_simple_code = """
for i in range(10):
    print(i)
"""

python_nested_code = """
for i in range(10):
    for j in range(10):
        print(i, j)
"""

# --------------------------
# JavaScript snippet (interpreted)
# --------------------------
js_react_code = """
import React from 'react';

for (let i = 0; i < 10; i++) {
    console.log(i);
}
"""

# --------------------------
# C snippet (compiled)
# --------------------------
c_simple_code = """
#include <stdio.h>

int main() {
    for (int i = 0; i < 10; i++) {
        printf("%d\\n", i);
    }
    return 0;
}
"""

# --------------------------
# HTML snippet (static)
# --------------------------
html_code = """
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <p>Hello World</p>
</body>
</html>
"""

def run_tests():
    test_cases = [
        # Interpreted
        ("Python Simple loop", python_simple_code, ".py"),
        ("Python Nested loops", python_nested_code, ".py"),
        ("JavaScript React snippet", js_react_code, ".js"),
        # Compiled
        ("C Simple loop", c_simple_code, ".c"),
        # Static
        ("HTML snippet", html_code, ".html"),
    ]

    for name, code, ext in test_cases:
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = grade_efficiency(code, tmp_path)
        print(f"Test: {name}")
        print(f"Time score: {result['time_score']}")
        print(f"Notes: {result['notes']}")
        print("-" * 50)

if __name__ == "__main__":
    run_tests()
