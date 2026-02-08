import sys
import os
import shutil

# Ensure the `src` directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import os
import zipfile
from src.Settings.config import EXT_SUPERTYPES
from src.Databases.database import db_manager
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Analysis.textDocumentScanner import scan_text_document

def splitZipFile(zip_path):
    """
    Given a zip folder, identifies distinct projects within it.
    Ignores system files like __MACOSX.

    Args:
        zip_path (str): Path to the zip file.

    Returns:
        list: List of project names.
    """
    projects = set()

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            # Ignore system files like __MACOSX
            if file.startswith('__MACOSX') or file.startswith('.'): 
                continue

            # Extract the top-level folder name (project name)
            parts = file.split('/')
            if len(parts) > 1:
                projects.add(parts[0])

    return list(projects)

def processZipFile(zipFilePath):
    """
    Process a zip file to identify and categorize top-level projects.
    Use appropriate scanners to analyze and store projects in the database.
    """
    import zipfile
    import os
    import shutil

    # Extract the zip file to a temporary directory
    tempDir = "temp_extracted_zip"
    if os.path.exists(tempDir):
        shutil.rmtree(tempDir)
    os.makedirs(tempDir)

    with zipfile.ZipFile(zipFilePath, 'r') as zip_ref:
        zip_ref.extractall(tempDir)

    # Analyze only top-level directories within the extracted zip file
    extracted_root = os.path.join(tempDir, os.listdir(tempDir)[0])
    results = []
    for item in os.listdir(extracted_root):
        itemPath = os.path.join(extracted_root, item)
        if os.path.isdir(itemPath):
            project_info = identifyProjectType(itemPath)
            project_type = project_info['type']

            # Use the appropriate scanner based on project type
            if project_type == 'code':
                project_id = scan_coding_project(itemPath)
            elif project_type == 'media':
                project_id = scan_media_project(itemPath)
            elif project_type == 'text':
                project_id = scan_text_document(itemPath)
            else:
                project_id = scan_text_document(itemPath)  # Default to text scanner

            results.append({
                "name": item,  # Changed key to match handle_multi_zip
                "type": project_type,
                "file_count": len(os.listdir(itemPath)),  # Added file count
                "path": itemPath,  # Added project path
                "details": project_info['details'],
                "database_id": project_id  # Changed key to snake_case for consistency
            })

    # Clean up temporary directory
    shutil.rmtree(tempDir)

    return results

def identifyProjectType(folder_path):
    """
    Identifies the type of a project based on its contents.

    Args:
        folder_path (str): Path to the folder or project.

    Returns:
        dict: {
            'type': 'code', 'media', 'mixed', or 'unknown',
            'code_count': int,
            'media_count': int,
            'text_count': int,
            'details': str (description)
        }
    """
    type_counts = {'code': 0, 'media': 0, 'text': 0}
    skip_dirs = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env', 
                 'dist', 'build', '.next', '.cache', 'vendor', '__MACOSX'}

    # Scan folder and count file types
    for root, dirs, files in os.walk(folder_path):
        # Remove skip directories from dirs list
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

        for filename in files:
            if filename.startswith('.'):
                continue

            ext = os.path.splitext(filename)[1].lower()
            file_type = EXT_SUPERTYPES.get(ext)

            if file_type in type_counts:
                type_counts[file_type] += 1

    total_files = sum(type_counts.values())

    if total_files == 0:
        return {
            'type': 'unknown',
            'code_count': 0,
            'media_count': 0,
            'text_count': 0,
            'details': 'No recognizable files found'
        }

    # Calculate percentages
    code_pct = type_counts['code'] / total_files
    media_pct = type_counts['media'] / total_files

    # Determine project type
    if code_pct > 0.7:  # More than 70% code files
        project_type = 'code'
        details = f"Primarily code ({type_counts['code']} code files)"
    elif media_pct > 0.7:  # More than 70% media files
        project_type = 'media'
        details = f"Primarily media ({type_counts['media']} media files)"
    elif code_pct > 0.2 and media_pct > 0.2:  # Both significant
        project_type = 'mixed'
        details = f"Mixed project ({type_counts['code']} code, {type_counts['media']} media files)"
    elif type_counts['code'] > 0:  # Any code files present
        project_type = 'code'
        details = f"Small code project ({type_counts['code']} code files)"
    elif type_counts['media'] > 0:  # Any media files present
        project_type = 'media'
        details = f"Small media project ({type_counts['media']} media files)"
    else:
        project_type = 'unknown'
        details = f"Unrecognized project type ({total_files} files)"

    return {
        'type': project_type,
        'code_count': type_counts['code'],
        'media_count': type_counts['media'],
        'text_count': type_counts['text'],
        'details': details
    }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the processZipFile function manually.")
    parser.add_argument("zip_path", type=str, help="Path to the zip file to process.")
    args = parser.parse_args()

    if not os.path.exists(args.zip_path):
        print(f"Error: The file {args.zip_path} does not exist.")
    elif not zipfile.is_zipfile(args.zip_path):
        print(f"Error: The file {args.zip_path} is not a valid zip file.")
    else:
        print("Processing zip file...")
        results = processZipFile(args.zip_path)
        print("Results:")
        for project in results:
            print(f"Project Name: {project['name']}")
            print(f"Type: {project['type']}")
            print(f"Details: {project['details']}")
            print("-")