"""
User Configuration Storage System
Manages user preferences, consent settings, privacy options, and application settings
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import json
from typing import Dict, Any, Optional, List
from src.Databases.database import Base


class UserConfig(Base):
    """
    Store user configuration and preferences
    Includes consent, privacy settings, UI preferences, and feature toggles
    """
    __tablename__ = 'user_configs'
    
    id = Column(Integer, primary_key=True)
    config_version = Column(String(20), default='1.0.0')
    
    # === CONSENT MANAGEMENT ===
    basic_consent_granted = Column(Boolean, default=False)
    basic_consent_timestamp = Column(DateTime, nullable=True)
    
    ai_consent_granted = Column(Boolean, default=False)
    ai_consent_timestamp = Column(DateTime, nullable=True)
    
    # === PRIVACY SETTINGS ===
    anonymous_mode = Column(Boolean, default=False)
    store_file_contents = Column(Boolean, default=True)
    store_contributor_names = Column(Boolean, default=True)
    store_file_paths = Column(Boolean, default=True)
    
    # Privacy - Excluded items (stored as JSON)
    _excluded_folders = Column('excluded_folders', Text)  # List of folder paths
    _excluded_file_types = Column('excluded_file_types', Text)  # List of extensions
    _excluded_metadata_fields = Column('excluded_metadata_fields', Text)  # List of field names
    
    # === SCANNING PREFERENCES ===
    auto_detect_project_type = Column(Boolean, default=True)
    scan_nested_folders = Column(Boolean, default=True)
    max_scan_depth = Column(Integer, default=10)
    skip_hidden_files = Column(Boolean, default=True)
    skip_system_folders = Column(Boolean, default=True)
    
    # File size limits (in bytes)
    max_file_size_scan = Column(Integer, default=100_000_000)  # 100MB default
    min_file_size_scan = Column(Integer, default=0)
    
    # === AI/LLM SETTINGS ===
    ai_enabled = Column(Boolean, default=False)
    ai_provider = Column(String(50), default='gemini')  # 'gemini', 'openai', etc.
    ai_model = Column(String(100), default='gemini-2.5-flash')
    ai_cache_enabled = Column(Boolean, default=True)
    ai_max_tokens = Column(Integer, default=1000)
    ai_temperature = Column(Float, default=0.7)
    
    # === ANALYSIS PREFERENCES ===
    enable_keyword_extraction = Column(Boolean, default=True)
    enable_language_detection = Column(Boolean, default=True)
    enable_framework_detection = Column(Boolean, default=True)
    enable_collaboration_analysis = Column(Boolean, default=True)
    enable_duplicate_detection = Column(Boolean, default=True)
    
    keyword_extraction_method = Column(String(50), default='rake')  # 'rake', 'tfidf', etc.
    min_keyword_score = Column(Float, default=1.0)
    max_keywords_per_project = Column(Integer, default=50)
    
    # === OUTPUT PREFERENCES ===
    default_export_format = Column(String(20), default='pdf')  # 'pdf', 'html', 'json'
    include_thumbnails = Column(Boolean, default=True)
    summary_detail_level = Column(String(20), default='medium')  # 'brief', 'medium', 'detailed'
    
    # Resume generation preferences
    resume_style = Column(String(50), default='professional')
    resume_max_projects = Column(Integer, default=5)
    resume_include_metrics = Column(Boolean, default=True)
    
    # === UI/UX PREFERENCES ===
    theme = Column(String(20), default='light')  # 'light', 'dark', 'auto'
    language = Column(String(10), default='en')
    show_progress_indicators = Column(Boolean, default=True)
    auto_clear_screen = Column(Boolean, default=True)
    
    # Dashboard customization (stored as JSON)
    _dashboard_widgets = Column('dashboard_widgets', Text)
    _favorite_projects = Column('favorite_projects', Text)  # List of project IDs
    
    # === PERFORMANCE SETTINGS ===
    enable_caching = Column(Boolean, default=True)
    cache_expiry_hours = Column(Integer, default=24)
    parallel_processing = Column(Boolean, default=True)
    max_concurrent_tasks = Column(Integer, default=4)
    
    # === NOTIFICATION PREFERENCES ===
    enable_notifications = Column(Boolean, default=True)
    notify_on_scan_complete = Column(Boolean, default=True)
    notify_on_errors = Column(Boolean, default=True)
    
    # === BACKUP & DATA RETENTION ===
    auto_backup_enabled = Column(Boolean, default=False)
    backup_frequency_days = Column(Integer, default=7)
    data_retention_days = Column(Integer, default=365)
    
    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # === JSON PROPERTY HANDLERS ===
    
    @property
    def excluded_folders(self) -> List[str]:
        """Get list of excluded folder paths"""
        return json.loads(self._excluded_folders) if self._excluded_folders else []
    
    @excluded_folders.setter
    def excluded_folders(self, value: List[str]):
        """Set list of excluded folder paths"""
        self._excluded_folders = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def excluded_file_types(self) -> List[str]:
        """Get list of excluded file extensions"""
        return json.loads(self._excluded_file_types) if self._excluded_file_types else []
    
    @excluded_file_types.setter
    def excluded_file_types(self, value: List[str]):
        """Set list of excluded file extensions"""
        self._excluded_file_types = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def excluded_metadata_fields(self) -> List[str]:
        """Get list of excluded metadata field names"""
        return json.loads(self._excluded_metadata_fields) if self._excluded_metadata_fields else []
    
    @excluded_metadata_fields.setter
    def excluded_metadata_fields(self, value: List[str]):
        """Set list of excluded metadata field names"""
        self._excluded_metadata_fields = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def dashboard_widgets(self) -> Dict[str, Any]:
        """Get dashboard widget configuration"""
        return json.loads(self._dashboard_widgets) if self._dashboard_widgets else {
            'show_recent_projects': True,
            'show_skill_trends': True,
            'show_productivity_metrics': True,
            'show_project_timeline': True
        }
    
    @dashboard_widgets.setter
    def dashboard_widgets(self, value: Dict[str, Any]):
        """Set dashboard widget configuration"""
        self._dashboard_widgets = json.dumps(value) if isinstance(value, dict) else value
    
    @property
    def favorite_projects(self) -> List[int]:
        """Get list of favorite project IDs"""
        return json.loads(self._favorite_projects) if self._favorite_projects else []
    
    @favorite_projects.setter
    def favorite_projects(self, value: List[int]):
        """Set list of favorite project IDs"""
        self._favorite_projects = json.dumps(value) if isinstance(value, list) else value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format"""
        return {
            'id': self.id,
            'config_version': self.config_version,
            
            # Consent
            'basic_consent_granted': self.basic_consent_granted,
            'basic_consent_timestamp': self.basic_consent_timestamp.isoformat() if self.basic_consent_timestamp else None,
            'ai_consent_granted': self.ai_consent_granted,
            'ai_consent_timestamp': self.ai_consent_timestamp.isoformat() if self.ai_consent_timestamp else None,
            
            # Privacy
            'anonymous_mode': self.anonymous_mode,
            'store_file_contents': self.store_file_contents,
            'store_contributor_names': self.store_contributor_names,
            'store_file_paths': self.store_file_paths,
            'excluded_folders': self.excluded_folders,
            'excluded_file_types': self.excluded_file_types,
            'excluded_metadata_fields': self.excluded_metadata_fields,
            
            # Scanning
            'auto_detect_project_type': self.auto_detect_project_type,
            'scan_nested_folders': self.scan_nested_folders,
            'max_scan_depth': self.max_scan_depth,
            'skip_hidden_files': self.skip_hidden_files,
            'skip_system_folders': self.skip_system_folders,
            'max_file_size_scan': self.max_file_size_scan,
            'min_file_size_scan': self.min_file_size_scan,
            
            # AI Settings
            'ai_enabled': self.ai_enabled,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'ai_cache_enabled': self.ai_cache_enabled,
            'ai_max_tokens': self.ai_max_tokens,
            'ai_temperature': self.ai_temperature,
            
            # Analysis
            'enable_keyword_extraction': self.enable_keyword_extraction,
            'enable_language_detection': self.enable_language_detection,
            'enable_framework_detection': self.enable_framework_detection,
            'enable_collaboration_analysis': self.enable_collaboration_analysis,
            'enable_duplicate_detection': self.enable_duplicate_detection,
            'keyword_extraction_method': self.keyword_extraction_method,
            'min_keyword_score': self.min_keyword_score,
            'max_keywords_per_project': self.max_keywords_per_project,
            
            # Output
            'default_export_format': self.default_export_format,
            'include_thumbnails': self.include_thumbnails,
            'summary_detail_level': self.summary_detail_level,
            'resume_style': self.resume_style,
            'resume_max_projects': self.resume_max_projects,
            'resume_include_metrics': self.resume_include_metrics,
            
            # UI/UX
            'theme': self.theme,
            'language': self.language,
            'show_progress_indicators': self.show_progress_indicators,
            'auto_clear_screen': self.auto_clear_screen,
            'dashboard_widgets': self.dashboard_widgets,
            'favorite_projects': self.favorite_projects,
            
            # Performance
            'enable_caching': self.enable_caching,
            'cache_expiry_hours': self.cache_expiry_hours,
            'parallel_processing': self.parallel_processing,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            
            # Notifications
            'enable_notifications': self.enable_notifications,
            'notify_on_scan_complete': self.notify_on_scan_complete,
            'notify_on_errors': self.notify_on_errors,
            
            # Backup
            'auto_backup_enabled': self.auto_backup_enabled,
            'backup_frequency_days': self.backup_frequency_days,
            'data_retention_days': self.data_retention_days,
            
            # Timestamps
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    def __repr__(self):
        return f"<UserConfig(id={self.id}, version={self.config_version}, updated={self.updated_at})>"


class ConfigManager:
    """
    Manager for user configuration operations
    Handles CRUD operations and configuration validation
    """
    
    def __init__(self, database_manager):
        """Initialize configuration manager with database manager"""
        self.db_manager = database_manager
    
    def get_or_create_config(self) -> UserConfig:
        """
        Get existing configuration or create default one
        There should only be one config per user/installation
        
        Returns:
            UserConfig: The user's configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            
            if not config:
                # Create default configuration
                config = UserConfig()
                session.add(config)
                session.commit()
                session.refresh(config)
            else:
                # Update last accessed timestamp
                config.last_accessed = datetime.now(timezone.utc)
                session.commit()
                session.refresh(config)
            
            # Detach from session by accessing all properties
            # This ensures the object can be used after session closes
            session.expunge(config)
            
            return config
        finally:
            session.close()
    
    def get_config(self) -> Optional[UserConfig]:
        """
        Get existing configuration without creating one
        
        Returns:
            Optional[UserConfig]: The configuration or None (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if config:
                session.expunge(config)
            return config
        finally:
            session.close()
    
    def update_config(self, updates: Dict[str, Any]) -> UserConfig:
        """
        Update configuration with provided values
        
        Args:
            updates: Dictionary of field names and new values
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            
            if not config:
                config = UserConfig()
                session.add(config)
            
            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(config)
            
            # Detach from session
            session.expunge(config)
            
            return config
        finally:
            session.close()
    
    def grant_basic_consent(self) -> UserConfig:
        """
        Grant basic file access consent
        
        Returns:
            UserConfig: Updated configuration
        """
        return self.update_config({
            'basic_consent_granted': True,
            'basic_consent_timestamp': datetime.now(timezone.utc)
        })
    
    def revoke_basic_consent(self) -> UserConfig:
        """
        Revoke basic file access consent
        
        Returns:
            UserConfig: Updated configuration
        """
        return self.update_config({
            'basic_consent_granted': False
        })
    
    def grant_ai_consent(self) -> UserConfig:
        """
        Grant AI/LLM service consent
        
        Returns:
            UserConfig: Updated configuration
        """
        return self.update_config({
            'ai_consent_granted': True,
            'ai_consent_timestamp': datetime.now(timezone.utc),
            'ai_enabled': True
        })
    
    def revoke_ai_consent(self) -> UserConfig:
        """
        Revoke AI/LLM service consent
        
        Returns:
            UserConfig: Updated configuration
        """
        return self.update_config({
            'ai_consent_granted': False,
            'ai_enabled': False
        })
    
    def add_excluded_folder(self, folder_path: str) -> UserConfig:
        """
        Add folder to exclusion list
        
        Args:
            folder_path: Path to exclude from scanning
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            excluded = config.excluded_folders
            
            if folder_path not in excluded:
                excluded.append(folder_path)
                config.excluded_folders = excluded
                session.commit()
                session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def remove_excluded_folder(self, folder_path: str) -> UserConfig:
        """
        Remove folder from exclusion list
        
        Args:
            folder_path: Path to remove from exclusions
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            excluded = config.excluded_folders
            
            if folder_path in excluded:
                excluded.remove(folder_path)
                config.excluded_folders = excluded
                session.commit()
                session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def add_excluded_file_type(self, extension: str) -> UserConfig:
        """
        Add file extension to exclusion list
        
        Args:
            extension: File extension to exclude (e.g., '.log')
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            # Ensure extension starts with dot
            if not extension.startswith('.'):
                extension = '.' + extension
            
            excluded = config.excluded_file_types
            
            if extension not in excluded:
                excluded.append(extension)
                config.excluded_file_types = excluded
                session.commit()
                session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def remove_excluded_file_type(self, extension: str) -> UserConfig:
        """
        Remove file extension from exclusion list
        
        Args:
            extension: File extension to remove from exclusions
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            # Ensure extension starts with dot
            if not extension.startswith('.'):
                extension = '.' + extension
            
            excluded = config.excluded_file_types
            
            if extension in excluded:
                excluded.remove(extension)
                config.excluded_file_types = excluded
                session.commit()
                session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def toggle_feature(self, feature_name: str) -> UserConfig:
        """
        Toggle a boolean feature on/off
        
        Args:
            feature_name: Name of the boolean field to toggle
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            if hasattr(config, feature_name):
                current_value = getattr(config, feature_name)
                if isinstance(current_value, bool):
                    setattr(config, feature_name, not current_value)
                    session.commit()
                    session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def add_favorite_project(self, project_id: int) -> UserConfig:
        """
        Add project to favorites
        
        Args:
            project_id: ID of project to favorite
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            favorites = config.favorite_projects
            
            if project_id not in favorites:
                favorites.append(project_id)
                config.favorite_projects = favorites
                session.commit()
                session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def remove_favorite_project(self, project_id: int) -> UserConfig:
        """
        Remove project from favorites
        
        Args:
            project_id: ID of project to unfavorite
            
        Returns:
            UserConfig: Updated configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.flush()
            
            favorites = config.favorite_projects
            
            if project_id in favorites:
                favorites.remove(project_id)
                config.favorite_projects = favorites
                session.commit()
                session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def reset_to_defaults(self) -> UserConfig:
        """
        Reset configuration to default values
        
        Returns:
            UserConfig: New default configuration (detached from session)
        """
        session = self.db_manager.get_session()
        try:
            # Delete existing config
            session.query(UserConfig).delete()
            
            # Create new default config
            config = UserConfig()
            session.add(config)
            session.commit()
            session.refresh(config)
            
            session.expunge(config)
            return config
        finally:
            session.close()
    
    def export_config(self) -> Dict[str, Any]:
        """
        Export configuration as dictionary
        
        Returns:
            Dict: Configuration data
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                config = UserConfig()
                session.add(config)
                session.commit()
                session.refresh(config)
            
            # Convert to dict while in session
            config_dict = config.to_dict()
            return config_dict
        finally:
            session.close()
    
    def import_config(self, config_data: Dict[str, Any]) -> UserConfig:
        """
        Import configuration from dictionary
        
        Args:
            config_data: Configuration data to import
            
        Returns:
            UserConfig: Updated configuration
        """
        # Filter out non-editable fields
        exclude_fields = {'id', 'created_at', 'updated_at', 'last_accessed'}
        filtered_data = {k: v for k, v in config_data.items() if k not in exclude_fields}
        
        return self.update_config(filtered_data)
    
    def is_folder_excluded(self, folder_path: str) -> bool:
        """
        Check if a folder is in the exclusion list
        
        Args:
            folder_path: Path to check
            
        Returns:
            bool: True if excluded
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                return False
            return folder_path in config.excluded_folders
        finally:
            session.close()
    
    def is_file_type_excluded(self, extension: str) -> bool:
        """
        Check if a file type is in the exclusion list
        
        Args:
            extension: File extension to check
            
        Returns:
            bool: True if excluded
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                return False
            
            # Ensure extension starts with dot
            if not extension.startswith('.'):
                extension = '.' + extension
            
            return extension in config.excluded_file_types
        finally:
            session.close()
    
    def should_process_file(self, file_path: str, file_size: int) -> bool:
        """
        Determine if a file should be processed based on configuration
        
        Args:
            file_path: Path to the file
            file_size: Size of file in bytes
            
        Returns:
            bool: True if file should be processed
        """
        session = self.db_manager.get_session()
        try:
            config = session.query(UserConfig).first()
            if not config:
                return True  # Process by default if no config
            
            # Check file size limits
            if file_size < config.min_file_size_scan or file_size > config.max_file_size_scan:
                return False
            
            # Check if extension is excluded
            extension = '.' + file_path.split('.')[-1] if '.' in file_path else ''
            if extension and extension in config.excluded_file_types:
                return False
            
            # Check if parent folder is excluded
            for excluded_folder in config.excluded_folders:
                if excluded_folder in file_path:
                    return False
            
            return True
        finally:
            session.close()

