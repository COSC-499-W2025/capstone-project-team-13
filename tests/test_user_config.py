# tests/test_user_config.py
"""
Comprehensive test suite for user configuration system
Tests all CRUD operations, consent management, privacy settings, and preferences
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.user_config import UserConfig, ConfigManager
from src.Databases.database import DatabaseManager, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestUserConfig(unittest.TestCase):
    """Test UserConfig model and ConfigManager functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests"""
        cls.test_db_path = tempfile.mktemp(suffix='.db')
        cls.engine = create_engine(f'sqlite:///{cls.test_db_path}')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        # Close all connections and dispose engine
        if hasattr(cls, 'Session'):
            cls.Session.close_all()
        if hasattr(cls, 'engine'):
            cls.engine.dispose()
        
        # Give Windows time to release file locks
        import time
        time.sleep(0.1)
        
        # Try to remove file, ignore if still locked (Windows issue)
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except PermissionError:
                # File still locked on Windows - this is OK for tests
                pass
    
    def setUp(self):
        """Set up fresh database for each test"""
        # Create database manager for this test
        self.db_manager = DatabaseManager(db_path=self.test_db_path)
        self.config_manager = ConfigManager(database_manager=self.db_manager)
        
        # Clear any existing config
        session = self.Session()
        try:
            session.query(UserConfig).delete()
            session.commit()
        finally:
            session.close()
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
    
    # ============ BASIC CONFIGURATION TESTS ============
    
    def test_create_default_config(self):
        """Test creating default configuration"""
        config = self.config_manager.get_or_create_config()
        
        self.assertIsNotNone(config)
        self.assertEqual(config.config_version, '1.0.0')
        self.assertFalse(config.basic_consent_granted)
        self.assertFalse(config.ai_consent_granted)
        self.assertFalse(config.anonymous_mode)
        self.assertTrue(config.auto_detect_project_type)
    
    def test_get_or_create_idempotent(self):
        """Test that get_or_create doesn't create duplicates"""
        config1 = self.config_manager.get_or_create_config()
        config2 = self.config_manager.get_or_create_config()
        
        self.assertEqual(config1.id, config2.id)
        
        # Verify only one config exists
        session = self.Session()
        try:
            count = session.query(UserConfig).count()
            self.assertEqual(count, 1)
        finally:
            session.close()
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary"""
        config = self.config_manager.get_or_create_config()
        config_dict = config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertIn('config_version', config_dict)
        self.assertIn('basic_consent_granted', config_dict)
        self.assertIn('ai_enabled', config_dict)
        self.assertIn('theme', config_dict)
    
    # ============ CONSENT MANAGEMENT TESTS ============
    
    def test_grant_basic_consent(self):
        """Test granting basic file access consent"""
        config = self.config_manager.grant_basic_consent()
        
        self.assertTrue(config.basic_consent_granted)
        self.assertIsNotNone(config.basic_consent_timestamp)
        self.assertIsInstance(config.basic_consent_timestamp, datetime)
    
    def test_revoke_basic_consent(self):
        """Test revoking basic file access consent"""
        # First grant it
        self.config_manager.grant_basic_consent()
        
        # Then revoke it
        config = self.config_manager.revoke_basic_consent()
        
        self.assertFalse(config.basic_consent_granted)
    
    def test_grant_ai_consent(self):
        """Test granting AI service consent"""
        config = self.config_manager.grant_ai_consent()
        
        self.assertTrue(config.ai_consent_granted)
        self.assertTrue(config.ai_enabled)
        self.assertIsNotNone(config.ai_consent_timestamp)
    
    def test_revoke_ai_consent(self):
        """Test revoking AI service consent"""
        # First grant it
        self.config_manager.grant_ai_consent()
        
        # Then revoke it
        config = self.config_manager.revoke_ai_consent()
        
        self.assertFalse(config.ai_consent_granted)
        self.assertFalse(config.ai_enabled)
    
    # ============ PRIVACY SETTINGS TESTS ============
    
    def test_add_excluded_folder(self):
        """Test adding folder to exclusion list"""
        folder_path = '/home/user/private'
        config = self.config_manager.add_excluded_folder(folder_path)
        
        self.assertIn(folder_path, config.excluded_folders)
    
    def test_add_excluded_folder_no_duplicates(self):
        """Test that same folder isn't added twice"""
        folder_path = '/home/user/private'
        
        self.config_manager.add_excluded_folder(folder_path)
        config = self.config_manager.add_excluded_folder(folder_path)
        
        # Should only appear once
        self.assertEqual(config.excluded_folders.count(folder_path), 1)
    
    def test_remove_excluded_folder(self):
        """Test removing folder from exclusion list"""
        folder_path = '/home/user/private'
        
        self.config_manager.add_excluded_folder(folder_path)
        config = self.config_manager.remove_excluded_folder(folder_path)
        
        self.assertNotIn(folder_path, config.excluded_folders)
    
    def test_add_excluded_file_type(self):
        """Test adding file type to exclusion list"""
        config = self.config_manager.add_excluded_file_type('.log')
        
        self.assertIn('.log', config.excluded_file_types)
    
    def test_add_excluded_file_type_auto_dot(self):
        """Test that dot is automatically added to extension"""
        config = self.config_manager.add_excluded_file_type('log')
        
        self.assertIn('.log', config.excluded_file_types)
    
    def test_remove_excluded_file_type(self):
        """Test removing file type from exclusion list"""
        self.config_manager.add_excluded_file_type('.log')
        config = self.config_manager.remove_excluded_file_type('.log')
        
        self.assertNotIn('.log', config.excluded_file_types)
    
    def test_is_folder_excluded(self):
        """Test checking if folder is excluded"""
        folder_path = '/home/user/private'
        
        self.assertFalse(self.config_manager.is_folder_excluded(folder_path))
        
        self.config_manager.add_excluded_folder(folder_path)
        
        self.assertTrue(self.config_manager.is_folder_excluded(folder_path))
    
    def test_is_file_type_excluded(self):
        """Test checking if file type is excluded"""
        self.assertFalse(self.config_manager.is_file_type_excluded('.log'))
        
        self.config_manager.add_excluded_file_type('.log')
        
        self.assertTrue(self.config_manager.is_file_type_excluded('.log'))
        self.assertTrue(self.config_manager.is_file_type_excluded('log'))  # Works without dot too
    
    # ============ UPDATE CONFIGURATION TESTS ============
    
    def test_update_single_field(self):
        """Test updating a single configuration field"""
        config = self.config_manager.update_config({'theme': 'dark'})
        
        self.assertEqual(config.theme, 'dark')
    
    def test_update_multiple_fields(self):
        """Test updating multiple configuration fields"""
        updates = {
            'theme': 'dark',
            'language': 'es',
            'max_scan_depth': 5
        }
        config = self.config_manager.update_config(updates)
        
        self.assertEqual(config.theme, 'dark')
        self.assertEqual(config.language, 'es')
        self.assertEqual(config.max_scan_depth, 5)
    
    def test_update_timestamp_changes(self):
        """Test that updated_at timestamp changes on update"""
        config1 = self.config_manager.get_or_create_config()
        original_timestamp = config1.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        config2 = self.config_manager.update_config({'theme': 'dark'})
        
        self.assertNotEqual(original_timestamp, config2.updated_at)
    
    # ============ FEATURE TOGGLE TESTS ============
    
    def test_toggle_feature(self):
        """Test toggling boolean features"""
        # Get initial state
        config = self.config_manager.get_or_create_config()
        initial_state = config.enable_keyword_extraction
        
        # Toggle it
        config = self.config_manager.toggle_feature('enable_keyword_extraction')
        
        self.assertEqual(config.enable_keyword_extraction, not initial_state)
        
        # Toggle back
        config = self.config_manager.toggle_feature('enable_keyword_extraction')
        
        self.assertEqual(config.enable_keyword_extraction, initial_state)
    
    def test_toggle_multiple_features(self):
        """Test toggling multiple features"""
        features = [
            'enable_keyword_extraction',
            'enable_language_detection',
            'enable_framework_detection'
        ]
        
        for feature in features:
            self.config_manager.toggle_feature(feature)
        
        config = self.config_manager.get_config()
        
        self.assertFalse(config.enable_keyword_extraction)  # Was True by default
        self.assertFalse(config.enable_language_detection)
        self.assertFalse(config.enable_framework_detection)
    
    # ============ FAVORITE PROJECTS TESTS ============
    
    def test_add_favorite_project(self):
        """Test adding project to favorites"""
        config = self.config_manager.add_favorite_project(1)
        
        self.assertIn(1, config.favorite_projects)
    
    def test_add_multiple_favorite_projects(self):
        """Test adding multiple favorite projects"""
        for project_id in [1, 2, 3, 5, 8]:
            self.config_manager.add_favorite_project(project_id)
        
        config = self.config_manager.get_config()
        
        self.assertEqual(len(config.favorite_projects), 5)
        self.assertIn(5, config.favorite_projects)
    
    def test_add_favorite_no_duplicates(self):
        """Test that favorite projects don't have duplicates"""
        self.config_manager.add_favorite_project(1)
        config = self.config_manager.add_favorite_project(1)
        
        self.assertEqual(config.favorite_projects.count(1), 1)
    
    def test_remove_favorite_project(self):
        """Test removing project from favorites"""
        self.config_manager.add_favorite_project(1)
        config = self.config_manager.remove_favorite_project(1)
        
        self.assertNotIn(1, config.favorite_projects)
    
    # ============ FILE PROCESSING TESTS ============
    
    def test_should_process_file_size_too_small(self):
        """Test file rejection when size is too small"""
        self.config_manager.update_config({'min_file_size_scan': 1000})
        
        should_process = self.config_manager.should_process_file(
            '/home/user/test.txt',
            file_size=500
        )
        
        self.assertFalse(should_process)
    
    def test_should_process_file_size_too_large(self):
        """Test file rejection when size is too large"""
        self.config_manager.update_config({'max_file_size_scan': 10000})
        
        should_process = self.config_manager.should_process_file(
            '/home/user/test.txt',
            file_size=50000
        )
        
        self.assertFalse(should_process)
    
    def test_should_process_file_excluded_extension(self):
        """Test file rejection when extension is excluded"""
        self.config_manager.add_excluded_file_type('.log')
        
        should_process = self.config_manager.should_process_file(
            '/home/user/debug.log',
            file_size=5000
        )
        
        self.assertFalse(should_process)
    
    def test_should_process_file_excluded_folder(self):
        """Test file rejection when in excluded folder"""
        self.config_manager.add_excluded_folder('/home/user/private')
        
        should_process = self.config_manager.should_process_file(
            '/home/user/private/data.txt',
            file_size=5000
        )
        
        self.assertFalse(should_process)
    
    def test_should_process_file_valid(self):
        """Test file acceptance when all criteria met"""
        should_process = self.config_manager.should_process_file(
            '/home/user/project/main.py',
            file_size=5000
        )
        
        self.assertTrue(should_process)
    
    # ============ IMPORT/EXPORT TESTS ============
    
    def test_export_config(self):
        """Test exporting configuration"""
        self.config_manager.update_config({
            'theme': 'dark',
            'language': 'fr',
            'ai_enabled': True
        })
        
        exported = self.config_manager.export_config()
        
        self.assertIsInstance(exported, dict)
        self.assertEqual(exported['theme'], 'dark')
        self.assertEqual(exported['language'], 'fr')
        self.assertTrue(exported['ai_enabled'])
    
    def test_import_config(self):
        """Test importing configuration"""
        config_data = {
            'theme': 'dark',
            'language': 'de',
            'max_scan_depth': 15,
            'ai_enabled': True
        }
        
        config = self.config_manager.import_config(config_data)
        
        self.assertEqual(config.theme, 'dark')
        self.assertEqual(config.language, 'de')
        self.assertEqual(config.max_scan_depth, 15)
        self.assertTrue(config.ai_enabled)
    
    def test_import_config_excludes_protected_fields(self):
        """Test that import doesn't modify protected fields"""
        original_config = self.config_manager.get_or_create_config()
        original_id = original_config.id
        original_created = original_config.created_at
        
        # Try to import with id and created_at
        config_data = {
            'id': 999,
            'created_at': datetime(2020, 1, 1),
            'theme': 'dark'
        }
        
        config = self.config_manager.import_config(config_data)
        
        # ID and created_at should remain unchanged
        self.assertEqual(config.id, original_id)
        self.assertEqual(config.created_at, original_created)
        # But theme should change
        self.assertEqual(config.theme, 'dark')
    
    # ============ RESET TESTS ============
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults"""
        # Modify configuration
        self.config_manager.update_config({
            'theme': 'dark',
            'language': 'es',
            'ai_enabled': True,
            'max_scan_depth': 20
        })
        
        # Reset to defaults
        config = self.config_manager.reset_to_defaults()
        
        self.assertEqual(config.theme, 'light')  # Default theme
        self.assertEqual(config.language, 'en')  # Default language
        self.assertFalse(config.ai_enabled)  # Default AI disabled
        self.assertEqual(config.max_scan_depth, 10)  # Default depth
    
    # ============ JSON FIELD TESTS ============
    
    def test_dashboard_widgets_default(self):
        """Test default dashboard widgets"""
        config = self.config_manager.get_or_create_config()
        widgets = config.dashboard_widgets
        
        self.assertIsInstance(widgets, dict)
        self.assertIn('show_recent_projects', widgets)
        self.assertTrue(widgets['show_recent_projects'])
    
    def test_dashboard_widgets_custom(self):
        """Test setting custom dashboard widgets"""
        custom_widgets = {
            'show_recent_projects': False,
            'show_skill_trends': True,
            'show_custom_widget': True
        }
        
        config = self.config_manager.update_config({
            'dashboard_widgets': custom_widgets
        })
        
        self.assertEqual(config.dashboard_widgets, custom_widgets)
        self.assertFalse(config.dashboard_widgets['show_recent_projects'])
        self.assertTrue(config.dashboard_widgets['show_custom_widget'])
    
    def test_excluded_metadata_fields(self):
        """Test excluded metadata fields list"""
        config = self.config_manager.get_or_create_config()
        
        # Initially empty
        self.assertEqual(len(config.excluded_metadata_fields), 0)
        
        # Add some exclusions
        config = self.config_manager.update_config({
            'excluded_metadata_fields': ['author', 'created_by', 'last_editor']
        })
        
        self.assertEqual(len(config.excluded_metadata_fields), 3)
        self.assertIn('author', config.excluded_metadata_fields)
    
    # ============ AI SETTINGS TESTS ============
    
    def test_ai_settings_defaults(self):
        """Test default AI settings"""
        config = self.config_manager.get_or_create_config()
        
        self.assertEqual(config.ai_provider, 'gemini')
        self.assertEqual(config.ai_model, 'gemini-2.5-flash')
        self.assertTrue(config.ai_cache_enabled)
        self.assertEqual(config.ai_max_tokens, 1000)
        self.assertEqual(config.ai_temperature, 0.7)
    
    def test_update_ai_settings(self):
        """Test updating AI settings"""
        config = self.config_manager.update_config({
            'ai_provider': 'openai',
            'ai_model': 'gpt-4',
            'ai_max_tokens': 2000,
            'ai_temperature': 0.5
        })
        
        self.assertEqual(config.ai_provider, 'openai')
        self.assertEqual(config.ai_model, 'gpt-4')
        self.assertEqual(config.ai_max_tokens, 2000)
        self.assertEqual(config.ai_temperature, 0.5)
    
    # ============ SCANNING PREFERENCES TESTS ============
    
    def test_scanning_defaults(self):
        """Test default scanning preferences"""
        config = self.config_manager.get_or_create_config()
        
        self.assertTrue(config.auto_detect_project_type)
        self.assertTrue(config.scan_nested_folders)
        self.assertEqual(config.max_scan_depth, 10)
        self.assertTrue(config.skip_hidden_files)
        self.assertTrue(config.skip_system_folders)
    
    def test_update_scan_settings(self):
        """Test updating scan settings"""
        config = self.config_manager.update_config({
            'max_scan_depth': 5,
            'skip_hidden_files': False,
            'max_file_size_scan': 50_000_000
        })
        
        self.assertEqual(config.max_scan_depth, 5)
        self.assertFalse(config.skip_hidden_files)
        self.assertEqual(config.max_file_size_scan, 50_000_000)


class TestConfigManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(db_path=self.test_db_path)
        self.config_manager = ConfigManager(database_manager=self.db_manager)
    
    def tearDown(self):
        """Clean up test database"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        
        # Small delay for Windows file lock release
        import time
        time.sleep(0.05)
        
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                # Windows file locking - ignore
                pass
    
    def test_update_nonexistent_field(self):
        """Test updating field that doesn't exist"""
        # This should not raise an error, just ignore the field
        config = self.config_manager.update_config({
            'nonexistent_field': 'value',
            'theme': 'dark'
        })
        
        self.assertEqual(config.theme, 'dark')
        self.assertFalse(hasattr(config, 'nonexistent_field'))
    
    def test_toggle_nonboolean_field(self):
        """Test toggling a non-boolean field"""
        config = self.config_manager.toggle_feature('theme')  # String field
        
        # Should return config unchanged
        self.assertIsNotNone(config)
    
    def test_multiple_config_managers_same_db(self):
        """Test multiple ConfigManager instances on same database"""
        manager1 = ConfigManager(database_manager=self.db_manager)
        manager2 = ConfigManager(database_manager=self.db_manager)
        
        config1 = manager1.update_config({'theme': 'dark'})
        config2 = manager2.get_config()
        
        self.assertEqual(config1.theme, config2.theme)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()