# src/Analysis/incrementalZipHandler.py

"""
Handler for incremental uploads to existing projects.
Accepts ZIP archives OR individual files of any type.
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from src.Databases.database import db_manager
from src.Analysis.codingProjectScanner import CodingProjectScanner
from src.Analysis.mediaProjectScanner import MediaProjectScanner
from src.Analysis.textDocumentScanner import TextDocumentScanner
from src.Settings.config import EXT_SUPERTYPES


def detect_project_type(folder_path):
    type_counts = {'code': 0, 'media': 0, 'text': 0}
    skip_dirs = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env',
                 'dist', 'build', '.next', '.cache', 'vendor', '__MACOSX'}

    for root, dirs, files in os.walk(folder_path):
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
        return {'type': 'unknown', 'code_count': 0, 'media_count': 0, 'text_count': 0,
                'details': 'No recognizable files found'}

    code_pct = type_counts['code'] / total_files
    media_pct = type_counts['media'] / total_files

    if code_pct > 0.7:
        project_type, details = 'code', f"Primarily code ({type_counts['code']} code files)"
    elif media_pct > 0.7:
        project_type, details = 'media', f"Primarily media ({type_counts['media']} media files)"
    elif code_pct > 0.2 and media_pct > 0.2:
        project_type, details = 'mixed', f"Mixed project ({type_counts['code']} code, {type_counts['media']} media files)"
    elif type_counts['code'] > 0:
        project_type, details = 'code', f"Small code project ({type_counts['code']} code files)"
    elif type_counts['media'] > 0:
        project_type, details = 'media', f"Small media project ({type_counts['media']} media files)"
    else:
        project_type, details = 'unknown', f"Unrecognized project type ({total_files} files)"

    return {'type': project_type, 'code_count': type_counts['code'],
            'media_count': type_counts['media'], 'text_count': type_counts['text'],
            'details': details}


class IncrementalZipHandler:
    """Handles incremental uploads — ZIP archives or individual files of any type."""

    def __init__(self):
        self.temp_dir = None

    def add_zip_to_existing_project(self, project_id: int, file_path: str) -> Dict[str, Any]:
        """
        Add files from a ZIP archive OR a single file to an existing project.

        Args:
            project_id: ID of existing project
            file_path: Path to a ZIP file or any individual file
        """
        try:
            project = db_manager.get_project(project_id)
            if not project:
                return {'success': False, 'error': f'Project with ID {project_id} not found'}

            suffix = Path(file_path).suffix.lower()

            # ── ZIP: extract to temp dir then scan ────────────────────────────
            if suffix == '.zip':
                try:
                    from src.Extraction.zipHandler import extract_zip, validate_zip_file
                    if not validate_zip_file(file_path):
                        return {'success': False, 'error': 'Invalid ZIP file format'}
                    self.temp_dir = tempfile.mkdtemp(prefix='incremental_')
                    extract_dir = extract_zip(file_path, self.temp_dir)
                    if not extract_dir:
                        return {'success': False, 'error': 'Failed to extract ZIP file'}
                    scan_dir = extract_dir
                except ImportError:
                    return {'success': False, 'error': 'ZIP extraction module not available'}

            # ── Single file: copy to temp dir so scanners can walk it ─────────
            else:
                self.temp_dir = tempfile.mkdtemp(prefix='incremental_')
                dest = Path(self.temp_dir) / Path(file_path).name
                shutil.copy2(file_path, dest)
                scan_dir = self.temp_dir

            result = self._update_project_all_types(project, scan_dir)
            self._cleanup()
            return result

        except Exception as e:
            self._cleanup()
            return {'success': False, 'error': f'Error during incremental update: {str(e)}'}

    def _update_project_all_types(self, project, extract_dir: str) -> Dict[str, Any]:
        """Update ANY project with ALL file types found in the scan directory."""
        try:
            from src.Analysis.file_hasher import compute_file_hash

            initial_file_count = project.file_count or 0
            initial_languages = set(project.languages) if project.languages else set()
            initial_frameworks = set(project.frameworks) if project.frameworks else set()
            initial_skills = set(project.skills) if project.skills else set()
            initial_tags = set(project.tags) if project.tags else set()

            code_scanner = CodingProjectScanner(extract_dir)
            media_scanner = MediaProjectScanner(extract_dir)
            text_scanner = TextDocumentScanner(extract_dir)

            code_scanner._find_code_files()
            media_scanner._find_files()
            text_scanner._find_text_files()

            total_found = (len(code_scanner.code_files) +
                           len(media_scanner.media_files) +
                           len(text_scanner.text_files))

            if total_found == 0:
                return {'success': False, 'error': 'No recognizable files found in upload'}

            # Deduplicate against existing files by hash
            existing_files = db_manager.get_files_for_project(project.id)
            existing_hashes = {f.file_hash for f in existing_files if f.file_hash}

            all_new_files = []
            for file_path in (list(code_scanner.code_files) +
                              list(media_scanner.media_files) +
                              list(text_scanner.text_files)):
                file_hash = compute_file_hash(str(file_path))
                if file_hash and file_hash not in existing_hashes:
                    all_new_files.append(file_path)
                    existing_hashes.add(file_hash)

            if not all_new_files:
                return {
                    'success': True,
                    'project_id': project.id,
                    'project_name': project.custom_description or project.name,
                    'files_added': 0,
                    'total_files': initial_file_count,
                    'details': {'message': 'All files already exist in this project (duplicates skipped)'},
                }

            # Analyse new content
            new_languages, new_frameworks, new_skills, new_tags = set(), set(), set(), set()

            if code_scanner.code_files:
                code_scanner._detect_languages_and_frameworks()
                new_languages = code_scanner.languages
                new_frameworks = code_scanner.frameworks

            if media_scanner.media_files:
                media_scanner._analyze_media()
                new_skills.update(media_scanner.skills_detected)
                new_tags.update(media_scanner.software_used)

            if text_scanner.text_files:
                text_scanner._detect_document_types()
                new_tags.update(text_scanner.document_types)

            # Persist new files
            for file_path in all_new_files:
                file_hash = compute_file_hash(str(file_path))
                db_manager.add_file_to_project({
                    'project_id': project.id,
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix,
                    'file_size': file_path.stat().st_size,
                    'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                    'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                    'file_hash': file_hash,
                })

            # Determine updated project type
            has_code = len(code_scanner.code_files) > 0 or 'code' in (project.project_type or '')
            has_media = len(media_scanner.media_files) > 0 or 'media' in (project.project_type or '')
            has_text = len(text_scanner.text_files) > 0 or 'text' in (project.project_type or '')
            new_project_type = 'mixed' if sum([has_code, has_media, has_text]) > 1 else project.project_type

            db_manager.update_project(project.id, {
                'file_count': initial_file_count + len(all_new_files),
                'project_type': new_project_type,
                'languages': list(initial_languages | new_languages),
                'frameworks': list(initial_frameworks | new_frameworks),
                'skills': list((initial_skills | new_skills))[:20],
                'tags': list(initial_tags | new_tags),
                'date_scanned': datetime.now(timezone.utc),
            })

            updated_project = db_manager.get_project(project.id)
            details = {}
            languages_added = new_languages - initial_languages
            if languages_added:
                details['languages_added'] = list(languages_added)
            frameworks_added = new_frameworks - initial_frameworks
            if frameworks_added:
                details['frameworks_added'] = list(frameworks_added)
            if new_project_type != project.project_type:
                details['type_upgraded'] = f"Upgraded from '{project.project_type}' to '{new_project_type}'"

            return {
                'success': True,
                'project_id': project.id,
                'project_name': updated_project.custom_description or updated_project.name,
                'files_added': len(all_new_files),
                'total_files': updated_project.file_count,
                'details': details,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'Error updating project: {str(e)}'}

    def _cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")


# ── CLI helpers (unchanged) ────────────────────────────────────────────────────

def select_project_for_incremental_update() -> Optional[int]:
    projects = db_manager.get_all_projects()
    if not projects:
        print("\nNo projects found in database.")
        return None

    print("\nSelect a project to update:")
    print("-" * 60)
    for i, project in enumerate(projects, 1):
        type_str = project.project_type or "unknown"
        file_count = project.file_count or 0
        name = project.custom_description or project.name
        print(f"{i:2d}. {name:<30} ({type_str}, {file_count} files)")
    print("-" * 60)

    try:
        choice = input("\nEnter project number (or 'c' to cancel): ").strip()
        if choice.lower() == 'c':
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            return projects[idx].id
        print("Invalid selection")
        return None
    except ValueError:
        print("Invalid input")
        return None


def handle_incremental_zip_upload():
    print("\n" + "=" * 70)
    print("ADD FILES TO EXISTING PROJECT (INCREMENTAL UPDATE)")
    print("=" * 70)
    print("\nAdd files to an existing project. Accepts ZIP archives or individual files.\n")

    project_id = select_project_for_incremental_update()
    if not project_id:
        print("\nCancelled.")
        return

    project = db_manager.get_project(project_id)
    name = project.custom_description or project.name
    print(f"\nSelected: {name}  |  Files: {project.file_count}  |  Type: {project.project_type}")

    file_path = input("\nEnter path to file or ZIP: ").strip().strip('"')
    if not file_path:
        print("\nNo path provided.")
        return
    if not os.path.exists(file_path):
        print(f"\nFile not found: {file_path}")
        return

    confirm = input("\nProceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\nCancelled.")
        return

    handler = IncrementalZipHandler()
    result = handler.add_zip_to_existing_project(project_id, file_path)

    print("\n" + "=" * 70)
    if result['success']:
        print("INCREMENTAL UPDATE SUCCESSFUL")
        print(f"  Files added:  {result['files_added']}")
        print(f"  Total files:  {result['total_files']}")
        details = result.get('details', {})
        if details.get('languages_added'):
            print(f"  New languages: {', '.join(details['languages_added'])}")
        if details.get('frameworks_added'):
            print(f"  New frameworks: {', '.join(details['frameworks_added'])}")
        if details.get('type_upgraded'):
            print(f"  {details['type_upgraded']}")
        if details.get('message'):
            print(f"  {details['message']}")
    else:
        print("INCREMENTAL UPDATE FAILED")
        print(f"  Error: {result['error']}")
    print("=" * 70)