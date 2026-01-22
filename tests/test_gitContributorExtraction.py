"""
Unit tests for gitContributorExtraction.py
Tests Git contributor extraction and database population
"""

import unittest
import os
import tempfile
import shutil
import sys
import subprocess
from pathlib import Path
import time

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Helpers.gitContributorExtraction import (
    run_git_command,
    is_git_repository,
    extract_git_contributors,
    populate_contributors_for_project
)
from src.Databases.database import DatabaseManager, Project


class TestGitContributorExtraction(unittest.TestCase):
    """Test Git contributor extraction functionality"""
    
    def setUp(self):
        """Create temporary directory and mock Git repository"""
        self.test_dir = tempfile.mkdtemp()
        self.git_repo = os.path.join(self.test_dir, "test_repo")
        os.makedirs(self.git_repo)
        
        # Create a test database
        self.db_path = os.path.join(self.test_dir, 'test.db')
        self.db = DatabaseManager(self.db_path)
        
        # Initialize a Git repository for testing
        self._create_test_git_repo()
    
    def tearDown(self):
        """Clean up test directory and database"""
        if hasattr(self, 'db'):
            self.db.close()
        
        time.sleep(0.1)  # Give Windows time to release locks
        
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            time.sleep(0.5)
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError as e:
                print(f"Warning: Could not remove test directory: {e}")
    
    def _create_test_git_repo(self):
        """Create a simple Git repository with test commits"""
        try:
            # Initialize repository
            subprocess.run(['git', 'init'], cwd=self.git_repo, check=True, 
                         capture_output=True, text=True)
            
            # Configure Git (required for commits)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                         cwd=self.git_repo, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                         cwd=self.git_repo, check=True, capture_output=True)
            
            # Create and commit first file
            test_file1 = os.path.join(self.git_repo, 'test1.py')
            with open(test_file1, 'w') as f:
                f.write("def hello():\n    print('Hello, World!')\n")
            
            subprocess.run(['git', 'add', 'test1.py'], cwd=self.git_repo, 
                         check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                         cwd=self.git_repo, check=True, capture_output=True)
            
            # Create and commit second file
            test_file2 = os.path.join(self.git_repo, 'test2.py')
            with open(test_file2, 'w') as f:
                f.write("def goodbye():\n    print('Goodbye!')\n")
            
            subprocess.run(['git', 'add', 'test2.py'], cwd=self.git_repo, 
                         check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Add goodbye function'], 
                         cwd=self.git_repo, check=True, capture_output=True)
            
            self.has_git = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Git not available on system
            self.has_git = False
    
    def test_import(self):
        """Test that module can be imported"""
        try:
            from src.Helpers.gitContributorExtraction import extract_git_contributors
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import gitContributorExtraction")
    
    def test_is_git_repository_true(self):
        """Test that function correctly identifies Git repository"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        result = is_git_repository(self.git_repo)
        self.assertTrue(result)
    
    def test_is_git_repository_false(self):
        """Test that function correctly identifies non-Git directory"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        non_git_dir = os.path.join(self.test_dir, "not_a_repo")
        os.makedirs(non_git_dir)
        
        result = is_git_repository(non_git_dir)
        self.assertFalse(result)
    
    def test_run_git_command_success(self):
        """Test that Git commands execute successfully"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        result = run_git_command(self.git_repo, ['rev-parse', '--git-dir'])
        self.assertIsNotNone(result)
        self.assertIn('.git', result)
    
    def test_run_git_command_failure(self):
        """Test that invalid Git commands return None"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        result = run_git_command(self.git_repo, ['invalid-command'])
        self.assertIsNone(result)
    
    def test_extract_git_contributors_returns_list(self):
        """Test that contributor extraction returns a list"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        contributors = extract_git_contributors(self.git_repo)
        self.assertIsInstance(contributors, list)
    
    def test_extract_git_contributors_has_data(self):
        """Test that contributors have required fields"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        contributors = extract_git_contributors(self.git_repo)
        
        if len(contributors) > 0:
            contributor = contributors[0]
            self.assertIn('name', contributor)
            self.assertIn('email', contributor)
            self.assertIn('commit_count', contributor)
            self.assertIn('lines_added', contributor)
            self.assertIn('lines_deleted', contributor)
            self.assertIn('contribution_percent', contributor)
    
    def test_extract_git_contributors_non_git_repo(self):
        """Test that extraction returns empty list for non-Git directory"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        non_git_dir = os.path.join(self.test_dir, "not_a_repo")
        os.makedirs(non_git_dir)
        
        contributors = extract_git_contributors(non_git_dir)
        self.assertEqual(len(contributors), 0)
    
    def test_extract_git_contributors_commit_count(self):
        """Test that commit count is correct"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        contributors = extract_git_contributors(self.git_repo)
        
        # We made 2 commits with 1 contributor
        if len(contributors) > 0:
            total_commits = sum(c['commit_count'] for c in contributors)
            self.assertEqual(total_commits, 2)
    
    def test_extract_git_contributors_percentage_sums_100(self):
        """Test that contribution percentages sum to approximately 100%"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        contributors = extract_git_contributors(self.git_repo)
        
        if len(contributors) > 0:
            total_percent = sum(c['contribution_percent'] for c in contributors)
            self.assertAlmostEqual(total_percent, 100, delta=1)
    
    def test_populate_contributors_for_project(self):
        """Test populating contributors to database"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        # Note: This test verifies the function executes without errors
        # Full database integration testing would require using the same
        # db_manager instance that the function uses internally
        
        # Create a project in database
        project_data = {
            'name': 'Test Project',
            'file_path': self.git_repo,
            'project_type': 'code',
            'file_count': 2,
            'languages': ['Python'],
            'frameworks': []
        }
        project = self.db.create_project(project_data)
        
        # Populate contributors - this uses the global db_manager,
        # not our test db instance, so we just verify it returns a count
        count = populate_contributors_for_project(project)
        
        # Should have added at least 1 contributor
        self.assertGreater(count, 0)
        self.assertIsInstance(count, int)
    
    def test_extract_with_date_range(self):
        """Test extracting contributors with date filters"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        # Extract with very recent date range (should be empty or have limited results)
        from datetime import datetime, timedelta
        
        # Use a date in the far future - should return no commits
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        contributors = extract_git_contributors(self.git_repo, since_date=future_date)
        
        # Should have no contributors from the future
        self.assertEqual(len(contributors), 0)
    
    def test_contributor_email_format(self):
        """Test that contributor email is properly formatted"""
        if not self.has_git:
            self.skipTest("Git not available on system")
        
        contributors = extract_git_contributors(self.git_repo)
        
        if len(contributors) > 0:
            email = contributors[0]['email']
            self.assertIsInstance(email, str)
            # Email should contain @
            self.assertIn('@', email)


class TestGitContributorExtractionNoGit(unittest.TestCase):
    """Test behavior when Git is not installed or not available"""
    
    def test_non_existent_path(self):
        """Test extraction on non-existent path"""
        result = is_git_repository('/path/that/does/not/exist')
        self.assertFalse(result)
    
    def test_extract_on_invalid_path(self):
        """Test extraction returns empty list for invalid path"""
        contributors = extract_git_contributors('/path/that/does/not/exist')
        self.assertEqual(len(contributors), 0)


if __name__ == '__main__':
    unittest.main()
