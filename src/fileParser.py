import os
import json
import csv

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

def parse_py(file_path):
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
    
    parsers = {
        '.txt': parse_txt,
        '.json': parse_json,
        '.csv': parse_csv,
        '.py': parse_py
    }
    
    if ext not in parsers:
        raise FileParseError(f"No parser available for {ext} files")
    
    return parsers[ext](file_path)
