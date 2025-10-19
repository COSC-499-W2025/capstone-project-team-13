import os
import zipfile
import tempfile
from fileFormatCheck import check_file_format, InvalidFileFormatError

class ZipExtractionError(Exception):
    """Exception raised when zip extraction fails"""
    pass

def validate_zip_file(zip_path):
    """
    Validate that the file is a proper zip file
    
    Args:
        zip_path (str): Path to the zip file
        
    Returns:
        bool: True if valid zip file
        
    Raises:
        InvalidFileFormatError: If file format is wrong
        ZipExtractionError: If zip file is corrupted
    """
    # check format first
    check_file_format(zip_path)
    
    # check if its actually a valid zip
    if not zipfile.is_zipfile(zip_path):
        raise ZipExtractionError(f"File {zip_path} is not a valid ZIP file")
    
    return True

def extract_zip(zip_path, extract_to=None):
    """
    Extract zip file to a directory
    
    Args:
        zip_path (str): Path to zip file
        extract_to (str): Directory to extract to. If None, creates temp directory
        
    Returns:
        str: Path to extraction directory
        
    Raises:
        ZipExtractionError: If extraction fails
    """
    # validate first
    validate_zip_file(zip_path)
    
    # create extraction directory if needed
    if extract_to is None:
        extract_to = tempfile.mkdtemp(prefix='extracted_')
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return extract_to
    except Exception as e:
        raise ZipExtractionError(f"Failed to extract zip: {str(e)}")

def get_zip_contents(zip_path):
    """
    Get list of files in zip without extracting
    
    Args:
        zip_path (str): Path to zip file
        
    Returns:
        list: List of file paths in the zip
    """
    validate_zip_file(zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        return zip_ref.namelist()

def count_files_in_zip(zip_path):
    """
    Count total files in zip
    
    Args:
        zip_path (str): Path to zip file
        
    Returns:
        int: Number of files in zip
    """
    contents = get_zip_contents(zip_path)
    # filter out directories
    files = [f for f in contents if not f.endswith('/')]
    return len(files)