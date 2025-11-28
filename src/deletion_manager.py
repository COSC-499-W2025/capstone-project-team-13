"""
Minimal Deletion Manager - Handles shared file protection and AI insights deletion
"""
import os
from pathlib import Path
from src.Databases.database import db_manager


class DeletionManager:
    """Core deletion logic: remove insights, remove project, protect shared files."""

    def get_shared_files(self, project_id: int):
        """
        Return a list of file paths used by more than one project.
        Uses file_path comparison across projects.
        """
        session = db_manager.get_session()
        try:
            from src.Databases.database import File
            from sqlalchemy import func
            
            # Get all files for this project
            project_files = session.query(File).filter(
                File.project_id == project_id
            ).all()
            
            shared = []
            for file in project_files:
                # Count how many projects use this file path
                count = session.query(File).filter(
                    File.file_path == file.file_path
                ).count()
                
                if count > 1:
                    shared.append(file.file_path)
            
            return shared
        finally:
            session.close()

    def _delete_cache_for_project(self, project_id: int):
        """
        Delete cached analysis results for a project.
        """
        # AI cache directories
        cache_dirs = [
            Path("data/ai_cache"),
            Path("data/ai_text_project_cache"),
            Path("data/ai_project_analysis_cache")
        ]
        
        deleted_count = 0
        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue
            
            # Look for cache files related to this project
            for cache_file in cache_dir.glob("*.json"):
                try:
                    # Check if this cache file is for our project
                    import json
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        if data.get('project_id') == project_id:
                            cache_file.unlink()
                            deleted_count += 1
                except:
                    pass
        
        return deleted_count

    def delete_ai_insights_for_project(self, project_id: int):
        """
        Remove AI-generated analysis fields from the database for a project.
        """
        project = db_manager.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}

        # Update project to clear AI insights using db_manager's update method
        db_manager.update_project(project_id, {'ai_description': None})

        # Delete cached files
        cache_deleted = self._delete_cache_for_project(project_id)
        
        return {"success": True, "cache_deleted": cache_deleted}

    def delete_project_safely(self, project_id: int, delete_shared_files: bool = False):
        """
        Delete a project and its files.
        If delete_shared_files=False, preserves files used by other projects.
        """
        project = db_manager.get_project(project_id)
        if not project:
            return {"project_deleted": False, "error": "Project not found"}

        # Get shared files BEFORE deleting the project
        shared_files = self.get_shared_files(project_id)
        
        # Delete AI insights + cache
        self.delete_ai_insights_for_project(project_id)

        # Delete project from database (cascade will delete related records)
        success = db_manager.delete_project(project_id)

        return {
            "project_deleted": success,
            "files_protected": len(shared_files) if not delete_shared_files else 0,
            "shared_files": shared_files
        }