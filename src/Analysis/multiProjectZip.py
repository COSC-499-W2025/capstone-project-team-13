import os
import zipfile
from datetime import datetime, timezone
from src.Analysis.codingProjectScanner import CodingProjectScanner
from src.Analysis.mediaProjectScanner import MediaProjectScanner
from src.Analysis.textDocumentScanner import TextDocumentScanner
from src.Databases.database import create_project, add_file_to_project, add_keyword
from src.Analysis.file_hasher import compute_file_hash

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

        # Determine project type
        has_code = any(file.endswith('.py') for file in files)
        has_media = any(file.lower().endswith(('.jpg', '.png', '.mp4')) for file in files)
        has_text = any(file.lower().endswith(('.txt', '.md', '.docx')) for file in files)

        if has_code:
            project_type = 'code'
            scanner = CodingProjectScanner(root)
            scanner._find_code_files()
            scanner._detect_languages_and_frameworks()
            project_metadata = {
                'project_type': project_type,
                'languages': list(scanner.languages),
                'frameworks': list(scanner.frameworks),
                'files': scanner.code_files
            }
        elif has_media:
            project_type = 'media'
            scanner = MediaProjectScanner(root)
            scanner._find_files()
            scanner._analyze_media()
            project_metadata = {
                'project_type': project_type,
                'software_used': list(scanner.software_used),
                'skills_detected': list(scanner.skills_detected),
                'files': scanner.media_files
            }
        elif has_text:
            project_type = 'text'
            scanner = TextDocumentScanner(root)
            scanner._find_text_files()
            scanner._detect_document_types()
            project_metadata = {
                'project_type': project_type,
                'document_types': list(scanner.document_types),
                'files': scanner.text_files
            }
        else:
            continue

        # Store project metadata
        project_metadata['project_path'] = root
        project_metadata['file_count'] = len(files)
        project_metadata['total_size'] = sum(os.path.getsize(os.path.join(root, file)) for file in files)
        project_metadata['date_scanned'] = datetime.now(timezone.utc)

        # Add project to database
        project = create_project(project_metadata)
        project_metadata['project_id'] = project.id

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
            add_file_to_project(file_data)

        # Add keywords to database (if any)
        if hasattr(scanner, 'all_keywords') and scanner.all_keywords:
            for keyword, score in scanner.all_keywords:
                add_keyword({
                    'project_id': project.id,
                    'keyword': keyword,
                    'score': score,
                    'category': project_type
                })

        projects_metadata.append(project_metadata)

    return projects_metadata

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the parse_zip_and_identify_projects function.")
    parser.add_argument("zip_path", type=str, help="Path to the zip file to parse.")
    parser.add_argument("extract_to", type=str, help="Directory to extract the zip file to.")

    args = parser.parse_args()

    try:
        print("\nStarting manual test for parse_zip_and_identify_projects...\n")
        projects_metadata = parse_zip_and_identify_projects(args.zip_path, args.extract_to)
        print("\nTest completed. Projects metadata:")
        for project in projects_metadata:
            print(project)
    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")