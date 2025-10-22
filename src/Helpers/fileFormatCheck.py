import os
from src.Settings.config import ALLOWED_FORMATS

class InvalidFileFormatError(Exception):
    """Custom exception for invalid file formats."""
    pass

def check_file_format(file_path):
    """
    Check if the file has a supported format    
    Args:
        file_path (str): The path to the file to be checked.

    Returns:
        bool: True if the file is in a supported format, False otherwise.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in ALLOWED_FORMATS:
        raise InvalidFileFormatError(f"'{ext}' not supported. Allowed formats: {ALLOWED_FORMATS}")
        
    return True

