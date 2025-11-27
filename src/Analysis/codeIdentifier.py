import os
import re

# We are able to add more, just basic for now
LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".m": "Objective-C",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL"
}

FRAMEWORKS = {
    "Python": [
        ("Django", r"from\s+django"),
        ("Flask", r"from\s+flask|import\s+Flask"),
        ("FastAPI", r"from\s+fastapi"),
    ],
    "JavaScript": [
        ("React", r"from\s+['\"]react['\"]"),
        ("Next.js", r"from\s+['\"]next"),
        ("Vue", r"from\s+['\"]vue['\"]"),
        ("Express", r"require\(['\"]express['\"]"),
    ],
    "TypeScript": [
        ("Angular", r"from\s+['\"]@angular"),
    ],
}

def identify_language_and_framework(file_path: str):
    """
    Identifies the programming language and framework used in the provided code file.
    Args:
        file_path (str): Path to the code file
    Returns:
        tuple: (language, list of frameworks detected) or dict with error
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    _, ext = os.path.splitext(file_path)
    
    if ext not in LANGUAGE_BY_EXTENSION:
        return (None, None)
    
    language = LANGUAGE_BY_EXTENSION[ext]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"error": str(e)}
    
    detected_frameworks = []

    # Only check frameworks if the language is in FRAMEWORKS
    if language in FRAMEWORKS:
        for frameworkFound, pattern in FRAMEWORKS[language]:
            if re.search(pattern, content):
                detected_frameworks.append(frameworkFound)
                break

    return (language, detected_frameworks)
