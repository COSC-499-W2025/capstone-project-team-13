import sys
import os
import shutil
import tempfile

# Ensure the `src` directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import zipfile
from pathlib import PurePosixPath
from src.Settings.config import EXT_SUPERTYPES
from src.Databases.database import db_manager
from src.Analysis.codingProjectScanner import scan_coding_project
from src.Analysis.mediaProjectScanner import scan_media_project
from src.Analysis.textDocumentScanner import scan_text_document


def _zip_top_level_name(member_name):
    """Normalise a zip member path and return its top-level component."""
    # ZIPs may use '/' or '\'; PurePosixPath handles both after replacing '\'
    parts = PurePosixPath(member_name.replace("\\", "/")).parts
    return parts[0] if parts else None


def splitZipFile(zip_path):
    """
    Given a zip file, identifies distinct top-level project folders within it.
    Ignores macOS artefacts (__MACOSX) and hidden entries.

    Returns:
        list[str]: Top-level folder names that contain at least one file.
    """
    projects = set()
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            top = _zip_top_level_name(member)
            if not top or top.startswith('__MACOSX') or top.startswith('.'):
                continue
            # Only add if this entry has a sub-path (i.e. is inside a folder)
            parts = PurePosixPath(member.replace("\\", "/")).parts
            if len(parts) > 1:
                projects.add(top)
    return list(projects)


def _count_files_recursive(folder):
    """Count all files under *folder* recursively."""
    total = 0
    for _, _, files in os.walk(folder):
        total += len(files)
    return total


def _find_project_roots(extract_dir):
    """
    Determine which directories inside *extract_dir* should each be treated as
    a separate project root.

    Rules:
      - Skip __MACOSX and hidden directories.
      - If the ZIP extracted to a single wrapper folder that contains only
        sub-folders (a common pattern: project.zip → project/src/, project/tests/),
        return the direct children of that wrapper as roots.
      - If the extracted root contains multiple top-level directories, each is a
        separate project root.
      - If the extracted root contains files directly (flat ZIP), treat the
        entire extracted directory as one project root.

    Returns:
        list[tuple[str, str]]: (name, absolute_path) pairs for each root.
    """
    skip = {'__MACOSX', '__pycache__', '.git', 'node_modules'}

    top_items = [
        item for item in os.listdir(extract_dir)
        if not item.startswith('.') and item not in skip
    ]

    top_dirs = [i for i in top_items if os.path.isdir(os.path.join(extract_dir, i))]
    top_files = [i for i in top_items if os.path.isfile(os.path.join(extract_dir, i))]

    # Flat ZIP: files sitting directly at the root — one project
    if top_files and not top_dirs:
        return [("project", extract_dir)]

    # Single wrapper folder with no loose files: look one level deeper
    if len(top_dirs) == 1 and not top_files:
        wrapper = os.path.join(extract_dir, top_dirs[0])
        inner = [
            item for item in os.listdir(wrapper)
            if not item.startswith('.') and item not in skip
        ]
        inner_dirs = [i for i in inner if os.path.isdir(os.path.join(wrapper, i))]
        inner_files = [i for i in inner if os.path.isfile(os.path.join(wrapper, i))]

        # Wrapper contains multiple sub-projects
        if len(inner_dirs) > 1 and not inner_files:
            return [(d, os.path.join(wrapper, d)) for d in inner_dirs]

        # Wrapper is itself the project (mixed content or single sub-folder)
        return [(top_dirs[0], wrapper)]

    # Multiple top-level directories: each is a separate project
    if top_dirs:
        roots = [(d, os.path.join(extract_dir, d)) for d in top_dirs]
        # If there are also loose files at root, include the root itself
        if top_files:
            roots.insert(0, ("root_files", extract_dir))
        return roots

    # Fallback: treat whole directory as one project
    return [("project", extract_dir)]


def processZipFile(zipFilePath, user_id=None):
    """
    Extract a ZIP file and scan each detected project root with the appropriate
    scanner, storing results in the database.

    Returns:
        list[dict]: One entry per discovered project.
    """
    temp_dir = tempfile.mkdtemp(prefix="zip_extract_")
    try:
        with zipfile.ZipFile(zipFilePath, 'r') as zf:
            zf.extractall(temp_dir)

        roots = _find_project_roots(temp_dir)
        results = []

        for name, path in roots:
            project_info = identifyProjectType(path)
            project_type = project_info['type']

            if project_type == 'code':
                project_id = scan_coding_project(path, user_id=user_id)
            elif project_type == 'media':
                project_id = scan_media_project(path, user_id=user_id)
            elif project_type == 'text':
                project_id = scan_text_document(path, user_id=user_id)
            else:
                project_id = scan_text_document(path, user_id=user_id)

            results.append({
                "name": name,
                "type": project_type,
                "file_count": _count_files_recursive(path),
                "path": path,
                "details": project_info['details'],
                "database_id": project_id,
            })

        return results
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

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

            print(f"Processing file: {filename}, Extension: {ext}, Type: {file_type}")

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