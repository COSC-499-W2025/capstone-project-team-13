"""
Configuration and Settings Routes
==================================
API endpoints for managing user configuration, privacy settings, and analysis preferences.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from src.Databases.database import db_manager
from src.Databases.user_config import ConfigManager

router = APIRouter(prefix="/configuration", tags=["Configuration"])

config_manager = ConfigManager(db_manager)


# ============================================================================
# Request/Response Models
# ============================================================================

class PrivacySettingsUpdate(BaseModel):
    """Model for privacy settings updates"""
    anonymous_mode: Optional[bool] = None
    store_file_contents: Optional[bool] = None
    store_contributor_names: Optional[bool] = None
    store_file_paths: Optional[bool] = None
    max_file_size_scan: Optional[int] = None


class ExcludedFolderRequest(BaseModel):
    """Model for adding/removing excluded folders"""
    folder_path: str


class ExcludedFileTypeRequest(BaseModel):
    """Model for adding/removing excluded file types"""
    file_type: str


# ============================================================================
# Privacy Settings Endpoints
# ============================================================================

@router.get("/privacy-settings")
def get_privacy_settings():
    """Retrieve current privacy settings"""
    try:
        config = config_manager.get_or_create_config()
        return {
            "anonymous_mode": config.anonymous_mode,
            "store_file_contents": config.store_file_contents,
            "store_contributor_names": config.store_contributor_names,
            "store_file_paths": config.store_file_paths,
            "max_file_size_scan": config.max_file_size_scan,
            "excluded_folders": config.excluded_folders or [],
            "excluded_file_types": config.excluded_file_types or [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving privacy settings: {str(e)}")


@router.patch("/privacy-settings")
def update_privacy_settings(settings: PrivacySettingsUpdate):
    """Update privacy settings"""
    try:
        update_dict = settings.dict(exclude_unset=True)
        config = config_manager.update_config(update_dict)
        return {
            "success": True,
            "message": "Privacy settings updated successfully",
            "settings": {
                "anonymous_mode": config.anonymous_mode,
                "store_file_contents": config.store_file_contents,
                "store_contributor_names": config.store_contributor_names,
                "store_file_paths": config.store_file_paths,
                "max_file_size_scan": config.max_file_size_scan,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating privacy settings: {str(e)}")


@router.post("/privacy-settings/excluded-folders")
def add_excluded_folder(request: ExcludedFolderRequest):
    """Add a folder to the exclusion list"""
    try:
        if not request.folder_path:
            raise ValueError("Folder path cannot be empty")
        
        config_manager.add_excluded_folder(request.folder_path)
        config = config_manager.get_or_create_config()
        
        return {
            "success": True,
            "message": f"Folder '{request.folder_path}' added to exclusion list",
            "excluded_folders": config.excluded_folders or []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding excluded folder: {str(e)}")


@router.delete("/privacy-settings/excluded-folders")
def remove_excluded_folder(request: ExcludedFolderRequest):
    """Remove a folder from the exclusion list"""
    try:
        if not request.folder_path:
            raise ValueError("Folder path cannot be empty")

        config = config_manager.remove_excluded_folder(request.folder_path)
        return {
            "success": True,
            "message": f"Folder '{request.folder_path}' removed from exclusion list",
            "excluded_folders": config.excluded_folders or []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error removing excluded folder: {str(e)}")


@router.post("/privacy-settings/excluded-file-types")
def add_excluded_file_type(request: ExcludedFileTypeRequest):
    """Add a file type to the exclusion list"""
    try:
        if not request.file_type:
            raise ValueError("File type cannot be empty")
        
        config_manager.add_excluded_file_type(request.file_type)
        config = config_manager.get_or_create_config()
        
        return {
            "success": True,
            "message": f"File type '{request.file_type}' added to exclusion list",
            "excluded_file_types": config.excluded_file_types or []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding excluded file type: {str(e)}")


@router.delete("/privacy-settings/excluded-file-types")
def remove_excluded_file_type(request: ExcludedFileTypeRequest):
    """Remove a file type from the exclusion list"""
    try:
        if not request.file_type:
            raise ValueError("File type cannot be empty")

        config = config_manager.remove_excluded_file_type(request.file_type)
        return {
            "success": True,
            "message": f"File type '{request.file_type}' removed from exclusion list",
            "excluded_file_types": config.excluded_file_types or []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error removing excluded file type: {str(e)}")
