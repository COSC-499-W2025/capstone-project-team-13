# src/Analysis/incrementalZipHandler.py

"""
Handler for incremental ZIP uploads to existing projects
Allows users to add more files to a project by uploading additional ZIP files
Compatible with current GitHub project structure
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from src.Extraction.zipHandler import extract_zip, validate_zip_file
from src.Databases.database import db_manager
from src.Analysis.codingProjectScanner import CodingProjectScanner
from src.Analysis.mediaProjectScanner import MediaProjectScanner
from src.Analysis.textDocumentScanner import TextDocumentScanner
from src.Settings.config import EXT_SUPERTYPES


def detect_project_type(folder_path):
    """
    Automatically detect project type by scanning folder contents
    
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


class IncrementalZipHandler:
    """Handles incremental uploads via ZIP files"""
    
    def __init__(self):
        self.temp_dir = None
    
    def add_zip_to_existing_project(self, project_id: int, zip_path: str) -> Dict[str, Any]:
        """
        Add files from ZIP to an existing project
        
        Args:
            project_id: ID of existing project
            zip_path: Path to ZIP file containing additional files
            
        Returns:
            Dictionary with success status and details
        """
        try:
            # Get existing project
            project = db_manager.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': f'Project with ID {project_id} not found'
                }
            
            # Validate ZIP file
            print("\n🔍 Validating ZIP file...")
            if not validate_zip_file(zip_path):
                return {
                    'success': False,
                    'error': 'Invalid ZIP file format'
                }
            
            # Extract ZIP to temporary location
            print("📦 Extracting ZIP file...")
            self.temp_dir = tempfile.mkdtemp(prefix='incremental_')
            extract_dir = extract_zip(zip_path, self.temp_dir)
            
            if not extract_dir:
                return {
                    'success': False,
                    'error': 'Failed to extract ZIP file'
                }
            
            # Detect type of extracted content
            print("🔍 Detecting content type...")
            detected_type = detect_project_type(extract_dir)
            
            print(f"   Detected: {detected_type['details']}")
            print(f"   Existing project type: {project.project_type}")
            
            # ALL project types now use the comprehensive multi-type update
            print(f"\n🔄 Performing incremental update for {project.project_type} project...")
            print(f"   Scanning for all file types (code, media, text)...")
            result = self._update_project_all_types(project, extract_dir)
            
            # Cleanup
            self._cleanup()
            
            return result
            
        except Exception as e:
            self._cleanup()
            return {
                'success': False,
                'error': f'Error during incremental update: {str(e)}'
            }
    
    def _update_project_all_types(self, project, extract_dir: str) -> Dict[str, Any]:
        """
        Update ANY project type with ALL file types from ZIP
        This replaces the old type-specific methods
        """
        try:
            from src.Analysis.file_hasher import compute_file_hash
            
            # Get baseline
            initial_file_count = project.file_count or 0
            initial_languages = set(project.languages) if project.languages else set()
            initial_frameworks = set(project.frameworks) if project.frameworks else set()
            initial_skills = set(project.skills) if project.skills else set()
            initial_tags = set(project.tags) if project.tags else set()
            
            # Scan ALL file types
            code_scanner = CodingProjectScanner(extract_dir)
            media_scanner = MediaProjectScanner(extract_dir)
            text_scanner = TextDocumentScanner(extract_dir)
            
            code_scanner._find_code_files()
            media_scanner._find_files()
            text_scanner._find_text_files()
            
            total_found = len(code_scanner.code_files) + len(media_scanner.media_files) + len(text_scanner.text_files)
            print(f"   Found {total_found} total files ({len(code_scanner.code_files)} code, {len(media_scanner.media_files)} media, {len(text_scanner.text_files)} text)")
            
            if total_found == 0:
                return {
                    'success': False,
                    'error': 'No recognizable files found in ZIP'
                }
            
            # Get existing file hashes
            existing_files = db_manager.get_files_for_project(project.id)
            existing_hashes = {f.file_hash for f in existing_files if f.file_hash}
            
            all_new_files = []
            
            # Collect all new files (avoid duplicates)
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
                    'project_name': project.name,
                    'files_added': 0,
                    'total_files': initial_file_count,
                    'details': {'message': 'All files were duplicates'}
                }
            
            print(f"   Adding {len(all_new_files)} new files (skipped {total_found - len(all_new_files)} duplicates)...")
            
            # Analyze what we found
            new_languages = set()
            new_frameworks = set()
            new_skills = set()
            new_tags = set()
            
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
            
            # Add all new files to database
            for file_path in all_new_files:
                file_hash = compute_file_hash(str(file_path))
                file_data = {
                    'project_id': project.id,
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix,
                    'file_size': file_path.stat().st_size,
                    'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                    'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                    'file_hash': file_hash
                }
                db_manager.add_file_to_project(file_data)
            
            # Determine new project type (may upgrade to 'mixed')
            new_project_type = project.project_type
            has_code = len(code_scanner.code_files) > 0 or 'code' in project.project_type
            has_media = len(media_scanner.media_files) > 0 or 'media' in project.project_type
            has_text = len(text_scanner.text_files) > 0 or 'text' in project.project_type
            
            # Upgrade to mixed if we now have multiple types
            type_count = sum([has_code, has_media, has_text])
            if type_count > 1:
                new_project_type = 'mixed'
            
            # Update project
            update_data = {
                'file_count': initial_file_count + len(all_new_files),
                'project_type': new_project_type,
                'languages': list(initial_languages | new_languages),
                'frameworks': list(initial_frameworks | new_frameworks),
                'skills': list((initial_skills | new_skills))[:20],
                'tags': list(initial_tags | new_tags),
                'date_scanned': datetime.now(timezone.utc)
            }
            db_manager.update_project(project.id, update_data)
            
            updated_project = db_manager.get_project(project.id)
            
            # Build details for response
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
                'project_name': updated_project.name,
                'files_added': len(all_new_files),
                'total_files': updated_project.file_count,
                'details': details
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Error updating project: {str(e)}'
            }
        
    def _cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up temp directory: {e}")


# ============================================
# MENU INTEGRATION FUNCTIONS
# ============================================

def select_project_for_incremental_update() -> Optional[int]:
    """
    Interactive project selection for incremental update
    
    Returns:
        project_id or None if cancelled
    """
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("\n❌ No projects found in database.")
        print("   Please analyze a project first before using incremental update.")
        return None
    
    print("\n📋 Select a project to update:")
    print("-" * 60)
    
    for i, project in enumerate(projects, 1):
        type_str = project.project_type or "unknown"
        file_count = project.file_count or 0
        print(f"{i:2d}. {project.name:<30} ({type_str}, {file_count} files)")
    
    print("-" * 60)
    
    try:
        choice = input("\nEnter project number (or 'c' to cancel): ").strip()
        
        if choice.lower() == 'c':
            return None
        
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            return projects[idx].id
        else:
            print("❌ Invalid selection")
            return None
            
    except ValueError:
        print("❌ Invalid input")
        return None


def handle_incremental_zip_upload():
    """
    Main handler for incremental ZIP upload feature
    Called from project upload menu
    """
    print("\n" + "="*70)
    print("ADD ZIP TO EXISTING PROJECT (INCREMENTAL UPDATE)")
    print("="*70)
    print("\nThis feature allows you to add more files to an existing project")
    print("by uploading a new ZIP file. Only new files will be added.\n")
    
    # Step 1: Select existing project
    project_id = select_project_for_incremental_update()
    if not project_id:
        print("\nCancelled.")
        return
    
    # Show selected project
    project = db_manager.get_project(project_id)
    print(f"\n✓ Selected project: {project.name}")
    print(f"  Current files: {project.file_count}")
    print(f"  Type: {project.project_type}")
    
    # Step 2: Get ZIP file path
    zip_path = input("\nEnter path to ZIP file with additional files: ").strip().strip('"')
    
    if not zip_path:
        print("\n❌ No path provided.")
        return
    
    if not zip_path.lower().endswith('.zip'):
        print("\n❌ File must be a ZIP archive (.zip)")
        return
    
    if not os.path.exists(zip_path):
        print(f"\n❌ File not found: {zip_path}")
        return
    
    # Step 3: Confirm
    print(f"\n📋 Summary:")
    print(f"   Project: {project.name} (ID: {project_id})")
    print(f"   ZIP file: {os.path.basename(zip_path)}")
    print(f"   Action: Add new files from ZIP to existing project")
    
    confirm = input("\nProceed with incremental update? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\nCancelled.")
        return
    
    # Step 4: Perform incremental update
    print("\n" + "="*70)
    print("PROCESSING INCREMENTAL UPDATE")
    print("="*70)
    
    handler = IncrementalZipHandler()
    result = handler.add_zip_to_existing_project(project_id, zip_path)
    
    # Step 5: Display results
    print("\n" + "="*70)
    if result['success']:
        print("✅ INCREMENTAL UPDATE SUCCESSFUL")
        print("="*70)
        print(f"\n📊 Update Summary:")
        print(f"   Project: {result['project_name']}")
        print(f"   Files added: {result['files_added']}")
        print(f"   Total files now: {result['total_files']}")
        
        if 'details' in result:
            details = result['details']
            if 'languages_added' in details and details['languages_added']:
                print(f"   New languages detected: {', '.join(details['languages_added'])}")
            if 'frameworks_added' in details and details['frameworks_added']:
                print(f"   New frameworks detected: {', '.join(details['frameworks_added'])}")
            if 'type_upgraded' in details:
                print(f"   🔄 {details['type_upgraded']}")
    else:
        print("❌ INCREMENTAL UPDATE FAILED")
        print("="*70)
        print(f"\n   Error: {result['error']}")
    
    print("\n" + "="*70)