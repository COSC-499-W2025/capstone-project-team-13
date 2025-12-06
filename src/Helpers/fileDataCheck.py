import os
import re
from docx import Document
from PyPDF2 import PdfReader


# -------------------------------------------------------------
# Extract text from different file types
# -------------------------------------------------------------
def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return ""

    elif ext == ".docx":
        try:
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except:
            return ""

    elif ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text
        except:
            return ""

    return ""


# -------------------------------------------------------------
# Detect if extracted text is human-readable (not binary)
# -------------------------------------------------------------
def is_text_content(text: str, min_length: int = 20) -> bool:
    if not text or len(text.strip()) < min_length:
        return False

    printable = sum(c.isprintable() or c in "\n\r\t" for c in text)
    ratio = printable / len(text)
    return ratio > 0.85


# -------------------------------------------------------------
# Detect if text looks like code
# -------------------------------------------------------------
def looks_like_code(text: str) -> bool:
    lines = text.splitlines()

    patterns = [
        r"^\s*def\s+\w+\(",
        r"^\s*class\s+\w+",
        r"^\s*#include",
        r"^\s*function\s",
        r"^\s*import\s",
        r"^\s*(var|let|const)\s+\w+",
        r"^\s*public\s",
        r"^\s*<html",
        r"^\s*<!doctype",
        r"^\s*<\?xml",
        r"^\s*fn\s+\w+\(",
    ]
    regexes = [re.compile(p, re.I) for p in patterns]

    for line in lines:
        if any(r.search(line) for r in regexes):
            return True

    return False


# -------------------------------------------------------------
# MAIN classifier: "text", "code", or "media"
# -------------------------------------------------------------
def sniff_supertype(file_path: str) -> str:
    text = extract_text(file_path)

    if is_text_content(text):
        if looks_like_code(text):
            return "code"
        return "text"

    return "media"
