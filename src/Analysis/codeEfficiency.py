# src/Analysis/code_efficiency.py

import ast
import subprocess
import tempfile
import time
import os
import re
from typing import Dict, Optional
from Analysis.codeIdentifier import identify_language_and_framework

def grade_efficiency(code: str, file_path: str) -> Dict[str, Optional[float]]:
    """
    Grades a piece of code for time and space complexity.
    Returns a dictionary with:
        - 'time_score': 0-100
        - 'space_score': 0-100
        - 'notes': optional textual notes about detected issues
    """
    # Identify language using the existing module
    result = identify_language_and_framework(file_path)

    # Handle error dicts
    if isinstance(result, dict):
        notes = [result.get("error", "Unknown error")]
        return {"time_score": None, "space_score": None, "notes": notes}

    # Unpack tuple safely
    language, framework = result
        
    if not language:
        return {"time_score": None, "space_score": None, "notes": ["Unknown language"]}

    time_score = None
    space_score = None
    result = timeScore(code, file_path)
    time_score = result.get("time_score")
    space_score = 80  # placeholder
    notes = result.get("notes", [])

    return {
        "time_score": time_score,
        "space_score": space_score,
        "notes": notes
    }

def timeScore(code: str, file_path: str) -> dict:
    language, _ = identify_language_and_framework(file_path)

    if language in ["Python", "Ruby", "PHP", "R", "JavaScript", "TypeScript"]:
        return timeScore_interpreted(code, file_path)

    elif language in ["C", "C++", "Java", "Go", "Rust", "Kotlin", "Swift", "C#"]:
        return timeScore_compiled(code, file_path)

    elif language in ["HTML", "CSS", "SQL"]:
        return timeScore_static(code, file_path)

    else:
        return {"time_score": None, "notes": ["Unknown language"]}


def timeScore_interpreted(code: str, file_path: str, max_runtime: float = 2.0) -> Dict[str, Optional[float]]:
    """
    Grades time efficiency for interpreted languages (Python, JS, Ruby, etc.)
    Combines static analysis with optional runtime measurement.
    Returns a dict with 'time_score' (0-100) and 'notes'.
    """

    language, _ = identify_language_and_framework(file_path)
    notes = []

    # -----------------------
    # STATIC ANALYSIS (AST)
    # -----------------------
    static_score = 100

    if language == "Python":
        try:
            tree = ast.parse(code)

            # Count nested loops
            class LoopVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.max_depth = 0
                    self.stack = 0

                def visit_For(self, node):
                    self.stack += 1
                    self.max_depth = max(self.max_depth, self.stack)
                    self.generic_visit(node)
                    self.stack -= 1

                visit_While = visit_For

            loops = LoopVisitor()
            loops.visit(tree)

            if loops.max_depth >= 3:
                static_score -= 30
                notes.append("Deeply nested loops (3+)")

            elif loops.max_depth == 2:
                static_score -= 15
                notes.append("Nested loops (2 deep)")

            # Count recursive functions
            class RecursionVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.recursive_count = 0

                def visit_FunctionDef(self, node):
                    func_name = node.name
                    for n in ast.walk(node):
                        if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == func_name:
                            self.recursive_count += 1
                    self.generic_visit(node)

            rec = RecursionVisitor()
            rec.visit(tree)

            if rec.recursive_count > 0:
                static_score -= min(20, rec.recursive_count * 5)
                notes.append(f"{rec.recursive_count} recursive function(s) detected")

        except Exception as e:
            notes.append(f"AST parsing failed: {e}")
            static_score -= 20

    # -----------------------
    # RUNTIME MEASUREMENT
    # -----------------------
    runtime_score = 100

    if language == "Python":
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            start = time.time()
            subprocess.run(["python", tmp_path], timeout=max_runtime, capture_output=True)
            elapsed = time.time() - start

            runtime_score -= min(50, (elapsed / max_runtime) * 50)
            notes.append(f"Executed Python code in {elapsed:.2f}s")

        except subprocess.TimeoutExpired:
            runtime_score = 10
            notes.append("Execution timed out")

        except Exception as e:
            runtime_score = 50
            notes.append(f"Execution failed: {e}")

    # -----------------------
    # FINAL SCORE
    # -----------------------
    final_score = max(0, min(100, (static_score + runtime_score) / 2))
    return {"time_score": final_score, "notes": notes}

def timeScore_compiled(code: str, file_path: str, max_runtime: float = 2.0) -> Dict[str, Optional[float]]:
    """
    Grades time efficiency for compiled languages (C, C++, Java, Rust, Go, etc.)
    Combines simple static checks with runtime measurement.
    Returns a dict with 'time_score' (0-100) and 'notes'.
    """
    language, _ = identify_language_and_framework(file_path)
    notes = []
    static_score = 100
    runtime_score = 100

    # -----------------------
    # STATIC ANALYSIS (approximate via regex)
    # -----------------------
    try:
        import re
        # Count nested loops roughly
        loop_keywords = {
            "C": r"\b(for|while)\b",
            "C++": r"\b(for|while)\b",
            "Java": r"\b(for|while)\b",
            "C#": r"\b(for|while|foreach)\b",
            "Rust": r"\b(loop|for|while)\b",
            "Go": r"\b(for)\b",
            "Kotlin": r"\b(for|while)\b",
            "Swift": r"\b(for|while)\b",
        }
        pattern = loop_keywords.get(language)
        if pattern:
            loops = re.findall(pattern, code)
            if len(loops) >= 5:
                static_score -= 30
                notes.append("Many loops detected (5+)")
            elif len(loops) >= 3:
                static_score -= 15
                notes.append("Some loops detected (3+)")

        # Simple recursion detection: function calls its own name
        func_defs = re.findall(r'\b(?:def|func|void|int|double|char)\s+(\w+)\s*\(', code)
        recursion_count = 0
        for f in func_defs:
            if re.search(rf'\b{f}\s*\(', code):
                recursion_count += 1
        if recursion_count > 0:
            static_score -= min(20, recursion_count * 5)
            notes.append(f"{recursion_count} recursive function(s) detected")

    except Exception as e:
        notes.append(f"Static analysis failed: {e}")
        static_score -= 20

    # -----------------------
    # RUNTIME MEASUREMENT
    # -----------------------
    try:
        import shutil
        import platform

        # Temporary directory to hold files
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = os.path.join(tmp_dir, os.path.basename(file_path))

            # Determine file extension
            _, ext = os.path.splitext(file_path)
            with open(tmp_file, "w") as f:
                f.write(code)

            run_cmd = None

            if ext in [".c"]:
                exe_file = os.path.join(tmp_dir, "program")
                subprocess.run(["gcc", tmp_file, "-o", exe_file], check=True)
                run_cmd = [exe_file]

            elif ext in [".cpp"]:
                exe_file = os.path.join(tmp_dir, "program")
                subprocess.run(["g++", tmp_file, "-o", exe_file], check=True)
                run_cmd = [exe_file]

            elif ext in [".java"]:
                subprocess.run(["javac", tmp_file], check=True)
                class_file = os.path.join(tmp_dir, os.path.splitext(os.path.basename(file_path))[0])
                run_cmd = ["java", "-cp", tmp_dir, class_file]

            elif ext in [".rs"]:
                exe_file = os.path.join(tmp_dir, "program")
                subprocess.run(["rustc", tmp_file, "-o", exe_file], check=True)
                run_cmd = [exe_file]

            elif ext in [".go"]:
                exe_file = os.path.join(tmp_dir, "program")
                subprocess.run(["go", "build", "-o", exe_file, tmp_file], check=True)
                run_cmd = [exe_file]

            elif ext in [".cs"]:
                exe_file = os.path.join(tmp_dir, "program.exe")
                subprocess.run(["csc", tmp_file], check=True)  # Windows only
                run_cmd = [exe_file]

            elif ext in [".kt"]:
                exe_file = os.path.join(tmp_dir, "program.jar")
                subprocess.run(["kotlinc", tmp_file, "-include-runtime", "-d", exe_file], check=True)
                run_cmd = ["java", "-jar", exe_file]

            elif ext in [".swift"]:
                exe_file = os.path.join(tmp_dir, "program")
                subprocess.run(["swiftc", tmp_file, "-o", exe_file], check=True)
                run_cmd = [exe_file]

            # Run the compiled binary
            if run_cmd:
                start = time.time()
                subprocess.run(run_cmd, timeout=max_runtime, capture_output=True)
                elapsed = time.time() - start
                runtime_score -= min(50, (elapsed / max_runtime) * 50)
                notes.append(f"Executed {language} code in {elapsed:.2f}s")
            else:
                notes.append(f"No runtime measurement implemented for {language}")

    except subprocess.TimeoutExpired:
        runtime_score = 10
        notes.append("Execution timed out")
    except subprocess.CalledProcessError as e:
        runtime_score = 50
        notes.append(f"Compilation or execution failed: {e}")
    except Exception as e:
        runtime_score = 50
        notes.append(f"Runtime measurement failed: {e}")

    # -----------------------
    # FINAL SCORE
    # -----------------------
    final_score = max(0, min(100, (static_score + runtime_score) / 2))
    return {"time_score": final_score, "notes": notes}

def timeScore_interpreted(code: str, file_path: str, max_runtime: float = 2.0) -> Dict[str, Optional[float]]:
    """
    Grades time efficiency for interpreted languages (Python, JS, TS, Ruby, etc.)
    Combines static analysis with optional runtime measurement.
    Returns a dict with 'time_score' (0-100) and 'notes'.
    """

    language, _ = identify_language_and_framework(file_path)
    notes = []

    # -----------------------
    # STATIC ANALYSIS (Python only)
    # -----------------------
    static_score = 100
    if language == "Python":
        try:
            tree = ast.parse(code)

            # Count nested loops
            class LoopVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.max_depth = 0
                    self.stack = 0

                def visit_For(self, node):
                    self.stack += 1
                    self.max_depth = max(self.max_depth, self.stack)
                    self.generic_visit(node)
                    self.stack -= 1

                visit_While = visit_For

            loops = LoopVisitor()
            loops.visit(tree)

            if loops.max_depth >= 3:
                static_score -= 30
                notes.append("Deeply nested loops (3+)")
            elif loops.max_depth == 2:
                static_score -= 15
                notes.append("Nested loops (2 deep)")

            # Count recursive functions
            class RecursionVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.recursive_count = 0

                def visit_FunctionDef(self, node):
                    func_name = node.name
                    for n in ast.walk(node):
                        if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == func_name:
                            self.recursive_count += 1
                    self.generic_visit(node)

            rec = RecursionVisitor()
            rec.visit(tree)
            if rec.recursive_count > 0:
                static_score -= min(20, rec.recursive_count * 5)
                notes.append(f"{rec.recursive_count} recursive function(s) detected")

        except Exception as e:
            notes.append(f"AST parsing failed: {e}")
            static_score -= 20

    # -----------------------
    # RUNTIME MEASUREMENT
    # -----------------------
    runtime_score = 100
    try:
        # Determine command based on language
        if language == "Python":
            cmd = ["python", file_path]
        elif language in ["JavaScript", "TypeScript"]:
            cmd = ["node", file_path]
        else:
            # Other interpreted languages could be added here
            cmd = None

        if cmd:
            start = time.time()
            subprocess.run(cmd, timeout=max_runtime, capture_output=True)
            elapsed = time.time() - start
            runtime_score -= min(50, (elapsed / max_runtime) * 50)
            notes.append(f"Executed {language} code in {elapsed:.2f}s")
        else:
            notes.append(f"No runtime execution implemented for {language}")

    except subprocess.TimeoutExpired:
        runtime_score = 10
        notes.append("Execution timed out")

    except Exception as e:
        runtime_score = 50
        notes.append(f"Execution failed: {e}")

    # -----------------------
    # FINAL SCORE
    # -----------------------
    final_score = max(0, min(100, (static_score + runtime_score) / 2))
    return {"time_score": final_score, "notes": notes}


def timeScore_static(code: str, file_path: str) -> Dict[str, Optional[float]]:
    """
    Grades time efficiency for static languages (HTML, CSS, SQL).
    Mostly placeholder since static files don't execute.
    Returns a dict with 'time_score' (0-100) and 'notes'.
    """
    language, _ = identify_language_and_framework(file_path)
    notes = []

    static_score = 100

    try:
        # File size penalty: larger static files could be slower to process
        num_lines = len(code.splitlines())
        if num_lines > 500:
            static_score -= 20
            notes.append(f"Large file ({num_lines} lines), may impact performance")
        elif num_lines > 200:
            static_score -= 10
            notes.append(f"Moderately large file ({num_lines} lines)")

        # Simple complexity check (HTML: many tags, CSS: many selectors, SQL: many statements)
        if language == "HTML":
            num_tags = len(re.findall(r"<\w+", code))
            if num_tags > 100:
                static_score -= 20
                notes.append(f"Many HTML tags ({num_tags})")
            elif num_tags > 50:
                static_score -= 10
                notes.append(f"Moderate number of HTML tags ({num_tags})")

        elif language == "CSS":
            num_selectors = len(re.findall(r"{", code))
            if num_selectors > 100:
                static_score -= 20
                notes.append(f"Many CSS selectors ({num_selectors})")
            elif num_selectors > 50:
                static_score -= 10
                notes.append(f"Moderate number of CSS selectors ({num_selectors})")

        elif language == "SQL":
            num_statements = len(re.findall(r";", code))
            if num_statements > 50:
                static_score -= 20
                notes.append(f"Many SQL statements ({num_statements})")
            elif num_statements > 20:
                static_score -= 10
                notes.append(f"Moderate number of SQL statements ({num_statements})")

    except Exception as e:
        notes.append(f"Static analysis failed: {e}")
        static_score -= 20

    final_score = max(0, min(100, static_score))
    notes.append(f"{language} static analysis applied")
    return {"time_score": final_score, "notes": notes}
