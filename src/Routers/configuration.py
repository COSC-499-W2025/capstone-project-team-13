from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.Databases.database import db_manager
from src.Databases.user_config import ConfigManager


router = APIRouter(prefix="/configuration", tags=["Configuration"])
config_manager = ConfigManager(db_manager)


class PrivacySettingsUpdate(BaseModel):
    anonymous_mode: Optional[bool] = None
    store_file_contents: Optional[bool] = None
    store_contributor_names: Optional[bool] = None
    store_file_paths: Optional[bool] = None
    max_file_size_scan: Optional[int] = None


class ExcludedFolderRequest(BaseModel):
    folder_path: str


class ExcludedFileTypeRequest(BaseModel):
    file_type: str


class AnalysisPreferencesUpdate(BaseModel):
    enable_keyword_extraction: Optional[bool] = None
    enable_language_detection: Optional[bool] = None
    enable_framework_detection: Optional[bool] = None
    enable_collaboration_analysis: Optional[bool] = None
    enable_duplicate_detection: Optional[bool] = None


@router.get("/privacy-settings")
def get_privacy_settings():
    config = config_manager.get_or_create_config()
    return {
        "anonymous_mode": config.anonymous_mode,
        "store_file_contents": config.store_file_contents,
        "store_contributor_names": config.store_contributor_names,
        "store_file_paths": config.store_file_paths,
        "max_file_size_scan": config.max_file_size_scan,
        "excluded_folders": config.excluded_folders,
        "excluded_file_types": config.excluded_file_types,
    }


@router.patch("/privacy-settings")
def update_privacy_settings(settings: PrivacySettingsUpdate):
    updates = settings.model_dump(exclude_unset=True)
    config = config_manager.update_config(updates)
    return {
        "success": True,
        "settings": {
            "anonymous_mode": config.anonymous_mode,
            "store_file_contents": config.store_file_contents,
            "store_contributor_names": config.store_contributor_names,
            "store_file_paths": config.store_file_paths,
            "max_file_size_scan": config.max_file_size_scan,
        },
    }


@router.post("/privacy-settings/excluded-folders")
def add_excluded_folder(request: ExcludedFolderRequest):
    folder_path = request.folder_path.strip()
    if not folder_path:
        raise HTTPException(status_code=400, detail="Folder path cannot be empty")

    config = config_manager.add_excluded_folder(folder_path)
    return {
        "success": True,
        "excluded_folders": config.excluded_folders,
    }


@router.delete("/privacy-settings/excluded-folders")
def remove_excluded_folder(request: ExcludedFolderRequest):
    folder_path = request.folder_path.strip()
    if not folder_path:
        raise HTTPException(status_code=400, detail="Folder path cannot be empty")

    config = config_manager.remove_excluded_folder(folder_path)
    return {
        "success": True,
        "excluded_folders": config.excluded_folders,
    }


@router.post("/privacy-settings/excluded-file-types")
def add_excluded_file_type(request: ExcludedFileTypeRequest):
    file_type = request.file_type.strip()
    if not file_type:
        raise HTTPException(status_code=400, detail="File type cannot be empty")

    config = config_manager.add_excluded_file_type(file_type)
    return {
        "success": True,
        "excluded_file_types": config.excluded_file_types,
    }


@router.delete("/privacy-settings/excluded-file-types")
def remove_excluded_file_type(request: ExcludedFileTypeRequest):
    file_type = request.file_type.strip()
    if not file_type:
        raise HTTPException(status_code=400, detail="File type cannot be empty")

    config = config_manager.remove_excluded_file_type(file_type)
    return {
        "success": True,
        "excluded_file_types": config.excluded_file_types,
    }


@router.get("/analysis-preferences")
def get_analysis_preferences():
    config = config_manager.get_or_create_config()
    return {
        "enable_keyword_extraction": config.enable_keyword_extraction,
        "enable_language_detection": config.enable_language_detection,
        "enable_framework_detection": config.enable_framework_detection,
        "enable_collaboration_analysis": config.enable_collaboration_analysis,
        "enable_duplicate_detection": config.enable_duplicate_detection,
    }


@router.patch("/analysis-preferences")
def update_analysis_preferences(preferences: AnalysisPreferencesUpdate):
    updates = preferences.model_dump(exclude_unset=True)
    config = config_manager.update_config(updates)

    return {
        "success": True,
        "preferences": {
            "enable_keyword_extraction": config.enable_keyword_extraction,
            "enable_language_detection": config.enable_language_detection,
            "enable_framework_detection": config.enable_framework_detection,
            "enable_collaboration_analysis": config.enable_collaboration_analysis,
            "enable_duplicate_detection": config.enable_duplicate_detection,
        },
    }


@router.post("/analysis-preferences/enable-all")
def enable_all_analysis_preferences():
    updates = {
        "enable_keyword_extraction": True,
        "enable_language_detection": True,
        "enable_framework_detection": True,
        "enable_collaboration_analysis": True,
        "enable_duplicate_detection": True,
    }
    config = config_manager.update_config(updates)

    return {
        "success": True,
        "preferences": {
            "enable_keyword_extraction": config.enable_keyword_extraction,
            "enable_language_detection": config.enable_language_detection,
            "enable_framework_detection": config.enable_framework_detection,
            "enable_collaboration_analysis": config.enable_collaboration_analysis,
            "enable_duplicate_detection": config.enable_duplicate_detection,
        },
    }


@router.post("/analysis-preferences/disable-all")
def disable_all_analysis_preferences():
    updates = {
        "enable_keyword_extraction": False,
        "enable_language_detection": False,
        "enable_framework_detection": False,
        "enable_collaboration_analysis": False,
        "enable_duplicate_detection": False,
    }
    config = config_manager.update_config(updates)

    return {
        "success": True,
        "preferences": {
            "enable_keyword_extraction": config.enable_keyword_extraction,
            "enable_language_detection": config.enable_language_detection,
            "enable_framework_detection": config.enable_framework_detection,
            "enable_collaboration_analysis": config.enable_collaboration_analysis,
            "enable_duplicate_detection": config.enable_duplicate_detection,
        },
    }
