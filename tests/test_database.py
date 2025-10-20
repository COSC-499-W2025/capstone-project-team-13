# tests/test_database.py
import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from database import DatabaseManager

class TestDatabase(unittest.TestCase):
    """Test database"""
    
    def setUp(self):
        """Create test database"""
        self.db = DatabaseManager(
            'data/test_projects_data.db',
        )
        self.db.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        self.db.clear_all_data()
    
    # ============ DATABASE 1 TESTS ============
    
    def test_create_project(self):
        """Test creating a project in DB1"""
        project = self.db.create_project({
            'name': 'Test Project',
            'file_path': '/test/path',
            'date_created': datetime.now(),
            'date_modified': datetime.now(),
            'lines_of_code': 1000,
            'file_count': 10,
            'project_type': 'code',
            'languages': ['Python', 'JavaScript'],
            'frameworks': ['Django', 'React']
        })
        
        self.assertIsNotNone(project.id)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.lines_of_code, 1000)
    
    def test_add_files_to_project(self):
        """Test adding files to a project"""
        project = self.db.create_project({
            'name': 'Test Project',
            'file_path': '/test/path',
            'project_type': 'code'
        })
        
        file1 = self.db.add_file_to_project({
            'project_id': project.id,
            'file_path': '/test/path/main.py',
            'file_type': '.py',
            'file_size': 1024,
            'file_created': datetime.now(),
            'file_modified': datetime.now()
        })
        
        files = self.db.get_files_for_project(project.id)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].file_type, '.py')
    
    def test_add_contributors(self):
        """Test adding contributors to a project"""
        project = self.db.create_project({
            'name': 'Test Project',
            'file_path': '/test/path',
            'project_type': 'code'
        })
        
        contributor = self.db.add_contributor_to_project({
            'project_id': project.id,
            'name': 'John Doe',
            'contributor_identifier': 'john@example.com',
            'commit_count': 50
        })
        
        contributors = self.db.get_contributors_for_project(project.id)
        self.assertEqual(len(contributors), 1)
        self.assertEqual(contributors[0].commit_count, 50)

    def test_update_project(self):
        """Test updating a project"""
        # Create initial project
        project = self.db.create_project({
            'name': 'Original Name',
            'file_path': '/test/path',
            'project_type': 'code',
            'lines_of_code': 100
        })
        
        original_id = project.id
        
        # Update the project
        updated = self.db.update_project(project.id, {
            'name': 'Updated Name',
            'lines_of_code': 500,
            'languages': ['Python', 'JavaScript'],
            'frameworks': ['Django']
        })
        
        # Verify updates
        self.assertIsNotNone(updated)
        self.assertEqual(updated.id, original_id)
        self.assertEqual(updated.name, 'Updated Name')
        self.assertEqual(updated.lines_of_code, 500)
        self.assertEqual(updated.languages, ['Python', 'JavaScript'])
        self.assertEqual(updated.frameworks, ['Django'])

        
    def test_delete_project(self):
        """Test deleting a project and cascade deletion"""
        # Create project with files and contributors
        project = self.db.create_project({
            'name': 'Delete Me',
            'file_path': '/test/path',
            'project_type': 'code'
        })
        
        # Add file
        self.db.add_file_to_project({
            'project_id': project.id,
            'file_path': '/test/file.py',
            'file_type': '.py',
            'file_size': 100
        })
        
        # Add contributor
        self.db.add_contributor_to_project({
            'project_id': project.id,
            'name': 'Test User',
            'contributor_identifier': 'test@example.com',
            'commit_count': 10
        })
        
        # Verify data exists
        self.assertEqual(len(self.db.get_files_for_project(project.id)), 1)
        self.assertEqual(len(self.db.get_contributors_for_project(project.id)), 1)
        
        # Delete project
        result = self.db.delete_project(project.id)
        self.assertTrue(result)
        
        # Verify project is gone
        deleted_project = self.db.get_project(project.id)
        self.assertIsNone(deleted_project)
        
        # Verify cascade deletion worked
        self.assertEqual(len(self.db.get_files_for_project(project.id)), 0)
        self.assertEqual(len(self.db.get_contributors_for_project(project.id)), 0)
    
    def test_get_stats(self):
        """Test getting statistics"""
        # Create some data
        self.db.create_project({
            'name': 'Project 1',
            'file_path': '/test/1',
            'project_type': 'code'
        })
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_projects'], 1)
        self.assertIn('total_files', stats)

if __name__ == '__main__':
    unittest.main()