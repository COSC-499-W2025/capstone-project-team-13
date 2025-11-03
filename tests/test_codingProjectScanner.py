# tests/test_codingProjectScanner.py
"""
Tests for the coding project scanner
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.codingProjectScanner import CodingProjectScanner, scan_coding_project
from src.Databases.database import db_manager


class TestCodingProjectScanner(unittest.TestCase):
    """Test cases for CodingProjectScanner"""
    
    def setUp(self):
        """Create a temporary test project directory"""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()
        
        # Create some test code files
        self._create_test_files()
        
        # Clean database before each test
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up test directory and database"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def _create_test_files(self):
        """Create sample code files for testing"""
        
        # Python file with Django
        python_file = self.project_dir / "app.py"
        python_file.write_text("""
from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    # Main application view
    return HttpResponse("Hello World")

class UserModel:
    def __init__(self, name):
        self.name = name
""")
        
        # JavaScript file with React
        js_file = self.project_dir / "App.js"
        js_file.write_text("""
import React from 'react';

function App() {
    // React component for the main application
    return (
        <div className="App">
            <h1>Hello World</h1>
        </div>
    );
}

export default App;
""")
        
        # Another Python file
        utils_file = self.project_dir / "utils.py"
        utils_file.write_text("""
import json

def parse_data(data):
    # Parse JSON data
    return json.loads(data)

def format_output(result):
    # Format the output
    return str(result)
""")
        
        # Create a nested directory with code
        src_dir = self.project_dir / "src"
        src_dir.mkdir()
        
        nested_file = src_dir / "helper.py"
        nested_file.write_text("""
def calculate(a, b):
    # Simple calculation
    return a + b
""")
        
        # Create a directory that should be skipped
        node_modules = self.project_dir / "node_modules"
        node_modules.mkdir()
        
        skip_file = node_modules / "package.js"
        skip_file.write_text("// This should be skipped")
    
    def test_initialization_valid_path(self):
        """Test scanner initialization with valid path"""
        scanner = CodingProjectScanner(str(self.project_dir))
        
        self.assertEqual(scanner.project_name, "test_project")
        self.assertTrue(scanner.project_path.exists())
    
    def test_initialization_invalid_path(self):
        """Test scanner initialization with invalid path"""
        with self.assertRaises(ValueError):
            CodingProjectScanner("/nonexistent/path")
    
    def test_initialization_file_not_directory(self):
        """Test scanner initialization with file instead of directory"""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test")
        
        with self.assertRaises(ValueError):
            CodingProjectScanner(str(test_file))
    
    def test_find_code_files(self):
        """Test that code files are found correctly"""
        scanner = CodingProjectScanner(str(self.project_dir))
        scanner._find_code_files()
        
        # Should find 4 code files (skip node_modules)
        self.assertEqual(len(scanner.code_files), 4)
        
        # Check that node_modules was skipped
        file_paths = [str(f) for f in scanner.code_files]
        self.assertFalse(any('node_modules' in path for path in file_paths))
    
    def test_detect_languages(self):
        """Test language detection"""
        scanner = CodingProjectScanner(str(self.project_dir))
        scanner._find_code_files()
        scanner._detect_languages_and_frameworks()
        
        # Should detect Python and JavaScript
        self.assertIn("Python", scanner.languages)
        self.assertIn("JavaScript", scanner.languages)
    
    def test_detect_frameworks(self):
        """Test framework detection"""
        scanner = CodingProjectScanner(str(self.project_dir))
        scanner._find_code_files()
        scanner._detect_languages_and_frameworks()
        
        # Should detect Django and React
        self.assertIn("Django", scanner.frameworks)
        self.assertIn("React", scanner.frameworks)
    
    def test_extract_keywords(self):
        """Test keyword extraction from code"""
        scanner = CodingProjectScanner(str(self.project_dir))
        scanner._find_code_files()
        scanner._extract_keywords()
        
        # Should extract some keywords
        self.assertGreater(len(scanner.all_keywords), 0)
        
        # Keywords should be tuples of (keyword, score)
        for keyword, score in scanner.all_keywords:
            self.assertIsInstance(keyword, str)
            self.assertIsInstance(score, (int, float))
    
    def test_analyze_skills(self):
        """Test skills analysis"""
        scanner = CodingProjectScanner(str(self.project_dir))
        scanner._find_code_files()
        scanner._analyze_skills()
        
        # Should detect some skills
        if scanner.all_skills:
            # Skills should be dict with string keys and float values
            for skill, score in scanner.all_skills.items():
                self.assertIsInstance(skill, str)
                self.assertIsInstance(score, float)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        scanner = CodingProjectScanner(str(self.project_dir))
        scanner._find_code_files()
        metrics = scanner._calculate_metrics()
        
        # Check that metrics are calculated
        self.assertIn('lines_of_code', metrics)
        self.assertIn('file_count', metrics)
        self.assertIn('total_size_bytes', metrics)
        
        # Lines of code should be > 0
        self.assertGreater(metrics['lines_of_code'], 0)
        
        # File count should match
        self.assertEqual(metrics['file_count'], 4)
    
    def test_scan_and_store(self):
        """Test complete scan and store workflow"""
        scanner = CodingProjectScanner(str(self.project_dir))
        project_id = scanner.scan_and_store()
        
        # Should return a valid project ID
        self.assertIsNotNone(project_id)
        self.assertIsInstance(project_id, int)
        
        # Verify project is in database
        project = db_manager.get_project(project_id)
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "test_project")
        self.assertEqual(project.project_type, "code")
        
        # Verify languages and frameworks were stored
        self.assertIn("Python", project.languages)
        self.assertIn("JavaScript", project.languages)
        
        # Verify keywords were stored
        keywords = db_manager.get_keywords_for_project(project_id)
        self.assertGreater(len(keywords), 0)
    
    def test_scan_coding_project_function(self):
        """Test convenience function"""
        project_id = scan_coding_project(str(self.project_dir))
        
        # Should return valid project ID
        self.assertIsNotNone(project_id)
        
        # Verify in database
        project = db_manager.get_project(project_id)
        self.assertIsNotNone(project)
    
    def test_scan_empty_directory(self):
        """Test scanning directory with no code files"""
        empty_dir = Path(self.test_dir) / "empty_project"
        empty_dir.mkdir()
        
        # Create only non-code files
        (empty_dir / "README.txt").write_text("This is a readme")
        (empty_dir / "data.json").write_text('{"key": "value"}')
        
        scanner = CodingProjectScanner(str(empty_dir))
        project_id = scanner.scan_and_store()
        
        # Should return None (no code files found)
        self.assertIsNone(project_id)
    
    def test_rescan_existing_project(self):
        """Test rescanning a project that already exists"""
        # First scan
        scanner1 = CodingProjectScanner(str(self.project_dir))
        project_id1 = scanner1.scan_and_store()
        
        # Try to scan again (should detect existing)
        scanner2 = CodingProjectScanner(str(self.project_dir))
        
        # Mock user input to not rescan
        # (In actual use, this would prompt the user)
        # For testing, we just verify it detects existing project
        existing = db_manager.get_project_by_path(str(scanner1.project_path))
        self.assertIsNotNone(existing)
        self.assertEqual(existing.id, project_id1)


class TestCodingProjectScannerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def test_files_with_unicode(self):
        """Test handling files with unicode characters"""
        project_dir = Path(self.test_dir) / "unicode_project"
        project_dir.mkdir()
        
        # Create file with unicode
        unicode_file = project_dir / "unicode.py"
        unicode_file.write_text("""
# Test file with unicode: café, naïve, 你好
def greet():
    print("Hello 世界")
""", encoding='utf-8')
        
        scanner = CodingProjectScanner(str(project_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
    
    def test_very_large_file(self):
        """Test handling very large code files"""
        project_dir = Path(self.test_dir) / "large_project"
        project_dir.mkdir()
        
        # Create a large file
        large_file = project_dir / "large.py"
        with open(large_file, 'w') as f:
            for i in range(10000):
                f.write(f"# Comment line {i}\n")
                f.write(f"def function_{i}(): pass\n")
        
        scanner = CodingProjectScanner(str(project_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
        
        # Verify high line count
        project = db_manager.get_project(project_id)
        self.assertGreater(project.lines_of_code, 10000)


if __name__ == '__main__':
    unittest.main(verbosity=2)