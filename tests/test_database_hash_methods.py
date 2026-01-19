"""
Unit tests for new database methods in database.py
Tests get_file_by_hash() and file_exists_in_project()
"""

import unittest
import os
import tempfile
import shutil
from datetime import datetime, timezone
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDatabaseHashMethods(unittest.TestCase):
    """Test new hash-based database methods"""
    
    def setUp(self):
        """Create temporary test database"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_hash_methods.db')
        
        from src.Databases.database import DatabaseManager
        self.db = DatabaseManager(db_path=self.test_db_path)
        
        # Create a test project
        project_data = {
            'name': 'Test Project',
            'file_path': '/test/path',
            'file_count': 0,
            'project_type': 'code',
            'languages': ['Python'],
            'frameworks': [],
            'date_scanned': datetime.now(timezone.utc)
        }
        self.test_project = self.db.create_project(project_data)
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        shutil.rmtree(self.test_dir)
    
    def test_get_file_by_hash_exists(self):
        """Test getting file by hash when it exists"""
        # Add a file with a hash
        file_data = {
            'project_id': self.test_project.id,
            'file_path': '/test/file.py',
            'file_name': 'file.py',
            'file_type': '.py',
            'file_size': 100,
            'file_created': datetime.now(timezone.utc),
            'file_modified': datetime.now(timezone.utc),
            'file_hash': 'abc123def456'
        }
        created_file = self.db.add_file_to_project(file_data)
        
        # Get file by hash
        found_file = self.db.get_file_by_hash('abc123def456')
        
        self.assertIsNotNone(found_file)
        self.assertEqual(found_file.file_hash, 'abc123def456')
        self.assertEqual(found_file.file_name, 'file.py')
    
    def test_get_file_by_hash_not_exists(self):
        """Test getting file by hash when it doesn't exist"""
        found_file = self.db.get_file_by_hash('nonexistent_hash')
        
        self.assertIsNone(found_file)
    
    def test_file_exists_in_project_true(self):
        """Test file_exists_in_project returns True when file exists"""
        # Add a file
        file_data = {
            'project_id': self.test_project.id,
            'file_path': '/test/file.py',
            'file_name': 'file.py',
            'file_type': '.py',
            'file_size': 100,
            'file_created': datetime.now(timezone.utc),
            'file_modified': datetime.now(timezone.utc),
            'file_hash': 'hash_exists'
        }
        self.db.add_file_to_project(file_data)
        
        # Check if exists
        exists = self.db.file_exists_in_project(self.test_project.id, 'hash_exists')
        
        self.assertTrue(exists)
    
    def test_file_exists_in_project_false(self):
        """Test file_exists_in_project returns False when file doesn't exist"""
        exists = self.db.file_exists_in_project(self.test_project.id, 'hash_not_exists')
        
        self.assertFalse(exists)
    
    def test_file_exists_in_different_project(self):
        """Test that file in one project doesn't match query for different project"""
        # Create second project
        project_data = {
            'name': 'Second Project',
            'file_path': '/test/path2',
            'file_count': 0,
            'project_type': 'code',
            'languages': ['JavaScript'],
            'frameworks': [],
            'date_scanned': datetime.now(timezone.utc)
        }
        project2 = self.db.create_project(project_data)
        
        # Add file to first project
        file_data = {
            'project_id': self.test_project.id,
            'file_path': '/test/file.py',
            'file_name': 'file.py',
            'file_type': '.py',
            'file_size': 100,
            'file_created': datetime.now(timezone.utc),
            'file_modified': datetime.now(timezone.utc),
            'file_hash': 'shared_hash'
        }
        self.db.add_file_to_project(file_data)
        
        # Check if exists in second project (should be False)
        exists_in_project2 = self.db.file_exists_in_project(project2.id, 'shared_hash')
        
        self.assertFalse(exists_in_project2)
    
    def test_multiple_files_same_hash_different_projects(self):
        """Test handling of same hash in different projects"""
        # Create second project
        project_data = {
            'name': 'Second Project',
            'file_path': '/test/path2',
            'file_count': 0,
            'project_type': 'code',
            'languages': ['JavaScript'],
            'frameworks': [],
            'date_scanned': datetime.now(timezone.utc)
        }
        project2 = self.db.create_project(project_data)
        
        # Add same hash to both projects
        file_data1 = {
            'project_id': self.test_project.id,
            'file_path': '/test/file1.py',
            'file_name': 'file1.py',
            'file_type': '.py',
            'file_size': 100,
            'file_created': datetime.now(timezone.utc),
            'file_modified': datetime.now(timezone.utc),
            'file_hash': 'duplicate_hash'
        }
        self.db.add_file_to_project(file_data1)
        
        file_data2 = {
            'project_id': project2.id,
            'file_path': '/test/file2.js',
            'file_name': 'file2.js',
            'file_type': '.js',
            'file_size': 100,
            'file_created': datetime.now(timezone.utc),
            'file_modified': datetime.now(timezone.utc),
            'file_hash': 'duplicate_hash'
        }
        self.db.add_file_to_project(file_data2)
        
        # Both should exist in their respective projects
        exists1 = self.db.file_exists_in_project(self.test_project.id, 'duplicate_hash')
        exists2 = self.db.file_exists_in_project(project2.id, 'duplicate_hash')
        
        self.assertTrue(exists1)
        self.assertTrue(exists2)


if __name__ == '__main__':
    unittest.main()