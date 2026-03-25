import os
import re
from docx import Document
from PyPDF2 import PdfReader
from src.Settings.config import EXT_SUPERTYPES


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

    # 🔥 IMPORTANT: fallback for code files & other text-like files (.py, .js, .json, etc.)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except:
        return ""


def is_text_content(text: str, min_length: int = 20) -> bool:
    if not text or len(text.strip()) < min_length:
        return False

    printable = sum(c.isprintable() or c in "\n\r\t" for c in text)
    ratio = printable / len(text)
    return ratio > 0.85


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


def sniff_supertype(path: str) -> str:
    """
    Determine project type by counting file extensions (code, media, text) in a file or directory.
    Uses EXT_SUPERTYPES mapping from config.
    """
    type_counts = {'code': 0, 'media': 0, 'text': 0}
    skip_dirs = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env',
                 'dist', 'build', '.next', '.cache', 'vendor', '__MACOSX'}

    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            for filename in files:
                if filename.startswith('.'):
                    continue
                ext = os.path.splitext(filename)[1].lower()
                file_type = EXT_SUPERTYPES.get(ext)
                if file_type in type_counts:
                    type_counts[file_type] += 1
    else:
        ext = os.path.splitext(path)[1].lower()
        file_type = EXT_SUPERTYPES.get(ext)
        if file_type in type_counts:
            type_counts[file_type] += 1

    total_files = sum(type_counts.values())
    if total_files == 0:
        return 'media'  # fallback for unknown or binary files

    code_pct = type_counts['code'] / total_files
    media_pct = type_counts['media'] / total_files

    if code_pct > 0.7:
        return 'code'
    elif media_pct > 0.7:
        return 'media'
    elif code_pct > 0.2 and media_pct > 0.2:
        return 'mixed'
    elif type_counts['code'] > 0:
        return 'code'
    elif type_counts['media'] > 0:
        return 'media'
    elif type_counts['text'] > 0:
        return 'text'
    else:
        return 'media'
