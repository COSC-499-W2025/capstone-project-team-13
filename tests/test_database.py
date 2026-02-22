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

try:
    from Databases.database import DatabaseManager, Project, File, Contributor, Keyword, User, Education, WorkHistory
except ImportError:
    try:
        from database import DatabaseManager, Project, File, Contributor, Keyword, User, Education, WorkHistory
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
    
    def test_resume_bullets_operations(self):
        """Test saving, retrieving, and deleting resume bullets"""
        # Create project
        project = self.db.create_project({
            'name': 'Test Project',
            'file_path': '/test/bullets',
            'project_type': 'code',
            'languages': ['Python'],
            'frameworks': ['Django']
        })
        
        # Save bullets
        bullets = [
            'Developed REST API using Python and Django',
            'Implemented CI/CD pipeline reducing deployment time by 40%',
            'Architected scalable backend handling 10K+ requests'
        ]
        header = 'Test Project | Python, Django'
        ats_score = 85.5
        
        success = self.db.save_resume_bullets(project.id, bullets, header, ats_score)
        self.assertTrue(success)
        
        # Retrieve bullets via db_manager
        bullets_data = self.db.get_resume_bullets(project.id)
        self.assertIsNotNone(bullets_data)
        self.assertEqual(bullets_data['num_bullets'], 3)
        self.assertEqual(bullets_data['header'], header)
        self.assertEqual(bullets_data['ats_score'], ats_score)
        self.assertEqual(len(bullets_data['bullets']), 3)
        
        # Retrieve via project
        project = self.db.get_project(project.id)
        self.assertIsNotNone(project.bullets)
        self.assertEqual(project.bullets['num_bullets'], 3)
        
        # Check to_dict includes bullets
        project_dict = project.to_dict()
        self.assertIn('bullets', project_dict)
        self.assertIsNotNone(project_dict['bullets'])
        
        # Delete bullets
        success = self.db.delete_resume_bullets(project.id)
        self.assertTrue(success)
        
        # Verify deletion
        bullets_data = self.db.get_resume_bullets(project.id)
        self.assertIsNone(bullets_data)

    # ============ USER TESTS ============

    def test_create_user(self):
        """Test creating a user with required fields"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'password_hash': 'hashed_password_123',
        })

        self.assertIsNotNone(user.id)
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'jane@example.com')
        self.assertEqual(user.password_hash, 'hashed_password_123')
        self.assertIsNone(user.portfolio)
        self.assertIsNone(user.resume)

    def test_create_user_duplicate_email(self):
        """Test that creating two users with the same email fails"""
        self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'duplicate@example.com',
            'password_hash': 'hash1',
        })

        with self.assertRaises(Exception):
            self.db.create_user({
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'duplicate@example.com',
                'password_hash': 'hash2',
            })

    def test_get_user_by_id(self):
        """Test retrieving a user by ID"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'getbyid@example.com',
            'password_hash': 'hashed_password_123',
        })

        retrieved = self.db.get_user(user.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, user.id)
        self.assertEqual(retrieved.email, 'getbyid@example.com')

    def test_get_user_nonexistent_id(self):
        """Test that retrieving a nonexistent user returns None"""
        retrieved = self.db.get_user(99999)
        self.assertIsNone(retrieved)

    def test_get_user_by_email(self):
        """Test retrieving a user by email"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'byemail@example.com',
            'password_hash': 'hashed_password_123',
        })

        retrieved = self.db.get_user_by_email('byemail@example.com')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, user.id)

    def test_get_user_by_email_nonexistent(self):
        """Test that retrieving a nonexistent email returns None"""
        retrieved = self.db.get_user_by_email('nobody@example.com')
        self.assertIsNone(retrieved)

    def test_update_user(self):
        """Test updating user fields"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'update@example.com',
            'password_hash': 'hashed_password_123',
        })

        updated = self.db.update_user(user.id, {
            'first_name': 'Janet',
            'last_name': 'Smith',
        })

        self.assertIsNotNone(updated)
        self.assertEqual(updated.first_name, 'Janet')
        self.assertEqual(updated.last_name, 'Smith')
        # Email should remain unchanged
        self.assertEqual(updated.email, 'update@example.com')

    def test_update_user_nonexistent(self):
        """Test that updating a nonexistent user returns None"""
        result = self.db.update_user(99999, {'first_name': 'Ghost'})
        self.assertIsNone(result)

    def test_update_user_portfolio_and_resume(self):
        """Test setting portfolio and resume JSON fields"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'portfolio@example.com',
            'password_hash': 'hashed_password_123',
        })

        portfolio_data = {
            'projects': ['Project A', 'Project B'],
            'summary': 'Full-stack developer'
        }
        resume_data = {
            'objective': 'Seeking a senior role',
            'skills': ['Python', 'Django', 'SQLite']
        }

        updated = self.db.update_user(user.id, {
            'portfolio': portfolio_data,
            'resume': resume_data,
        })

        self.assertEqual(updated.portfolio, portfolio_data)
        self.assertEqual(updated.resume, resume_data)

        # Verify persistence by re-fetching
        fetched = self.db.get_user(user.id)
        self.assertEqual(fetched.portfolio, portfolio_data)
        self.assertEqual(fetched.resume, resume_data)

    def test_delete_user(self):
        """Test deleting a user"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'delete@example.com',
            'password_hash': 'hashed_password_123',
        })

        result = self.db.delete_user(user.id)
        self.assertTrue(result)
        self.assertIsNone(self.db.get_user(user.id))

    def test_delete_user_nonexistent(self):
        """Test that deleting a nonexistent user returns False"""
        result = self.db.delete_user(99999)
        self.assertFalse(result)

    def test_delete_user_cascades_to_education_and_work(self):
        """Test that deleting a user also deletes their education and work history"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'cascade@example.com',
            'password_hash': 'hashed_password_123',
        })

        self.db.add_education({
            'user_id': user.id,
            'institution': 'UBC',
            'degree_type': "Bachelor's",
            'topic': 'Computer Science',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2024, 4, 30),
        })

        self.db.add_work_history({
            'user_id': user.id,
            'company': 'Acme Corp',
            'role': 'Developer',
            'start_date': datetime(2022, 6, 1),
            'end_date': None,
        })

        # Verify they exist
        self.assertEqual(len(self.db.get_education_for_user(user.id)), 1)
        self.assertEqual(len(self.db.get_work_history_for_user(user.id)), 1)

        # Delete user
        self.db.delete_user(user.id)

        # Verify cascade
        self.assertEqual(len(self.db.get_education_for_user(user.id)), 0)
        self.assertEqual(len(self.db.get_work_history_for_user(user.id)), 0)

    def test_user_to_dict(self):
        """Test User to_dict excludes password_hash"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'todict@example.com',
            'password_hash': 'secret_hash',
        })

        user_dict = user.to_dict()

        self.assertEqual(user_dict['first_name'], 'Jane')
        self.assertEqual(user_dict['email'], 'todict@example.com')
        self.assertNotIn('password_hash', user_dict)

    # ============ EDUCATION TESTS ============

    def test_add_education(self):
        """Test adding an education entry"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'edu@example.com',
            'password_hash': 'hashed_password_123',
        })

        education = self.db.add_education({
            'user_id': user.id,
            'institution': 'UBC Okanagan',
            'degree_type': "Bachelor's",
            'topic': 'Computer Science',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2024, 4, 30),
        })

        self.assertIsNotNone(education.id)
        self.assertEqual(education.institution, 'UBC Okanagan')
        self.assertEqual(education.degree_type, "Bachelor's")
        self.assertEqual(education.topic, 'Computer Science')
        self.assertEqual(education.end_date, datetime(2024, 4, 30))

    def test_add_education_present(self):
        """Test adding an education entry with no end date (present)"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'edupresent@example.com',
            'password_hash': 'hashed_password_123',
        })

        education = self.db.add_education({
            'user_id': user.id,
            'institution': 'UBC Okanagan',
            'degree_type': "Master's",
            'topic': 'Computer Science',
            'start_date': datetime(2024, 9, 1),
            'end_date': None,
        })

        self.assertIsNone(education.end_date)
        # to_dict should show 'Present'
        edu_dict = education.to_dict()
        self.assertEqual(edu_dict['end_date'], 'Present')

    def test_get_education_for_user(self):
        """Test retrieving all education entries for a user, sorted by start_date descending"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'edulist@example.com',
            'password_hash': 'hashed_password_123',
        })

        # Add older entry first
        self.db.add_education({
            'user_id': user.id,
            'institution': 'College A',
            'degree_type': 'Diploma',
            'topic': 'Business',
            'start_date': datetime(2018, 1, 1),
            'end_date': datetime(2020, 6, 30),
        })

        # Add newer entry second
        self.db.add_education({
            'user_id': user.id,
            'institution': 'University B',
            'degree_type': "Bachelor's",
            'topic': 'Economics',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2024, 4, 30),
        })

        education_list = self.db.get_education_for_user(user.id)
        self.assertEqual(len(education_list), 2)
        # Newer entry should come first (descending order)
        self.assertEqual(education_list[0].institution, 'University B')
        self.assertEqual(education_list[1].institution, 'College A')

    def test_get_education_for_user_empty(self):
        """Test retrieving education for a user with no entries"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'eduempty@example.com',
            'password_hash': 'hashed_password_123',
        })

        education_list = self.db.get_education_for_user(user.id)
        self.assertEqual(len(education_list), 0)

    def test_update_education(self):
        """Test updating an education entry"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'eduupdate@example.com',
            'password_hash': 'hashed_password_123',
        })

        education = self.db.add_education({
            'user_id': user.id,
            'institution': 'Old University',
            'degree_type': "Bachelor's",
            'topic': 'Physics',
            'start_date': datetime(2019, 9, 1),
            'end_date': None,
        })

        updated = self.db.update_education(education.id, {
            'institution': 'New University',
            'topic': 'Mathematics',
            'end_date': datetime(2023, 6, 30),
        })

        self.assertIsNotNone(updated)
        self.assertEqual(updated.institution, 'New University')
        self.assertEqual(updated.topic, 'Mathematics')
        self.assertEqual(updated.end_date, datetime(2023, 6, 30))

    def test_update_education_nonexistent(self):
        """Test that updating a nonexistent education entry returns None"""
        result = self.db.update_education(99999, {'institution': 'Ghost'})
        self.assertIsNone(result)

    def test_delete_education(self):
        """Test deleting an education entry"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'edudel@example.com',
            'password_hash': 'hashed_password_123',
        })

        education = self.db.add_education({
            'user_id': user.id,
            'institution': 'UBC',
            'degree_type': "Bachelor's",
            'topic': 'Computer Science',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2024, 4, 30),
        })

        result = self.db.delete_education(education.id)
        self.assertTrue(result)
        self.assertEqual(len(self.db.get_education_for_user(user.id)), 0)

    def test_delete_education_nonexistent(self):
        """Test that deleting a nonexistent education entry returns False"""
        result = self.db.delete_education(99999)
        self.assertFalse(result)

    def test_education_to_dict(self):
        """Test Education to_dict with and without end date"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'edudict@example.com',
            'password_hash': 'hashed_password_123',
        })

        # With end date
        edu_completed = self.db.add_education({
            'user_id': user.id,
            'institution': 'UBC',
            'degree_type': "Bachelor's",
            'topic': 'Computer Science',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2024, 4, 30),
        })

        edu_dict = edu_completed.to_dict()
        self.assertEqual(edu_dict['institution'], 'UBC')
        self.assertIn('2024', edu_dict['end_date'])

        # Without end date
        edu_current = self.db.add_education({
            'user_id': user.id,
            'institution': 'MIT',
            'degree_type': "Master's",
            'topic': 'AI',
            'start_date': datetime(2024, 9, 1),
            'end_date': None,
        })

        edu_dict_current = edu_current.to_dict()
        self.assertEqual(edu_dict_current['end_date'], 'Present')

    # ============ WORK HISTORY TESTS ============

    def test_add_work_history(self):
        """Test adding a work history entry"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'work@example.com',
            'password_hash': 'hashed_password_123',
        })

        work = self.db.add_work_history({
            'user_id': user.id,
            'company': 'Acme Corp',
            'role': 'Software Developer',
            'start_date': datetime(2022, 6, 1),
            'end_date': datetime(2024, 1, 15),
        })

        self.assertIsNotNone(work.id)
        self.assertEqual(work.company, 'Acme Corp')
        self.assertEqual(work.role, 'Software Developer')
        self.assertEqual(work.end_date, datetime(2024, 1, 15))

    def test_add_work_history_present(self):
        """Test adding a work history entry with no end date (present)"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'workpresent@example.com',
            'password_hash': 'hashed_password_123',
        })

        work = self.db.add_work_history({
            'user_id': user.id,
            'company': 'Tech Inc',
            'role': 'Senior Developer',
            'start_date': datetime(2023, 3, 1),
            'end_date': None,
        })

        self.assertIsNone(work.end_date)
        work_dict = work.to_dict()
        self.assertEqual(work_dict['end_date'], 'Present')

    def test_get_work_history_for_user(self):
        """Test retrieving all work history entries for a user, sorted by start_date descending"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'worklist@example.com',
            'password_hash': 'hashed_password_123',
        })

        # Add older job first
        self.db.add_work_history({
            'user_id': user.id,
            'company': 'Old Company',
            'role': 'Intern',
            'start_date': datetime(2020, 5, 1),
            'end_date': datetime(2020, 8, 31),
        })

        # Add newer job second
        self.db.add_work_history({
            'user_id': user.id,
            'company': 'New Company',
            'role': 'Developer',
            'start_date': datetime(2022, 1, 10),
            'end_date': None,
        })

        work_list = self.db.get_work_history_for_user(user.id)
        self.assertEqual(len(work_list), 2)
        # Newer entry should come first (descending order)
        self.assertEqual(work_list[0].company, 'New Company')
        self.assertEqual(work_list[1].company, 'Old Company')

    def test_get_work_history_for_user_empty(self):
        """Test retrieving work history for a user with no entries"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'workempty@example.com',
            'password_hash': 'hashed_password_123',
        })

        work_list = self.db.get_work_history_for_user(user.id)
        self.assertEqual(len(work_list), 0)

    def test_update_work_history(self):
        """Test updating a work history entry"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'workupdate@example.com',
            'password_hash': 'hashed_password_123',
        })

        work = self.db.add_work_history({
            'user_id': user.id,
            'company': 'Old Corp',
            'role': 'Junior Dev',
            'start_date': datetime(2021, 3, 1),
            'end_date': None,
        })

        updated = self.db.update_work_history(work.id, {
            'company': 'New Corp',
            'role': 'Senior Dev',
            'end_date': datetime(2024, 12, 31),
        })

        self.assertIsNotNone(updated)
        self.assertEqual(updated.company, 'New Corp')
        self.assertEqual(updated.role, 'Senior Dev')
        self.assertEqual(updated.end_date, datetime(2024, 12, 31))

    def test_update_work_history_nonexistent(self):
        """Test that updating a nonexistent work history entry returns None"""
        result = self.db.update_work_history(99999, {'company': 'Ghost'})
        self.assertIsNone(result)

    def test_delete_work_history(self):
        """Test deleting a work history entry"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'workdel@example.com',
            'password_hash': 'hashed_password_123',
        })

        work = self.db.add_work_history({
            'user_id': user.id,
            'company': 'Acme',
            'role': 'Developer',
            'start_date': datetime(2022, 6, 1),
            'end_date': datetime(2024, 1, 15),
        })

        result = self.db.delete_work_history(work.id)
        self.assertTrue(result)
        self.assertEqual(len(self.db.get_work_history_for_user(user.id)), 0)

    def test_delete_work_history_nonexistent(self):
        """Test that deleting a nonexistent work history entry returns False"""
        result = self.db.delete_work_history(99999)
        self.assertFalse(result)

    def test_work_history_to_dict(self):
        """Test WorkHistory to_dict with and without end date"""
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'workdict@example.com',
            'password_hash': 'hashed_password_123',
        })

        # With end date
        work_completed = self.db.add_work_history({
            'user_id': user.id,
            'company': 'Acme',
            'role': 'Developer',
            'start_date': datetime(2020, 1, 1),
            'end_date': datetime(2022, 6, 30),
        })

        work_dict = work_completed.to_dict()
        self.assertEqual(work_dict['company'], 'Acme')
        self.assertIn('2022', work_dict['end_date'])

        # Without end date
        work_current = self.db.add_work_history({
            'user_id': user.id,
            'company': 'Tech Inc',
            'role': 'Senior Dev',
            'start_date': datetime(2023, 1, 1),
            'end_date': None,
        })

        work_dict_current = work_current.to_dict()
        self.assertEqual(work_dict_current['end_date'], 'Present')

    # ============ CLEAR ALL DATA TEST (UPDATED) ============

    def test_clear_all_data_includes_user_tables(self):
        """Test that clear_all_data also clears users, education, and work history"""
        # Create a user with education and work history
        user = self.db.create_user({
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'clearuser@example.com',
            'password_hash': 'hashed_password_123',
        })

        self.db.add_education({
            'user_id': user.id,
            'institution': 'UBC',
            'degree_type': "Bachelor's",
            'topic': 'Computer Science',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2024, 4, 30),
        })

        self.db.add_work_history({
            'user_id': user.id,
            'company': 'Acme',
            'role': 'Developer',
            'start_date': datetime(2022, 6, 1),
            'end_date': None,
        })

        # Also create a project so we verify everything clears together
        self.db.create_project({
            'name': 'Clear Test',
            'file_path': '/test/clearall',
            'project_type': 'code',
        })

        # Clear everything
        self.db.clear_all_data()

        # Verify all tables are empty
        self.assertIsNone(self.db.get_user(user.id))
        self.assertEqual(len(self.db.get_education_for_user(user.id)), 0)
        self.assertEqual(len(self.db.get_work_history_for_user(user.id)), 0)
        stats = self.db.get_stats()
        self.assertEqual(stats['total_projects'], 0)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)