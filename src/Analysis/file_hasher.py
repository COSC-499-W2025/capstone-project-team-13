import hashlib
from pathlib import Path

def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file for duplicate detection
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"Error hashing file {file_path}: {e}")
        return ""