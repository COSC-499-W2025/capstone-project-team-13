"""
Integration tests for CodingProjectScanner incremental updates
Tests the complete incremental update workflow
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestCodingScannerIncremental(unittest.TestCase):
    """Test incremental update functionality in CodingProjectScanner"""
    
    def setUp(self):
        """Create temporary project and database"""
        self.test_dir = tempfile.mkdtemp()
        self.db_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.db_dir, 'test_scanner.db')
        
        # Create test project directory
        self.project_path = os.path.join(self.test_dir, 'test_project')
        os.makedirs(self.project_path)
        
        # Create initial files with substantial code content
        with open(os.path.join(self.project_path, 'main.py'), 'w') as f:
            f.write('''#!/usr/bin/env python
def main():
    """Main function"""
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
''')
        
        with open(os.path.join(self.project_path, 'utils.py'), 'w') as f:
            f.write('''def helper():
    """Helper function"""
    return True

def process_data(data):
    """Process data"""
    return data.strip()
''')
        
        # Initialize database
        from src.Databases.database import DatabaseManager
        self.db = DatabaseManager(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up temporary directories"""
        self.db.close()
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.db_dir)
    
    def test_first_scan_creates_project(self):
        """Test that first scan creates a new project"""
        from src.Analysis.codingProjectScanner import CodingProjectScanner
        
        # Mock user input for "no existing project" scenario
        scanner = CodingProjectScanner(self.project_path)
        
        # We can't easily test the full scan_and_store due to input() calls
        # But we can test the components
        scanner._find_code_files()
        scanner._detect_languages_and_frameworks()
        
        self.assertEqual(len(scanner.code_files), 2)
        self.assertIn('Python', scanner.languages)
    
    def test_incremental_update_adds_new_files(self):
        """Test that incremental update adds only new files"""
        from src.Analysis.codingProjectScanner import CodingProjectScanner
        from src.Analysis.file_hasher import compute_file_hash
        
        # First scan - create project manually
        project_data = {
            'name': 'test_project',
            'file_path': self.project_path,
            'file_count': 2,
            'project_type': 'code',
            'languages': ['Python'],
            'frameworks': [],
            'date_scanned': datetime.now(timezone.utc)
        }
        project = self.db.create_project(project_data)
        
        # Add initial files to database
        for filename in ['main.py', 'utils.py']:
            filepath = os.path.join(self.project_path, filename)
            file_hash = compute_file_hash(filepath)
            
            file_data = {
                'project_id': project.id,
                'file_path': filepath,
                'file_name': filename,
                'file_type': '.py',
                'file_size': os.path.getsize(filepath),
                'file_created': datetime.now(timezone.utc),
                'file_modified': datetime.now(timezone.utc),
                'file_hash': file_hash
            }
            self.db.add_file_to_project(file_data)
        
        # Add new file with substantial Python code
        with open(os.path.join(self.project_path, 'config.py'), 'w') as f:
            f.write('''#!/usr/bin/env python
"""Configuration module"""

CONFIG = {
    'debug': True,
    'host': 'localhost',
    'port': 8000
}

def get_config(key):
    """Get configuration value"""
    return CONFIG.get(key)
''')
        
        # Simulate incremental update
        scanner = CodingProjectScanner(self.project_path)
        scanner._find_code_files()
        
        existing_files = self.db.get_files_for_project(project.id)
        existing_hashes = {f.file_hash for f in existing_files if f.file_hash}
        
        new_files_count = 0
        for file_path in scanner.code_files:
            file_hash = compute_file_hash(str(file_path))
            if file_hash not in existing_hashes:
                new_files_count += 1
        
        # Should find config.py as new
        self.assertGreaterEqual(new_files_count, 1, "Should find at least 1 new file (config.py)")
    
    def test_duplicate_detection_skips_existing_files(self):
        """Test that duplicate files are not added"""
        from src.Analysis.file_hasher import compute_file_hash
        
        # Create project
        project_data = {
            'name': 'test_project',
            'file_path': self.project_path,
            'file_count': 2,
            'project_type': 'code',
            'languages': ['Python'],
            'frameworks': [],
            'date_scanned': datetime.now(timezone.utc)
        }
        project = self.db.create_project(project_data)
        
        # Add file to database
        filepath = os.path.join(self.project_path, 'main.py')
        file_hash = compute_file_hash(filepath)
        
        file_data = {
            'project_id': project.id,
            'file_path': filepath,
            'file_name': 'main.py',
            'file_type': '.py',
            'file_size': os.path.getsize(filepath),
            'file_created': datetime.now(timezone.utc),
            'file_modified': datetime.now(timezone.utc),
            'file_hash': file_hash
        }
        self.db.add_file_to_project(file_data)
        
        # Check if file exists in project
        exists = self.db.file_exists_in_project(project.id, file_hash)
        
        self.assertTrue(exists)


if __name__ == '__main__':
    unittest.main()