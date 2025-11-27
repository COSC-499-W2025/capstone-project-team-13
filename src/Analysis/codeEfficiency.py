# src/Analysis/code_efficiency.py

import ast
import re
from typing import Dict, Optional
from .codeIdentifier import identify_language_and_framework

# ===============================
# Main grading function
# ===============================
def grade_efficiency(code: str, file_path: str) -> Dict[str, Optional[float]]:
    """
    Grades a piece of code for time and space complexity.
    Returns a dictionary with:
        - time_score: 0-100
        - space_score: 0-100
        - efficiency_score: weighted combination
        - max_loop_depth: maximum nesting depth of loops
        - total_loops: total number of loops
        - notes: textual notes about detected issues
    """
    result = identify_language_and_framework(file_path)
    if isinstance(result, dict):
        notes = [result.get("error", "Unknown error")]
        return {"time_score": None, "space_score": None, "efficiency_score": None,
                "max_loop_depth": None, "total_loops": None, "notes": notes}

    language, framework = result
    if not language:
        return {"time_score": None, "space_score": None, "efficiency_score": None,
                "max_loop_depth": None, "total_loops": None, "notes": ["Unknown language"]}

    time_result = timeScore(code, file_path)
    space_result = spaceScore(code, file_path)

    time_score = time_result.get("time_score", 0)
    space_score = space_result.get("space_score", 0)
    max_loop_depth = time_result.get("max_loop_depth", 0)
    total_loops = time_result.get("total_loops", 0)
    notes = time_result.get("notes", []) + space_result.get("notes", [])

    efficiency_score = (time_score * 0.65 + space_score * 0.35) if time_score is not None and space_score is not None else None

    return {
        "time_score": time_score,
        "space_score": space_score,
        "efficiency_score": efficiency_score,
        "max_loop_depth": max_loop_depth,
        "total_loops": total_loops,
        "notes": notes
    }

# ===============================
# Time Score Dispatcher
# ===============================
def timeScore(code: str, file_path: str) -> dict:
    language, _ = identify_language_and_framework(file_path)
    if language in ["Python", "Ruby", "PHP", "R", "JavaScript", "TypeScript"]:
        return timeScore_interpreted(code, file_path)
    elif language in ["C", "C++", "Java", "Go", "Rust", "Kotlin", "Swift", "C#"]:
        return timeScore_compiled(code, file_path)
    elif language in ["HTML", "CSS", "SQL"]:
        return timeScore_static(code, file_path)
    else:
        return {"time_score": 0, "notes": ["Unknown language"], "max_loop_depth": 0, "total_loops": 0}

# ===============================
# Space Score Dispatcher
# ===============================
def spaceScore(code: str, file_path: str) -> dict:
    language, _ = identify_language_and_framework(file_path)
    if language in ["Python", "Ruby", "PHP", "R", "JavaScript", "TypeScript"]:
        return spaceScore_interpreted(code, file_path)
    elif language in ["C", "C++", "Java", "Go", "Rust", "Kotlin", "Swift", "C#"]:
        return spaceScore_compiled(code, file_path)
    elif language in ["HTML", "CSS", "SQL"]:
        return spaceScore_static(code, file_path)
    else:
        return {"space_score": 0, "notes": ["Unknown language"], "max_loop_depth": 0, "total_loops": 0}

# ===============================
# Utility: decaying penalty
# ===============================
def decaying_penalty(base: float, count: int, line_count: int = 100, decay: float = 0.75, ref_lines: int = 200) -> float:
    """
    Apply decaying penalty for 'count' occurrences.
    Scale penalty inversely by line count, but gently.
    """
    scale_factor = (ref_lines / max(line_count, ref_lines)) ** 0.5
    penalty = sum(base * (decay ** n) * scale_factor for n in range(count))
    return penalty

# ===============================
# Interpreted Language Scores
# ===============================
def timeScore_interpreted(code: str, file_path: str) -> dict:
    notes = []
    score = 100
    file_lines = len(code.splitlines())
    max_depth = 0
    total_loops = 0

    # Time-focused base penalties
    base_loop_penalty = max(3, min(20, 0.1 * file_lines))
    base_nested_penalty = max(7, min(30, 0.2 * file_lines))
    base_recursion_penalty = max(10, min(35, 0.25 * file_lines))

    try:
        tree = ast.parse(code)

        # Loop detection
        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
                self.total_loops = 0
            def visit_For(self, node): self._enter_loop(node)
            def visit_While(self, node): self._enter_loop(node)
            def _enter_loop(self, node):
                self.total_loops += 1
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

        lv = LoopVisitor()
        lv.visit(tree)
        total_loops = lv.total_loops
        max_depth = lv.max_depth

        # Recursion detection
        class RecVisitor(ast.NodeVisitor):
            def __init__(self):
                self.count = 0
            def visit_FunctionDef(self, node):
                func_name = node.name
                for n in ast.walk(node):
                    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == func_name:
                        self.count += 1
                self.generic_visit(node)

        rv = RecVisitor()
        rv.visit(tree)

        # Apply decaying penalties
        score -= decaying_penalty(base_loop_penalty, total_loops, file_lines)
        if max_depth > 1:
            score -= decaying_penalty(base_nested_penalty, max_depth - 1, file_lines)
        score -= decaying_penalty(base_recursion_penalty, rv.count, file_lines)

        if rv.count > 0:
            notes.append(f"{rv.count} recursive function(s) detected")

    except Exception as e:
        score -= 30
        notes.append(f"AST parse failed: {e}")

    notes.append(f"Detected {total_loops} loops with depth {max_depth}")
    score = max(0, min(100, score))
    return {"time_score": score, "notes": notes, "max_loop_depth": max_depth, "total_loops": total_loops}

def spaceScore_interpreted(code: str, file_path: str) -> dict:
    notes = []
    score = 100
    file_lines = len(code.splitlines())
    max_depth = 0
    total_loops = 0

    # Space-focused base penalties
    base_loop_penalty = max(5, min(25, 0.15 * file_lines))
    base_nested_penalty = max(3, min(20, 0.1 * file_lines))
    base_recursion_penalty = max(5, min(25, 0.2 * file_lines))

    try:
        tree = ast.parse(code)

        # Loop detection
        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
                self.total_loops = 0
            def visit_For(self, node): self._enter_loop(node)
            def visit_While(self, node): self._enter_loop(node)
            def _enter_loop(self, node):
                self.total_loops += 1
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

        lv = LoopVisitor()
        lv.visit(tree)
        total_loops = lv.total_loops
        max_depth = lv.max_depth

        # Recursion detection
        class RecVisitor(ast.NodeVisitor):
            def __init__(self):
                self.count = 0
            def visit_FunctionDef(self, node):
                func_name = node.name
                for n in ast.walk(node):
                    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == func_name:
                        self.count += 1
                self.generic_visit(node)

        rv = RecVisitor()
        rv.visit(tree)

        # Apply decaying penalties
        score -= decaying_penalty(base_loop_penalty, total_loops, file_lines)
        if max_depth > 1:
            score -= decaying_penalty(base_nested_penalty, max_depth - 1, file_lines)
        score -= decaying_penalty(base_recursion_penalty, rv.count, file_lines)

        if rv.count > 0:
            notes.append(f"{rv.count} recursive function(s) detected")

    except Exception as e:
        score -= 30
        notes.append(f"AST parse failed: {e}")

    notes.append(f"Detected {total_loops} loops with depth {max_depth}")
    score = max(0, min(100, score))
    return {"space_score": score, "notes": notes}

# ===============================
# Compiled Language Scores
# ===============================
def timeScore_compiled(code: str, file_path: str) -> dict:
    notes = []
    score = 100
    max_depth = 0
    total_loops = 0

    loop_patterns = [r"\bfor\b", r"\bwhile\b", r"\bdo\b", r"\bforeach\b"]
    for pat in loop_patterns:
        total_loops += len(re.findall(pat, code))

    depth = 0
    for line in code.splitlines():
        if any(re.search(pat, line) for pat in loop_patterns):
            depth += 1
            max_depth = max(max_depth, depth)
        depth = max(0, depth - line.count("}"))

    file_lines = len(code.splitlines())
    base_loop_penalty = max(5, min(25, 0.15 * file_lines))
    base_nested_penalty = max(5, min(30, 0.2 * file_lines))
    score -= decaying_penalty(base_loop_penalty, total_loops)
    if max_depth > 1:
        score -= decaying_penalty(base_nested_penalty, max_depth - 1)

    notes.append(f"Detected {total_loops} loops with depth {max_depth}")
    score = max(0, min(100, score))
    return {"time_score": score, "notes": notes, "max_loop_depth": max_depth, "total_loops": total_loops}

def spaceScore_compiled(code: str, file_path: str) -> dict:
    notes = []
    score = 100
    max_depth = 0
    total_loops = 0

    loop_patterns = [r"\bfor\b", r"\bwhile\b", r"\bdo\b", r"\bforeach\b"]
    for pat in loop_patterns:
        total_loops += len(re.findall(pat, code))

    depth = 0
    for line in code.splitlines():
        if any(re.search(pat, line) for pat in loop_patterns):
            depth += 1
            max_depth = max(max_depth, depth)
        depth = max(0, depth - line.count("}"))

    file_lines = len(code.splitlines())
    base_loop_penalty = max(5, min(25, 0.15 * file_lines))
    base_nested_penalty = max(3, min(20, 0.1 * file_lines))
    score -= decaying_penalty(base_loop_penalty, total_loops)
    if max_depth > 1:
        score -= decaying_penalty(base_nested_penalty, max_depth - 1)

    score = max(0, min(100, score))
    return {"space_score": score, "notes": notes}

# ===============================
# Static Language Scores
# ===============================
def timeScore_static(code: str, file_path: str) -> dict:
    notes = []
    score = 100
    lines = len(code.splitlines())
    if lines > 500:
        score -= 40
    elif lines > 200:
        score -= 20
    notes.append("Static analysis applied")
    score = max(0, min(100, score))
    return {"time_score": score, "notes": notes, "max_loop_depth": 0, "total_loops": 0}

def spaceScore_static(code: str, file_path: str) -> dict:
    notes = []
    score = 100
    size = len(code.encode("utf-8"))
    if size > 200_000:
        score -= 30
    elif size > 100_000:
        score -= 15
    notes.append("Static analysis applied")
    score = max(0, min(100, score))
    return {"space_score": score, "notes": notes}
