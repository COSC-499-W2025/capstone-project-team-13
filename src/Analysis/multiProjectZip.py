import sys
import os

# Add the parent directory of `src` to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import zipfile
import src
import os
from src.Extraction.zipHandler import extract_zip, validate_zip_file, ZipExtractionError

from datetime import datetime, timezone
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.textDocumentScanner import scan_text_document
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Databases.database import db_manager
from src.Analysis.file_hasher import compute_file_hash
from src.Analysis.projectcollabtype import identify_project_type

def parse_zip_and_identify_projects(zip_path, extract_to):
    """
    Parses a zip file, identifies projects within, and scans them independently.

    Args:
        zip_path (str): Path to the zip file.
        extract_to (str): Directory to extract the zip file to.

    Returns:
        list: A list of dictionaries containing project metadata.
    """
    if not zip_path.lower().endswith('.zip'):
        raise ValueError("File must have a .zip extension")

    # Extract the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    projects_metadata = []

    # Walk through extracted files and identify projects
    for root, dirs, files in os.walk(extract_to):
        if not files:
            continue

        # Use identify_project_type to determine the project type
        project_type = identify_project_type(root, files)

        if project_type == 'code':
            project_metadata = scan_coding_project(root)
            print(f"Debug: scan_coding_project returned {type(project_metadata)}: {project_metadata}")
        elif project_type == 'media':
            project_metadata = scan_media_project(root)
            print(f"Debug: scan_media_project returned {type(project_metadata)}: {project_metadata}")
        elif project_type == 'text':
            project_metadata = scan_text_document(root)
            print(f"Debug: scan_text_document returned {type(project_metadata)}: {project_metadata}")
        else:
            continue

        # Debugging: Print the type and content of project_metadata
        print(f"Debug: project_metadata type: {type(project_metadata)}, content: {project_metadata}")

        # Store project metadata
        project_metadata['project_path'] = root
        project_metadata['file_count'] = len(files)
        project_metadata['total_size'] = sum(os.path.getsize(os.path.join(root, file)) for file in files)
        project_metadata['date_scanned'] = datetime.now(timezone.utc)

        # Remove unsupported keys from project_metadata
        project_metadata.pop('document_types', None)

        # Add project to database
        project = db_manager.create_project(project_metadata)
        project_metadata['project_id'] = project.id

        # Ensure nltk data is downloaded without SSL verification
        import nltk
        import ssl
        try:
            _create_unverified_https_context = ssl._create_unverified_context
            ssl._create_default_https_context = _create_unverified_https_context
        except AttributeError:
            pass

        nltk.download('punkt')
        nltk.download('stopwords')

        # Add files to database
        for file in files:
            file_path = os.path.join(root, file)
            file_data = {
                'project_id': project.id,
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_type': os.path.splitext(file_path)[1],
                'file_size': os.path.getsize(file_path),
                'file_created': datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc),
                'file_modified': datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc),
                'file_hash': compute_file_hash(file_path)
            }
            db_manager.add_file_to_project(file_data)

        # Ensure project_metadata is a dictionary before appending
        if isinstance(project_metadata, dict):
            projects_metadata.append(project_metadata)
        else:
            print(f"⚠️ Skipping invalid project_metadata: {project_metadata}")

    return projects_metadata

if __name__ == "__main__":
    try:
        print("\nStarting manual test for parse_zip_and_identify_projects...\n")

        # Prompt user for input
        zip_path = input("Enter the path to the ZIP file: ").strip()

        # Validate the ZIP file
        if not validate_zip_file(zip_path):
            raise ZipExtractionError("Invalid ZIP file.")

        # Extract the ZIP file to a temporary directory
        print("Extracting ZIP file...")
        extract_to = extract_zip(zip_path)
        print(f"ZIP file extracted to: {extract_to}")

        # Run the function
        projects_metadata = parse_zip_and_identify_projects(zip_path, extract_to)
        print("\nTest completed. Projects metadata:")
        for project in projects_metadata:
            print(project)

        # Cleanup extracted files
        import shutil
        shutil.rmtree(extract_to)
        print("\nTemporary files cleaned up.")

    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")