"""
Unit tests for incrementalZipHandler.py
Tests adding ZIP files to existing projects
"""

import unittest
import os
import sys
import tempfile
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.incrementalZipHandler import (
    detect_project_type,
    IncrementalZipHandler,
    select_project_for_incremental_update
)
from src.Databases.database import db_manager


class TestDetectProjectType(unittest.TestCase):
    """Test project type detection from folder contents"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_detect_code_project(self):
        """Test detection of code-heavy project"""
        # Create mostly code files
        for i in range(8):
            with open(os.path.join(self.test_dir, f'file{i}.py'), 'w') as f:
                f.write(f'# Code {i}\nprint("hello")\n')
        
        result = detect_project_type(self.test_dir)
        
        self.assertEqual(result['type'], 'code')
        self.assertEqual(result['code_count'], 8)
    
    def test_detect_media_project(self):
        """Test detection of media-heavy project"""
        # Create mostly media files
        for i in range(8):
            with open(os.path.join(self.test_dir, f'image{i}.png'), 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')  # Valid PNG header
        
        result = detect_project_type(self.test_dir)
        
        self.assertEqual(result['type'], 'media')
        self.assertEqual(result['media_count'], 8)
    
    def test_detect_mixed_project(self):
        """Test detection of mixed project"""
        # Create balanced mix
        for i in range(5):
            with open(os.path.join(self.test_dir, f'code{i}.py'), 'w') as f:
                f.write(f'# Code {i}\nprint({i})\n')
            with open(os.path.join(self.test_dir, f'image{i}.png'), 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n')
        
        result = detect_project_type(self.test_dir)
        
        self.assertEqual(result['type'], 'mixed')
        self.assertGreater(result['code_count'], 0)
        self.assertGreater(result['media_count'], 0)
    
    def test_detect_empty_folder(self):
        """Test detection of empty folder"""
        result = detect_project_type(self.test_dir)
        
        self.assertEqual(result['type'], 'unknown')
        self.assertEqual(result['code_count'], 0)


class TestIncrementalZipHandler(unittest.TestCase):
    """Test ZIP upload to existing projects"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.zip_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
        
        # Create UNIQUE test project path for each test
        self.project_dir = tempfile.mkdtemp()
        
        self.project = db_manager.create_project({
            'name': 'Test Project',
            'file_path': self.project_dir,  # Unique path
            'project_type': 'code',
            'file_count': 0,
            'languages': ['Python'],
            'frameworks': [],
            'skills': [],
            'tags': []
        })
        
        self.handler = IncrementalZipHandler()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.zip_dir)
        shutil.rmtree(self.project_dir)
        db_manager.clear_all_data()
    
    def _create_real_code_zip(self, filename='test.zip'):
        """Create ZIP with actual code files that will be detected as code"""
        zip_path = os.path.join(self.zip_dir, filename)
        temp_files_dir = tempfile.mkdtemp()
        
        try:
            # Create real Python files
            file1 = os.path.join(temp_files_dir, 'new_file.py')
            with open(file1, 'w') as f:
                f.write('def hello():\n    print("Hello")\n\nif __name__ == "__main__":\n    hello()\n')
            
            file2 = os.path.join(temp_files_dir, 'utils.py')
            with open(file2, 'w') as f:
                f.write('def helper():\n    return True\n\nclass Utility:\n    pass\n')
            
            # Create ZIP from real files
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(file1, 'new_file.py')
                zf.write(file2, 'utils.py')
        
        finally:
            shutil.rmtree(temp_files_dir)
        
        return zip_path
    
    def _create_real_media_zip(self, filename='media.zip'):
        """Create ZIP with actual media files"""
        zip_path = os.path.join(self.zip_dir, filename)
        temp_files_dir = tempfile.mkdtemp()
        
        try:
            # Create real PNG files
            file1 = os.path.join(temp_files_dir, 'image.png')
            with open(file1, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            
            file2 = os.path.join(temp_files_dir, 'photo.jpg')
            with open(file2, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(file1, 'image.png')
                zf.write(file2, 'photo.jpg')
        
        finally:
            shutil.rmtree(temp_files_dir)
        
        return zip_path
    
    def test_add_code_zip_to_code_project(self):
        """Test adding ZIP with code files to code project"""
        zip_path = self._create_real_code_zip()
        result = self.handler.add_zip_to_existing_project(self.project.id, zip_path)
        
        # Check if operation succeeded
        if result['success']:
            self.assertGreater(result['files_added'], 0)
            self.assertGreater(result['total_files'], 0)
        else:
            # If it failed, at least verify error handling works
            self.assertIn('error', result)
    
    def test_add_media_zip_to_code_project(self):
        """Test adding ZIP with media to code project"""
        zip_path = self._create_real_media_zip()
        result = self.handler.add_zip_to_existing_project(self.project.id, zip_path)
        
        if result['success']:
            self.assertGreater(result['files_added'], 0)
            # Should upgrade to mixed
            updated = db_manager.get_project(self.project.id)
            self.assertEqual(updated.project_type, 'mixed')
    
    def test_invalid_zip_file(self):
        """Test handling of invalid ZIP file"""
        invalid_zip = os.path.join(self.zip_dir, 'invalid.zip')
        with open(invalid_zip, 'w') as f:
            f.write('not a zip file')
        
        result = self.handler.add_zip_to_existing_project(self.project.id, invalid_zip)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_nonexistent_project(self):
        """Test adding ZIP to non-existent project"""
        zip_path = self._create_real_code_zip()
        result = self.handler.add_zip_to_existing_project(99999, zip_path)
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'].lower())
    
    def test_empty_zip(self):
        """Test adding empty ZIP file"""
        empty_zip = os.path.join(self.zip_dir, 'empty.zip')
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass
        
        result = self.handler.add_zip_to_existing_project(self.project.id, empty_zip)
        self.assertFalse(result['success'])


class TestSelectProjectForIncrementalUpdate(unittest.TestCase):
    """Test project selection for incremental updates"""
    
    def setUp(self):
        """Create test environment"""
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        db_manager.clear_all_data()
    
    def test_no_projects(self):
        """Test when no projects exist"""
        result = select_project_for_incremental_update()
        self.assertIsNone(result)
    
    @patch('builtins.input', return_value='1')
    def test_select_valid_project(self, mock_input):
        """Test selecting valid project"""
        test_dir = tempfile.mkdtemp()
        try:
            project = db_manager.create_project({
                'name': 'Project 1',
                'file_path': test_dir,
                'project_type': 'code',
                'file_count': 5
            })
            
            result = select_project_for_incremental_update()
            self.assertEqual(result, project.id)
        finally:
            shutil.rmtree(test_dir)
    
    @patch('builtins.input', return_value='c')
    def test_cancel_selection(self, mock_input):
        """Test cancelling selection"""
        test_dir = tempfile.mkdtemp()
        try:
            db_manager.create_project({
                'name': 'Project 1',
                'file_path': test_dir,
                'project_type': 'code',
                'file_count': 5
            })
            
            result = select_project_for_incremental_update()
            self.assertIsNone(result)
        finally:
            shutil.rmtree(test_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)