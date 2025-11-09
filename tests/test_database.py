# Fixed tests/test_database.py
import sys
import os
import unittest
from datetime import datetime, timedelta
import tempfile
import shutil
import time

# Setup path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')

# Add src directory to path if it exists
if os.path.exists(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Try importing the database module
try:
    from Databases.database import DatabaseManager, Project, File, Contributor, Keyword
except ImportError:
    try:
        from database import DatabaseManager, Project, File, Contributor, Keyword
    except ImportError:
        print("ERROR: Could not import database modules.")
        sys.exit(1)


class TestDatabaseEnhanced(unittest.TestCase):
    """Comprehensive tests for enhanced database functionality"""
    
    def setUp(self):
        """Create test database in temp directory"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        self.db = DatabaseManager(self.db_path)
        
    def tearDown(self):
        """Clean up test database - FIXED: Properly close database first"""
        # CRITICAL FIX: Close the database and dispose of all connections
        if hasattr(self, 'db'):
            self.db.close()
        
        # Give Windows a moment to release file locks
        time.sleep(0.1)
        
        # Now safely remove the directory
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            # If still locked, wait a bit more and try again
            time.sleep(0.5)
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError as e:
                print(f"Warning: Could not remove test directory {self.test_dir}: {e}")
                # Don't fail the test, just warn
                pass
    
    # ============ PROJECT TESTS ============
    
    def test_create_project_comprehensive(self):
        """Test creating a project with all fields"""
        project = self.db.create_project({
            'name': 'Full Featured Project',
            'file_path': '/test/full',
            'description': 'A comprehensive test project',
            'date_created': datetime(2024, 1, 1),
            'date_modified': datetime(2024, 10, 1),
            'lines_of_code': 5000,
            'file_count': 50,
            'total_size_bytes': 1024000,
            'project_type': 'code',
            'collaboration_type': 'individual',
            'importance_score': 8.5,
            'is_featured': True,
            'languages': ['Python', 'JavaScript', 'TypeScript'],
            'frameworks': ['Django', 'React', 'FastAPI'],
            'skills': ['API Development', 'Frontend', 'Database Design'],
            'tags': ['web', 'api', 'fullstack'],
            'user_role': 'Lead Developer',
            'custom_description': 'Built a full-stack application',
        })
        
        self.assertIsNotNone(project.id)
        self.assertEqual(project.name, 'Full Featured Project')
        self.assertEqual(len(project.languages), 3)
        self.assertEqual(len(project.frameworks), 3)
        self.assertEqual(len(project.skills), 3)
        self.assertTrue(project.is_featured)
        self.assertEqual(project.importance_score, 8.5)
    
    def test_get_project_by_path(self):
        """Test retrieving project by file path"""
        project = self.db.create_project({
            'name': 'Path Test',
            'file_path': '/unique/path/test',
            'project_type': 'code'
        })
        
        retrieved = self.db.get_project_by_path('/unique/path/test')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, project.id)
    
    def test_get_featured_projects(self):
        """Test getting only featured projects"""
        # Create featured project
        self.db.create_project({
            'name': 'Featured 1',
            'file_path': '/featured/1',
            'is_featured': True,
            'project_type': 'code'
        })
        
        # Create non-featured project
        self.db.create_project({
            'name': 'Not Featured',
            'file_path': '/not/featured',
            'is_featured': False,
            'project_type': 'code'
        })
        
        featured = self.db.get_featured_projects()
        self.assertEqual(len(featured), 1)
        self.assertEqual(featured[0].name, 'Featured 1')
    
    def test_update_project_ranking(self):
        """Test updating multiple project rankings"""
        project1 = self.db.create_project({
            'name': 'Project 1',
            'file_path': '/test/1',
            'project_type': 'code'
        })
        
        project2 = self.db.create_project({
            'name': 'Project 2',
            'file_path': '/test/2',
            'project_type': 'code'
        })
        
        # Update rankings
        self.db.update_project(project1.id, {'user_rank': 1})
        self.db.update_project(project2.id, {'user_rank': 2})
        
        # Verify
        p1 = self.db.get_project(project1.id)
        p2 = self.db.get_project(project2.id)
        
        self.assertEqual(p1.user_rank, 1)
        self.assertEqual(p2.user_rank, 2)
    
    def test_cascade_delete_project(self):
        """Test that deleting project cascades to files, contributors, keywords"""
        # Create project
        project = self.db.create_project({
            'name': 'Delete Test',
            'file_path': '/test/delete',
            'project_type': 'code'
        })
        
        # Add file
        self.db.add_file_to_project({
            'project_id': project.id,
            'file_path': '/test/file.py',
            'file_name': 'file.py',
            'file_type': '.py',
            'file_size': 100
        })
        
        # Add contributor
        self.db.add_contributor_to_project({
            'project_id': project.id,
            'name': 'Test User',
            'contributor_identifier': 'test@example.com'
        })
        
        # Add keyword
        self.db.add_keyword({
            'project_id': project.id,
            'keyword': 'python',
            'score': 5.0
        })
        
        # Verify data exists
        self.assertEqual(len(self.db.get_files_for_project(project.id)), 1)
        self.assertEqual(len(self.db.get_contributors_for_project(project.id)), 1)
        self.assertEqual(len(self.db.get_keywords_for_project(project.id)), 1)
        
        # Delete project
        result = self.db.delete_project(project.id)
        self.assertTrue(result)
        
        # Verify everything was deleted
        self.assertIsNone(self.db.get_project(project.id))
        self.assertEqual(len(self.db.get_files_for_project(project.id)), 0)
        self.assertEqual(len(self.db.get_contributors_for_project(project.id)), 0)
        self.assertEqual(len(self.db.get_keywords_for_project(project.id)), 0)
    
    # ============ FILE TESTS ============
    
    def test_add_files_with_metadata(self):
        """Test adding files with comprehensive metadata"""
        project = self.db.create_project({
            'name': 'File Test',
            'file_path': '/test/files',
            'project_type': 'code'
        })
        
        file = self.db.add_file_to_project({
            'project_id': project.id,
            'file_path': '/test/files/main.py',
            'file_name': 'main.py',
            'file_type': '.py',
            'file_size': 2048,
            'relative_path': 'src/main.py',
            'lines_of_code': 150,
            'owner': 'Alice',
            'editors': ['Bob', 'Charlie']
        })
        
        self.assertIsNotNone(file.id)
        self.assertEqual(file.file_name, 'main.py')
        self.assertEqual(file.lines_of_code, 150)
        self.assertEqual(file.owner, 'Alice')
        self.assertEqual(len(file.editors), 2)
    
    # ============ CONTRIBUTOR TESTS ============
    
    def test_add_contributors_with_metrics(self):
        """Test adding contributors with contribution metrics"""
        project = self.db.create_project({
            'name': 'Contrib Test',
            'file_path': '/test/contrib',
            'project_type': 'code'
        })
        
        contributor = self.db.add_contributor_to_project({
            'project_id': project.id,
            'name': 'John Doe',
            'contributor_identifier': 'john@example.com',
            'commit_count': 50,
            'lines_added': 1000,
            'lines_deleted': 200,
            'contribution_percent': 45.5
        })
        
        self.assertIsNotNone(contributor.id)
        self.assertEqual(contributor.commit_count, 50)
        self.assertEqual(contributor.lines_added, 1000)
        self.assertEqual(contributor.contribution_percent, 45.5)
    
    def test_update_contributor_metrics(self):
        """Test updating contributor metrics"""
        project = self.db.create_project({
            'name': 'Update Test',
            'file_path': '/test/update',
            'project_type': 'code'
        })
        
        contributor = self.db.add_contributor_to_project({
            'project_id': project.id,
            'name': 'Jane',
            'contributor_identifier': 'jane@example.com',
            'commit_count': 10
        })
        
        # Get session to update
        session = self.db.get_session()
        try:
            c = session.query(Contributor).filter(Contributor.id == contributor.id).first()
            c.commit_count = 20
            c.lines_added = 500
            session.commit()
        finally:
            session.close()
        
        # Verify update
        contributors = self.db.get_contributors_for_project(project.id)
        self.assertEqual(contributors[0].commit_count, 20)
        self.assertEqual(contributors[0].lines_added, 500)
    
    # ============ KEYWORD TESTS ============
    
    def test_add_keywords(self):
        """Test adding keywords to a project"""
        project = self.db.create_project({
            'name': 'Keyword Test',
            'file_path': '/test/keywords',
            'project_type': 'code'
        })
        
        # Add multiple keywords
        self.db.add_keyword({
            'project_id': project.id,
            'keyword': 'python',
            'score': 10.0,
            'category': 'language'
        })
        
        self.db.add_keyword({
            'project_id': project.id,
            'keyword': 'django',
            'score': 8.5,
            'category': 'framework'
        })
        
        keywords = self.db.get_keywords_for_project(project.id)
        self.assertEqual(len(keywords), 2)
        # Should be sorted by score descending
        self.assertEqual(keywords[0].keyword, 'python')
        self.assertEqual(keywords[1].keyword, 'django')
    
    # ============ PROJECT TO_DICT TEST - FIXED ============
    
    def test_project_to_dict(self):
        """Test converting project to dictionary - FIXED"""
        project = self.db.create_project({
            'name': 'Dict Test',
            'file_path': '/test/dict',
            'description': 'Test project',
            'project_type': 'code',
            'languages': ['Python'],
            'frameworks': ['Django']
        })
        
        # FIXED: Don't include counts by default (avoids DetachedInstanceError)
        project_dict = project.to_dict(include_counts=False)
        
        self.assertEqual(project_dict['name'], 'Dict Test')
        self.assertEqual(project_dict['project_type'], 'code')
        self.assertEqual(project_dict['languages'], ['Python'])
        self.assertEqual(project_dict['frameworks'], ['Django'])
        # Counts should not be included
        self.assertNotIn('file_count_actual', project_dict)
    
    def test_project_to_dict_with_counts(self):
        """Test to_dict with counts when session is active"""
        project = self.db.create_project({
            'name': 'Dict Test 2',
            'file_path': '/test/dict2',
            'project_type': 'code'
        })
        
        # Add a file
        self.db.add_file_to_project({
            'project_id': project.id,
            'file_path': '/test/file.py',
            'file_name': 'file.py',
            'file_type': '.py'
        })
        
        # Get project with eager loading
        loaded_project = self.db.get_project(project.id)
        
        # Now counts will work because relationships are loaded
        project_dict = loaded_project.to_dict(include_counts=True)
        
        self.assertEqual(project_dict['file_count_actual'], 1)
    
    # ============ JSON FIELD TESTS ============
    
    def test_empty_json_fields(self):
        """Test handling empty JSON fields"""
        project = self.db.create_project({
            'name': 'Empty JSON',
            'file_path': '/test/empty',
            'project_type': 'code'
        })
        
        # Should return empty lists for unset JSON fields
        self.assertEqual(project.languages, [])
        self.assertEqual(project.frameworks, [])
        self.assertEqual(project.skills, [])
        self.assertEqual(project.tags, [])
        self.assertEqual(project.success_metrics, {})
    
    # ============ UTILITY TESTS ============
    
    def test_clear_all_data(self):
        """Test clearing all data"""
        # Create some data
        project = self.db.create_project({
            'name': 'Clear Test',
            'file_path': '/test/clear',
            'project_type': 'code'
        })
        
        self.db.add_file_to_project({
            'project_id': project.id,
            'file_path': '/test/file.py',
            'file_name': 'file.py',
            'file_type': '.py'
        })
        
        # Clear all data
        self.db.clear_all_data()
        
        # Verify everything is gone
        stats = self.db.get_stats()
        self.assertEqual(stats['total_projects'], 0)
        self.assertEqual(stats['total_files'], 0)
    
    def test_get_stats(self):
        """Test getting database statistics"""
        # Create some data
        self.db.create_project({
            'name': 'Stats Test 1',
            'file_path': '/test/stats1',
            'project_type': 'code',
            'is_featured': True
        })
        
        self.db.create_project({
            'name': 'Stats Test 2',
            'file_path': '/test/stats2',
            'project_type': 'code',
            'is_featured': False
        })
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_projects'], 2)
        self.assertEqual(stats['featured_projects'], 1)
    
    # ============ DATABASE MANAGER CONTEXT TEST ============
    
    def test_context_manager(self):
        """Test using DatabaseManager as context manager"""
        test_path = os.path.join(self.test_dir, 'context_test.db')
        
        with DatabaseManager(test_path) as db:
            project = db.create_project({
                'name': 'Context Test',
                'file_path': '/test/context',
                'project_type': 'code'
            })
            self.assertIsNotNone(project.id)
        
        # Database should be closed automatically
        # Verify we can still access the file
        self.assertTrue(os.path.exists(test_path))


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)  