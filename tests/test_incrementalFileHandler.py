"""
Unit tests for incrementalFileHandler.py
Tests adding individual files to existing projects
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.incrementalFileHandler import (
    detect_file_type,
    add_file_to_project,
    add_multiple_files_to_project,
    select_project_for_file_addition
)
from src.Databases.database import db_manager


class TestDetectFileType(unittest.TestCase):
    """Test file type detection"""
    
    def test_detect_code_files(self):
        """Test detection of code files"""
        self.assertEqual(detect_file_type('test.py'), 'code')
        self.assertEqual(detect_file_type('app.js'), 'code')
        self.assertEqual(detect_file_type('Main.java'), 'code')
    
    def test_detect_media_files(self):
        """Test detection of media files"""
        self.assertEqual(detect_file_type('image.png'), 'media')
        self.assertEqual(detect_file_type('photo.jpg'), 'media')
        self.assertEqual(detect_file_type('design.psd'), 'media')
    
    def test_detect_text_files(self):
        """Test detection of text/document files"""
        self.assertEqual(detect_file_type('readme.txt'), 'text')
        self.assertEqual(detect_file_type('notes.md'), 'text')
        self.assertEqual(detect_file_type('document.pdf'), 'text')
    
    def test_detect_unknown_files(self):
        """Test detection of unknown file types"""
        self.assertEqual(detect_file_type('unknown.xyz'), 'unknown')
    
    def test_case_insensitive(self):
        """Test that file type detection is case-insensitive"""
        self.assertEqual(detect_file_type('FILE.PY'), 'code')
        self.assertEqual(detect_file_type('IMAGE.PNG'), 'media')


class TestAddFileToProject(unittest.TestCase):
    """Test adding single files to projects"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
        
        # Create UNIQUE project directories
        self.code_project_dir = tempfile.mkdtemp()
        self.media_project_dir = tempfile.mkdtemp()
        self.mixed_project_dir = tempfile.mkdtemp()
        
        # Create code project
        self.code_project = db_manager.create_project({
            'name': 'Code Project',
            'file_path': self.code_project_dir,
            'project_type': 'code',
            'file_count': 0,
            'date_scanned': datetime.now(timezone.utc)
        })
        
        # Create media project
        self.media_project = db_manager.create_project({
            'name': 'Media Project',
            'file_path': self.media_project_dir,
            'project_type': 'visual_media',
            'file_count': 0,
            'date_scanned': datetime.now(timezone.utc)
        })
        
        # Create mixed project
        self.mixed_project = db_manager.create_project({
            'name': 'Mixed Project',
            'file_path': self.mixed_project_dir,
            'project_type': 'mixed',
            'file_count': 0,
            'date_scanned': datetime.now(timezone.utc)
        })
        
        # Create test files
        self.code_file = os.path.join(self.test_dir, 'test.py')
        with open(self.code_file, 'w') as f:
            f.write('print("hello world")\n')
        
        self.media_file = os.path.join(self.test_dir, 'image.png')
        with open(self.media_file, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n')
        
        self.text_file = os.path.join(self.test_dir, 'readme.txt')
        with open(self.text_file, 'w') as f:
            f.write('Test readme')
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.code_project_dir)
        shutil.rmtree(self.media_project_dir)
        shutil.rmtree(self.mixed_project_dir)
        db_manager.clear_all_data()
    
    def test_add_code_to_code_project(self):
        """Test adding code file to code project"""
        result = add_file_to_project(self.code_project.id, self.code_file)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['file_added'], 'test.py')
        self.assertEqual(result['file_type'], 'code')
    
    def test_add_media_to_media_project(self):
        """Test adding media file to media project"""
        result = add_file_to_project(self.media_project.id, self.media_file)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['file_added'], 'image.png')
    
    def test_add_any_to_mixed_project(self):
        """Test adding any file type to mixed project"""
        result1 = add_file_to_project(self.mixed_project.id, self.code_file)
        self.assertTrue(result1['success'])
        
        result2 = add_file_to_project(self.mixed_project.id, self.media_file)
        self.assertTrue(result2['success'])
        
        result3 = add_file_to_project(self.mixed_project.id, self.text_file)
        self.assertTrue(result3['success'])
    
    @patch('builtins.input', return_value='yes')
    def test_type_mismatch_converts_to_mixed(self, mock_input):
        """Test that type mismatch converts project to mixed when user confirms"""
        result = add_file_to_project(self.code_project.id, self.media_file)
        
        self.assertTrue(result['success'])
        updated = db_manager.get_project(self.code_project.id)
        self.assertEqual(updated.project_type, 'mixed')
    
    @patch('builtins.input', return_value='no')
    def test_type_mismatch_rejected_when_declined(self, mock_input):
        """Test that file rejected when user declines conversion"""
        result = add_file_to_project(self.code_project.id, self.media_file)
        
        self.assertFalse(result['success'])
        self.assertIn('mismatch', result['error'].lower())
    
    def test_duplicate_detection(self):
        """Test duplicate file detection"""
        result1 = add_file_to_project(self.code_project.id, self.code_file)
        self.assertTrue(result1['success'])
        
        result2 = add_file_to_project(self.code_project.id, self.code_file)
        self.assertFalse(result2['success'])
        self.assertTrue(result2.get('duplicate'))
    
    def test_file_not_found(self):
        """Test error when file doesn't exist"""
        result = add_file_to_project(self.code_project.id, '/nonexistent/file.py')
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower())
    
    def test_path_is_directory(self):
        """Test error when path is directory"""
        result = add_file_to_project(self.code_project.id, self.test_dir)
        
        self.assertFalse(result['success'])
        self.assertIn('not a file', result['error'].lower())
    
    def test_project_not_found(self):
        """Test error when project doesn't exist"""
        result = add_file_to_project(99999, self.code_file)
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower())
    
    def test_file_metadata_stored(self):
        """Test that file metadata is correctly stored"""
        result = add_file_to_project(self.code_project.id, self.code_file)
        self.assertTrue(result['success'])
        
        files = db_manager.get_files_for_project(self.code_project.id)
        self.assertEqual(len(files), 1)
        
        file_record = files[0]
        self.assertEqual(file_record.file_name, 'test.py')
        self.assertEqual(file_record.file_type, '.py')
        self.assertIsNotNone(file_record.file_hash)
    
    def test_project_count_updated(self):
        """Test that project file count increments"""
        result1 = add_file_to_project(self.mixed_project.id, self.code_file)
        self.assertEqual(result1['total_files'], 1)
        
        file2 = os.path.join(self.test_dir, 'utils.py')
        with open(file2, 'w') as f:
            f.write('def helper(): pass')
        
        result2 = add_file_to_project(self.mixed_project.id, file2)
        self.assertEqual(result2['total_files'], 2)


class TestAddMultipleFiles(unittest.TestCase):
    """Test batch file addition"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
        
        self.project = db_manager.create_project({
            'name': 'Batch Project',
            'file_path': self.project_dir,
            'project_type': 'mixed',
            'file_count': 0
        })
        
        # Create multiple test files
        self.files = []
        for i in range(5):
            file_path = os.path.join(self.test_dir, f'file{i}.py')
            with open(file_path, 'w') as f:
                f.write(f'# File {i}\n')
            self.files.append(file_path)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.project_dir)
        db_manager.clear_all_data()
    
    def test_add_multiple_success(self):
        """Test adding multiple files successfully"""
        results = add_multiple_files_to_project(self.project.id, self.files)
        
        self.assertTrue(results['success'])
        self.assertEqual(len(results['files_added']), 5)
        self.assertEqual(len(results['files_skipped']), 0)
    
    def test_batch_with_duplicates(self):
        """Test batch with duplicate files"""
        results1 = add_multiple_files_to_project(self.project.id, self.files)
        self.assertEqual(len(results1['files_added']), 5)
        
        results2 = add_multiple_files_to_project(self.project.id, self.files)
        self.assertEqual(len(results2['files_added']), 0)
        self.assertEqual(len(results2['files_skipped']), 5)
    
    def test_empty_list(self):
        """Test with empty file list"""
        results = add_multiple_files_to_project(self.project.id, [])
        
        self.assertTrue(results['success'])
        self.assertEqual(len(results['files_added']), 0)


class TestSelectProjectForFileAddition(unittest.TestCase):
    """Test project selection"""
    
    def setUp(self):
        """Create test environment"""
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        db_manager.clear_all_data()
    
    def test_no_projects_available(self):
        """Test when no projects exist"""
        result = select_project_for_file_addition()
        self.assertIsNone(result)
    
    @patch('builtins.input', return_value='1')
    def test_select_valid_project(self, mock_input):
        """Test selecting a valid project"""
        test_dir = tempfile.mkdtemp()
        try:
            project = db_manager.create_project({
                'name': 'Test',
                'file_path': test_dir,
                'project_type': 'code',
                'file_count': 0
            })
            
            result = select_project_for_file_addition()
            self.assertEqual(result, project.id)
        finally:
            shutil.rmtree(test_dir)
    
    @patch('builtins.input', return_value='c')
    def test_cancel_selection(self, mock_input):
        """Test cancelling selection"""
        test_dir = tempfile.mkdtemp()
        try:
            db_manager.create_project({
                'name': 'Test',
                'file_path': test_dir,
                'project_type': 'code',
                'file_count': 0
            })
            
            result = select_project_for_file_addition()
            self.assertIsNone(result)
        finally:
            shutil.rmtree(test_dir)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
        
        self.project = db_manager.create_project({
            'name': 'Edge Test',
            'file_path': self.project_dir,
            'project_type': 'mixed',
            'file_count': 0
        })
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.project_dir)
        db_manager.clear_all_data()
    
    def test_empty_file(self):
        """Test adding empty file"""
        empty = os.path.join(self.test_dir, 'empty.py')
        with open(empty, 'w') as f:
            pass
        
        result = add_file_to_project(self.project.id, empty)
        self.assertTrue(result['success'])
    
    def test_unicode_filename(self):
        """Test file with unicode characters"""
        unicode_file = os.path.join(self.test_dir, 'café.py')
        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write('# Test\n')
        
        result = add_file_to_project(self.project.id, unicode_file)
        self.assertTrue(result['success'])
    
    def test_same_content_different_names(self):
        """Test that files with same content are detected as duplicates"""
        file1 = os.path.join(self.test_dir, 'file1.py')
        file2 = os.path.join(self.test_dir, 'file2.py')
        
        with open(file1, 'w') as f:
            f.write('print("same")\n')
        with open(file2, 'w') as f:
            f.write('print("same")\n')
        
        result1 = add_file_to_project(self.project.id, file1)
        self.assertTrue(result1['success'])
        
        result2 = add_file_to_project(self.project.id, file2)
        self.assertFalse(result2['success'])
        self.assertTrue(result2.get('duplicate'))


if __name__ == '__main__':
    unittest.main(verbosity=2)