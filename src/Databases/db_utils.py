# src/Databases/db_utils.py
"""
Database utility functions for migrations, backups, and maintenance
"""

import os
import shutil
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import after path setup in actual usage
try:
    from database import DatabaseManager, Project, File, Contributor, Keyword
except ImportError:
    # For testing purposes
    pass


def backup_database(source_path: str = 'data/projects.db', 
                   backup_dir: str = 'data/backups') -> Optional[str]:
    """
    Create a timestamped backup of the database
    
    Args:
        source_path: Path to source database
        backup_dir: Directory to store backups
        
    Returns:
        Path to backup file or None if source doesn't exist
    """
    if not os.path.exists(source_path):
        print(f"Source database not found: {source_path}")
        return None
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_projects_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Copy database
    shutil.copy2(source_path, backup_path)
    print(f"✓ Database backed up to: {backup_path}")
    
    return backup_path


def restore_database(backup_path: str, 
                    target_path: str = 'data/projects.db') -> bool:
    """
    Restore database from a backup
    
    Args:
        backup_path: Path to backup file
        target_path: Path where to restore database
        
    Returns:
        True if successful
    """
    if not os.path.exists(backup_path):
        print(f"Backup file not found: {backup_path}")
        return False
    
    # Backup current database first
    if os.path.exists(target_path):
        pre_restore_backup = backup_database(target_path)
        print(f"Current database backed up to: {pre_restore_backup}")
    
    # Restore
    shutil.copy2(backup_path, target_path)
    print(f"✓ Database restored from: {backup_path}")
    
    return True


def export_project_to_json(db_manager: DatabaseManager, 
                           project_id: int, 
                           output_path: str) -> bool:
    """
    Export a project to JSON file
    
    Args:
        db_manager: DatabaseManager instance
        project_id: ID of project to export
        output_path: Path to output JSON file
        
    Returns:
        True if successful
    """
    project_data = db_manager.export_project_to_dict(project_id)
    
    if not project_data:
        print(f"Project {project_id} not found")
        return False
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, indent=2, default=str)
    
    print(f"✓ Project exported to: {output_path}")
    return True


def export_all_projects_to_json(db_manager: DatabaseManager, 
                                output_dir: str = 'exports') -> int:
    """
    Export all projects to individual JSON files
    
    Args:
        db_manager: DatabaseManager instance
        output_dir: Directory to store exported files
        
    Returns:
        Number of projects exported
    """
    os.makedirs(output_dir, exist_ok=True)
    
    projects = db_manager.get_all_projects(include_hidden=True)
    count = 0
    
    for project in projects:
        # Create safe filename
        safe_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.replace(' ', '_')
        filename = f"project_{project.id}_{safe_name}.json"
        output_path = os.path.join(output_dir, filename)
        
        if export_project_to_json(db_manager, project.id, output_path):
            count += 1
    
    print(f"\n✓ Exported {count} projects to {output_dir}/")
    return count


def migrate_old_database(old_db_path: str, 
                        new_db_path: str = 'data/projects_migrated.db') -> bool:
    """
    Migrate data from old database structure to new enhanced structure
    
    Args:
        old_db_path: Path to old database
        new_db_path: Path to new database
        
    Returns:
        True if successful
    """
    if not os.path.exists(old_db_path):
        print(f"Old database not found: {old_db_path}")
        return False
    
    print("Starting database migration...")
    
    try:
        # Import here to avoid circular imports
        from database import DatabaseManager
        
        # Create new database manager
        old_db = DatabaseManager(old_db_path)
        new_db = DatabaseManager(new_db_path)
        
        # Get all projects from old database
        old_projects = old_db.get_all_projects(include_hidden=True)
        
        migrated_count = 0
        for old_project in old_projects:
            # Export old project data
            old_data = old_db.export_project_to_dict(old_project.id)
            
            if not old_data:
                continue
            
            # Create project in new database (will have new fields with defaults)
            new_project_data = {
                'name': old_data.get('name'),
                'file_path': old_data.get('file_path'),
                'description': old_data.get('description'),
                'date_created': datetime.fromisoformat(old_data['date_created']) if old_data.get('date_created') else None,
                'date_modified': datetime.fromisoformat(old_data['date_modified']) if old_data.get('date_modified') else None,
                'lines_of_code': old_data.get('lines_of_code', 0),
                'file_count': old_data.get('file_count', 0),
                'project_type': old_data.get('project_type'),
                'languages': old_data.get('languages', []),
                'frameworks': old_data.get('frameworks', []),
            }
            
            new_project = new_db.create_project(new_project_data)
            
            # Migrate files
            for old_file in old_data.get('files', []):
                file_data = {
                    'project_id': new_project.id,
                    'file_path': old_file.get('file_path'),
                    'file_name': Path(old_file.get('file_path', '')).name,
                    'file_type': old_file.get('file_type'),
                    'file_size': old_file.get('file_size'),
                    'file_created': datetime.fromisoformat(old_file['file_created']) if old_file.get('file_created') else None,
                    'file_modified': datetime.fromisoformat(old_file['file_modified']) if old_file.get('file_modified') else None,
                }
                new_db.add_file(file_data)
            
            # Migrate contributors
            for old_contrib in old_data.get('contributors', []):
                contrib_data = {
                    'project_id': new_project.id,
                    'name': old_contrib.get('name'),
                    'contributor_identifier': old_contrib.get('contributor_identifier'),
                    'commit_count': old_contrib.get('commit_count', 0),
                }
                new_db.add_contributor(contrib_data)
            
            migrated_count += 1
            print(f"✓ Migrated: {old_project.name}")
        
        print(f"\n✓ Migration complete! Migrated {migrated_count} projects")
        print(f"New database created at: {new_db_path}")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_database_report(db_manager: DatabaseManager, 
                            output_path: str = 'data/database_report.txt') -> None:
    """
    Generate a comprehensive report of database contents
    
    Args:
        db_manager: DatabaseManager instance
        output_path: Path to output report file
    """
    stats = db_manager.get_stats()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("DATABASE REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Overall stats
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Projects: {stats['total_projects']}\n")
        f.write(f"Visible Projects: {stats['visible_projects']}\n")
        f.write(f"Featured Projects: {stats['featured_projects']}\n")
        f.write(f"Total Files: {stats['total_files']}\n")
        f.write(f"Total Contributors: {stats['total_contributors']}\n")
        f.write(f"Total Keywords: {stats['total_keywords']}\n")
        f.write(f"Total Lines of Code: {stats['total_lines_of_code']:,}\n\n")
        
        # Projects by type
        f.write("PROJECTS BY TYPE\n")
        f.write("-" * 80 + "\n")
        for ptype, count in stats['projects_by_type'].items():
            f.write(f"{ptype}: {count}\n")
        f.write("\n")
        
        # Top projects
        projects = db_manager.get_all_projects()[:10]
        f.write("TOP 10 PROJECTS (by importance)\n")
        f.write("-" * 80 + "\n")
        for i, project in enumerate(projects, 1):
            f.write(f"{i}. {project.name}\n")
            f.write(f"   Score: {project.importance_score}\n")
            f.write(f"   Type: {project.project_type}\n")
            f.write(f"   Languages: {', '.join(project.languages)}\n")
            f.write(f"   Files: {project.file_count}, Lines: {project.lines_of_code:,}\n\n")
        
        # Top keywords
        f.write("TOP 20 KEYWORDS\n")
        f.write("-" * 80 + "\n")
        all_keywords = db_manager.get_all_keywords()[:20]
        for kw, count, avg_score in all_keywords:
            f.write(f"{kw}: {count} projects, avg score: {avg_score:.2f}\n")
    
    print(f"✓ Report generated: {output_path}")


def cleanup_old_backups(backup_dir: str = 'data/backups', 
                       keep_recent: int = 5) -> int:
    """
    Clean up old backup files, keeping only the most recent ones
    
    Args:
        backup_dir: Directory containing backups
        keep_recent: Number of recent backups to keep
        
    Returns:
        Number of files deleted
    """
    if not os.path.exists(backup_dir):
        return 0
    
    # Get all backup files
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.startswith('backup_projects_') and filename.endswith('.db'):
            filepath = os.path.join(backup_dir, filename)
            backups.append((filepath, os.path.getmtime(filepath)))
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x[1], reverse=True)
    
    # Delete old backups
    deleted = 0
    for filepath, _ in backups[keep_recent:]:
        os.remove(filepath)
        deleted += 1
        print(f"Deleted old backup: {os.path.basename(filepath)}")
    
    if deleted > 0:
        print(f"✓ Cleaned up {deleted} old backup(s)")
    else:
        print("No old backups to clean up")
    
    return deleted


def verify_database_integrity(db_manager: DatabaseManager) -> Dict[str, Any]:
    """
    Verify database integrity and report any issues
    
    Args:
        db_manager: DatabaseManager instance
        
    Returns:
        Dictionary with verification results
    """
    results = {
        'is_valid': True,
        'issues': [],
        'warnings': []
    }
    
    print("Verifying database integrity...")
    
    # Check for orphaned files
    session = db_manager.get_session()
    try:
        from sqlalchemy import text
        
        orphaned_files = session.execute(text(
            "SELECT COUNT(*) FROM files WHERE project_id NOT IN (SELECT id FROM projects)"
        )).scalar()
        
        if orphaned_files > 0:
            results['is_valid'] = False
            results['issues'].append(f"Found {orphaned_files} orphaned file(s)")
        
        # Check for orphaned contributors
        orphaned_contribs = session.execute(text(
            "SELECT COUNT(*) FROM contributors WHERE project_id NOT IN (SELECT id FROM projects)"
        )).scalar()
        
        if orphaned_contribs > 0:
            results['is_valid'] = False
            results['issues'].append(f"Found {orphaned_contribs} orphaned contributor(s)")
        
        # Check for orphaned keywords
        orphaned_keywords = session.execute(text(
            "SELECT COUNT(*) FROM keywords WHERE project_id NOT IN (SELECT id FROM projects)"
        )).scalar()
        
        if orphaned_keywords > 0:
            results['is_valid'] = False
            results['issues'].append(f"Found {orphaned_keywords} orphaned keyword(s)")
        
        # Check for projects with missing essential fields
        projects = db_manager.get_all_projects(include_hidden=True)
        for project in projects:
            if not project.name:
                results['warnings'].append(f"Project {project.id} has no name")
            if not project.file_path:
                results['warnings'].append(f"Project {project.id} has no file path")
        
        # Print results
        if results['is_valid']:
            print("✓ Database integrity check passed")
        else:
            print("✗ Database integrity check found issues:")
            for issue in results['issues']:
                print(f"  - {issue}")
        
        if results['warnings']:
            print("\n⚠ Warnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")
        
    finally:
        session.close()
    
    return results


if __name__ == '__main__':
    """Command-line interface for database utilities"""
    import sys
    
    if len(sys.argv) < 2:
        print("Database Utilities")
        print("\nUsage:")
        print("  python db_utils.py backup              - Create database backup")
        print("  python db_utils.py restore <file>      - Restore from backup")
        print("  python db_utils.py export [project_id] - Export project(s) to JSON")
        print("  python db_utils.py migrate <old_db>    - Migrate old database")
        print("  python db_utils.py report              - Generate database report")
        print("  python db_utils.py cleanup             - Clean up old backups")
        print("  python db_utils.py verify              - Verify database integrity")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Import here for CLI usage
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from database import DatabaseManager
    
    if command == 'backup':
        backup_database()
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Error: Please specify backup file")
            sys.exit(1)
        restore_database(sys.argv[2])
    
    elif command == 'export':
        db = DatabaseManager()
        if len(sys.argv) >= 3:
            project_id = int(sys.argv[2])
            export_project_to_json(db, project_id, f'exports/project_{project_id}.json')
        else:
            export_all_projects_to_json(db)
    
    elif command == 'migrate':
        if len(sys.argv) < 3:
            print("Error: Please specify old database path")
            sys.exit(1)
        migrate_old_database(sys.argv[2])
    
    elif command == 'report':
        db = DatabaseManager()
        generate_database_report(db)
    
    elif command == 'cleanup':
        cleanup_old_backups()
    
    elif command == 'verify':
        db = DatabaseManager()
        verify_database_integrity(db)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
