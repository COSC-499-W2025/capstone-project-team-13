import os
import json
import csv
from src.Settings.config import EXT_SUPERTYPES
from docx import Document # for .docx
import PyPDF2 # for PDFs

class FileParseError(Exception):
    """Exception raised when file parsing fails"""
    pass

def parse_txt(file_path):
    """
    Parse plain text file
    
    Args:
        file_path (str): Path to text file
        
    Returns:
        dict: Parsed content with metadata
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'type': 'text',
            'content': content,
            'lines': len(content.splitlines()),
            'characters': len(content)
        }
    except Exception as e:
        raise FileParseError(f"Failed to parse text file: {str(e)}")

def parse_docx(file_path):
    """Parse Microsoft Word documents as TEXT."""
    try:
        doc = Document(file_path)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        words = full_text.split()
        lines = full_text.splitlines()
        return {
            "type": "text",
            "content": full_text,
            "line_count": len(lines),
            "word_count": len(words),
            "char_count": len(full_text),
        }
    except Exception as e:
        raise FileParseError(f"Failed to parse DOCX: {e}")
    
    
    
def parse_pdf(file_path):
    """Parse PDF files as TEXT (best-effort)."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

        lines = text.splitlines()
        words = text.split()

        return {
            "type": "text",
            "content": text,
            "line_count": len(lines),
            "word_count": len(words),
            "char_count": len(text),
        }
    except Exception as e:
        raise FileParseError(f"Failed to parse PDF: {e}")
    
def parse_json(file_path):
    """
    Parse JSON file
    
    Args:
        file_path (str): Path to JSON file
        
    Returns:
        dict: Parsed JSON content with metadata
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'type': 'json',
            'content': data,
            'size': len(json.dumps(data))
        }
    except json.JSONDecodeError as e:
        raise FileParseError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise FileParseError(f"Failed to parse JSON file: {str(e)}")

def parse_csv(file_path):
    """
    Parse CSV file
    
    Args:
        file_path (str): Path to CSV file
        
    Returns:
        dict: Parsed CSV content with metadata
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        return {
            'type': 'csv',
            'content': rows,
            'rows': len(rows),
            'columns': list(rows[0].keys()) if rows else []
        }
    except Exception as e:
        raise FileParseError(f"Failed to parse CSV file: {str(e)}")

def parse_code(file_path):
    """
    Parse Python file (as text with basic analysis)
    
    Args:
        file_path (str): Path to Python file
        
    Returns:
        dict: Parsed content with metadata
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        
        return {
            'type': 'python',
            'content': content,
            'lines': len(lines),
            'functions': sum(1 for line in lines if line.strip().startswith('def ')),
            'classes': sum(1 for line in lines if line.strip().startswith('class '))
        }
    except Exception as e:
        raise FileParseError(f"Failed to parse Python file: {str(e)}")

def parse_media(file_path):
    """Media is never parsed; only metadata returned."""
    size = os.path.getsize(file_path)
    return {
        "type": "media",
        "content": None,
        "size_bytes": size,
    }

def parse_file(file_path):
    """
    Main parser that routes to appropriate parser based on extension
    
    Args:
        file_path (str): Path to file
        
    Returns:
        dict: Parsed content with metadata
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    category = EXT_SUPERTYPES.get(ext)

    if category is None:
        raise FileParseError(f"No parser available for {ext} files")

    
    # --- TEXT ---
    if category == "text":
        if ext == ".docx":
            return parse_docx(file_path)
        if ext == ".pdf":
            return parse_pdf(file_path)
        return parse_txt(file_path)

    # --- CODE ---
    if category == "code":
        return parse_code(file_path)
    
    # JSON
    if category == "json":
        return parse_json(file_path)

    # CSV
    if category == "csv":
        return parse_csv(file_path)
   
    # --- MEDIA ---
    if category == "media":
        return parse_media(file_path)
    

        
    
    raise FileParseError(f"Unknown category '{category}' for extension {ext}")
