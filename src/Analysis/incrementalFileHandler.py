"""
Handler for incremental file uploads to existing projects
Allows users to add individual files (not just ZIPs) to existing projects
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from src.Databases.database import db_manager
from src.Analysis.file_hasher import compute_file_hash
from src.Settings.config import EXT_SUPERTYPES


def select_project_for_file_addition() -> Optional[int]:
    """
    Interactive project selection for adding files
    
    Returns:
        project_id or None if cancelled
    """
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("\n❌ No projects found in database.")
        print("   Please create a project first before adding files.")
        return None
    
    print("\n📋 Select a project to add files to:")
    print("-" * 70)
    
    for i, project in enumerate(projects, 1):
        type_str = project.project_type or "unknown"
        file_count = project.file_count or 0
        print(f"{i:2d}. {project.name:<35} ({type_str}, {file_count} files)")
    
    print("-" * 70)
    
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


def detect_file_type(file_path: str) -> str:
    """
    Detect if file is code, media, or text
    
    Returns:
        'code', 'media', 'text', or 'unknown'
    """
    ext = os.path.splitext(file_path)[1].lower()
    file_type = EXT_SUPERTYPES.get(ext, 'unknown')
    return file_type


def add_file_to_project(project_id: int, file_path: str) -> Dict[str, Any]:
    """
    Add a single file to an existing project
    
    Args:
        project_id: ID of existing project
        file_path: Path to file to add
        
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
        
        # Validate file exists
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        if not os.path.isfile(file_path):
            return {
                'success': False,
                'error': f'Path is not a file: {file_path}'
            }
        
        # Detect file type
        file_type = detect_file_type(file_path)
        
        # Check compatibility with project type
        # Note: Handle both 'media' and 'visual_media' as they're used inconsistently
        # Allow cross-type additions - convert to mixed if needed
        project_type_map = {
            'code': ['code', 'mixed'],
            'media': ['media', 'visual_media', 'mixed'],
            'text': ['text', 'document', 'mixed'],
        }

        compatible_types = project_type_map.get(file_type, [])

        # Check if types match
        type_matches = project.project_type in compatible_types if compatible_types else True

        if not type_matches:
            # Ask user if they want to convert to mixed project
            print(f"\n⚠️  Type mismatch: Project is '{project.project_type}' but file is '{file_type}'")
            convert = input("   Convert project to 'mixed' type? (yes/no): ").strip().lower()
            
            if convert != 'yes':
                return {
                    'success': False,
                    'error': f"Type mismatch: Project is '{project.project_type}' but file is '{file_type}'"
                }
            
            # Convert to mixed
            db_manager.update_project(project_id, {'project_type': 'mixed'})
            print(f"   ✓ Project converted to mixed type")
        
        # Check for duplicate using file hash
        file_hash = compute_file_hash(file_path)
        existing_files = db_manager.get_files_for_project(project_id)
        existing_hashes = {f.file_hash for f in existing_files if f.file_hash}
        
        if file_hash in existing_hashes:
            return {
                'success': False,
                'error': 'File already exists in this project (duplicate detected)',
                'duplicate': True
            }
        
        # Add file to database
        path_obj = Path(file_path)
        file_data = {
            'project_id': project_id,
            'file_path': str(path_obj),
            'file_name': path_obj.name,
            'file_type': path_obj.suffix,
            'file_size': path_obj.stat().st_size,
            'file_created': datetime.fromtimestamp(path_obj.stat().st_ctime, tz=timezone.utc),
            'file_modified': datetime.fromtimestamp(path_obj.stat().st_mtime, tz=timezone.utc),
            'file_hash': file_hash
        }
        db_manager.add_file_to_project(file_data)
        
        # Update project file count
        new_file_count = len(db_manager.get_files_for_project(project_id))
        db_manager.update_project(project_id, {
            'file_count': new_file_count,
            'date_scanned': datetime.now(timezone.utc)
        })
        
        # Get updated project
        updated_project = db_manager.get_project(project_id)
        
        return {
            'success': True,
            'project_id': project_id,
            'project_name': updated_project.name,
            'file_added': path_obj.name,
            'total_files': new_file_count,
            'file_type': file_type
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Error adding file: {str(e)}'
        }


def add_multiple_files_to_project(project_id: int, file_paths: list) -> Dict[str, Any]:
    """
    Add multiple files to an existing project
    
    Args:
        project_id: ID of existing project
        file_paths: List of file paths to add
        
    Returns:
        Dictionary with success status and details
    """
    results = {
        'success': True,
        'files_added': [],
        'files_skipped': [],
        'errors': []
    }
    
    for file_path in file_paths:
        result = add_file_to_project(project_id, file_path)
        
        if result['success']:
            results['files_added'].append(result['file_added'])
        elif result.get('duplicate'):
            results['files_skipped'].append(os.path.basename(file_path))
        else:
            results['errors'].append(f"{os.path.basename(file_path)}: {result['error']}")
    
    # Get final project info
    project = db_manager.get_project(project_id)
    results['project_name'] = project.name
    results['total_files'] = project.file_count
    
    return results


# ============================================
# MENU INTEGRATION FUNCTION
# ============================================

def handle_add_files_to_project():
    """
    Main handler for adding individual files to existing projects
    Called from project upload menu
    """
    print("\n" + "="*70)
    print("ADD FILES TO EXISTING PROJECT")
    print("="*70)
    print("\nThis feature allows you to add individual files to an existing project.")
    print("Duplicates will be automatically skipped.\n")
    
    # Step 1: Select existing project
    project_id = select_project_for_file_addition()
    if not project_id:
        print("\nCancelled.")
        return
    
    # Show selected project
    project = db_manager.get_project(project_id)
    print(f"\n✓ Selected project: {project.name}")
    print(f"  Current files: {project.file_count}")
    print(f"  Type: {project.project_type}")
    
    # Step 2: Get file paths
    print("\n" + "="*70)
    print("ENTER FILES TO ADD")
    print("="*70)
    print("You can add:")
    print("  • A single file path")
    print("  • Multiple file paths (separated by semicolons)")
    print("  • Or type 'folder' to add all files from a folder")
    print()
    
    input_choice = input("Enter file path(s) or 'folder': ").strip()
    
    if not input_choice:
        print("\n❌ No input provided.")
        return
    
    file_paths = []
    
    if input_choice.lower() == 'folder':
        # Add all files from folder
        folder_path = input("Enter folder path: ").strip().strip('"')
        
        if not os.path.exists(folder_path):
            print(f"\n❌ Folder not found: {folder_path}")
            return
        
        if not os.path.isdir(folder_path):
            print(f"\n❌ Path is not a folder: {folder_path}")
            return
        
        # Get all files in folder (non-recursive)
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                file_paths.append(item_path)
        
        if not file_paths:
            print(f"\n❌ No files found in folder: {folder_path}")
            return
        
        print(f"\n✓ Found {len(file_paths)} files in folder")
    
    elif ';' in input_choice:
        # Multiple files separated by semicolons
        file_paths = [p.strip().strip('"') for p in input_choice.split(';')]
    
    else:
        # Single file
        file_paths = [input_choice.strip().strip('"')]
    
    # Validate all files exist
    missing_files = [f for f in file_paths if not os.path.exists(f)]
    if missing_files:
        print(f"\n❌ File(s) not found:")
        for f in missing_files[:5]:
            print(f"   • {f}")
        if len(missing_files) > 5:
            print(f"   ... and {len(missing_files) - 5} more")
        return
    
    # Step 3: Confirm
    print(f"\n📋 Summary:")
    print(f"   Project: {project.name} (ID: {project_id})")
    print(f"   Files to add: {len(file_paths)}")
    if len(file_paths) <= 5:
        for f in file_paths:
            print(f"      • {os.path.basename(f)}")
    else:
        for f in file_paths[:3]:
            print(f"      • {os.path.basename(f)}")
        print(f"      ... and {len(file_paths) - 3} more")
    
    confirm = input("\nProceed with adding files? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\nCancelled.")
        return
    
    # Step 4: Add files
    print("\n" + "="*70)
    print("ADDING FILES")
    print("="*70)
    
    if len(file_paths) == 1:
        # Single file
        result = add_file_to_project(project_id, file_paths[0])
        
        print("\n" + "="*70)
        if result['success']:
            print("✅ FILE ADDED SUCCESSFULLY")
            print("="*70)
            print(f"\n📊 Update Summary:")
            print(f"   Project: {result['project_name']}")
            print(f"   File added: {result['file_added']}")
            print(f"   File type: {result['file_type']}")
            print(f"   Total files: {result['total_files']}")
        else:
            print("❌ FAILED TO ADD FILE")
            print("="*70)
            if result.get('duplicate'):
                print(f"\n   ⚠️  {result['error']}")
            else:
                print(f"\n   Error: {result['error']}")
    
    else:
        # Multiple files
        results = add_multiple_files_to_project(project_id, file_paths)
        
        print("\n" + "="*70)
        print("✅ BATCH ADD COMPLETE")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   Project: {results['project_name']}")
        print(f"   Files added: {len(results['files_added'])}")
        print(f"   Files skipped (duplicates): {len(results['files_skipped'])}")
        print(f"   Errors: {len(results['errors'])}")
        print(f"   Total files in project: {results['total_files']}")
        
        if results['files_added']:
            print(f"\n✅ Added:")
            for f in results['files_added'][:10]:
                print(f"   • {f}")
            if len(results['files_added']) > 10:
                print(f"   ... and {len(results['files_added']) - 10} more")
        
        if results['files_skipped']:
            print(f"\n⚠️  Skipped (duplicates):")
            for f in results['files_skipped'][:10]:
                print(f"   • {f}")
            if len(results['files_skipped']) > 10:
                print(f"   ... and {len(results['files_skipped']) - 10} more")
        
        if results['errors']:
            print(f"\n❌ Errors:")
            for e in results['errors'][:5]:
                print(f"   • {e}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more")
    
    print("\n" + "="*70)