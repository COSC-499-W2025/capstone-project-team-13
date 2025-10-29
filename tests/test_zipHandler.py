import unittest
import os
import sys
import tempfile
import zipfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from Extraction.zipHandler import (
    validate_zip_file, extract_zip, get_zip_contents, 
    count_files_in_zip, ZipExtractionError
)
from Helpers.fileFormatCheck import InvalidFileFormatError


class TestZipValidation(unittest.TestCase):
    """Test cases for ZIP file validation"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, "test.zip")
        
    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)
    
    def test_validate_valid_zip(self):
        """Test validating a proper ZIP file"""
        # Create a valid ZIP file
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("test.txt", "test content")
        
        result = validate_zip_file(self.zip_file)
        self.assertTrue(result)
    
    def test_validate_invalid_zip(self):
        """Test validating a corrupted ZIP file"""
        # Create a fake ZIP file
        with open(self.zip_file, 'w') as f:
            f.write("not a zip file")
        
        with self.assertRaises(ZipExtractionError):
            validate_zip_file(self.zip_file)
    
    def test_validate_nonexistent_zip(self):
        """Test validating a non-existent file"""
        with self.assertRaises(ZipExtractionError):
            validate_zip_file("nonexistent.zip")
    
    def test_validate_wrong_extension(self):
        """Test validating file with wrong extension"""
        txt_file = os.path.join(self.test_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("text content")
        
        with self.assertRaises(ZipExtractionError):
            validate_zip_file(txt_file)


class TestZipExtraction(unittest.TestCase):
    """Test cases for ZIP file extraction"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, "test.zip")
        
        # Create a ZIP with some files
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("file1.txt", "content 1")
            zf.writestr("file2.txt", "content 2")
            zf.writestr("folder/file3.txt", "content 3")
    
    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)
    
    def test_extract_to_default_location(self):
        """Test extracting to default temp directory"""
        extract_path = extract_zip(self.zip_file)
        
        self.assertTrue(os.path.exists(extract_path))
        self.assertTrue(os.path.exists(os.path.join(extract_path, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(extract_path, "file2.txt")))
        
        # Cleanup
        shutil.rmtree(extract_path)
    
    def test_extract_to_specific_location(self):
        """Test extracting to specified directory"""
        extract_to = os.path.join(self.test_dir, "extracted")
        os.makedirs(extract_to)
        
        extract_path = extract_zip(self.zip_file, extract_to)
        
        self.assertEqual(extract_path, extract_to)
        self.assertTrue(os.path.exists(os.path.join(extract_to, "file1.txt")))
    
    def test_extract_invalid_zip(self):
        """Test extracting an invalid ZIP file"""
        bad_zip = os.path.join(self.test_dir, "bad.zip")
        with open(bad_zip, 'w') as f:
            f.write("not a zip")
        
        with self.assertRaises(ZipExtractionError):
            extract_zip(bad_zip)


class TestZipContents(unittest.TestCase):
    """Test cases for ZIP content inspection"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, "test.zip")
        
        # Create a ZIP with various files
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("file1.txt", "content 1")
            zf.writestr("file2.json", '{"key": "value"}')
            zf.writestr("folder/", "")  # Empty folder
            zf.writestr("folder/nested.py", "print('hello')")
    
    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)
    
    def test_get_zip_contents(self):
        """Test getting list of all items in ZIP"""
        contents = get_zip_contents(self.zip_file)
        
        self.assertEqual(len(contents), 4)
        self.assertIn("file1.txt", contents)
        self.assertIn("file2.json", contents)
        self.assertIn("folder/", contents)
        self.assertIn("folder/nested.py", contents)
    
    def test_count_files_in_zip(self):
        """Test counting files (excluding directories)"""
        count = count_files_in_zip(self.zip_file)
        
        # Should count 3 files, not the folder/
        self.assertEqual(count, 3)
    
    def test_empty_zip(self):
        """Test working with an empty ZIP file"""
        empty_zip = os.path.join(self.test_dir, "empty.zip")
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass  # Create empty ZIP
        
        contents = get_zip_contents(empty_zip)
        count = count_files_in_zip(empty_zip)
        
        self.assertEqual(len(contents), 0)
        self.assertEqual(count, 0)


class TestZipIntegration(unittest.TestCase):
    """Integration tests for ZIP handling workflow"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, "project.zip")
        
        # Create a realistic project ZIP
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("README.md", "# Project")
            zf.writestr("config.json", '{"version": "1.0"}')
            zf.writestr("src/main.py", "def main(): pass")
            zf.writestr("src/utils.py", "def helper(): pass")
            zf.writestr("tests/test_main.py", "import unittest")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """Test complete ZIP processing workflow"""
        # Validate
        self.assertTrue(validate_zip_file(self.zip_file))
        
        # Get contents
        contents = get_zip_contents(self.zip_file)
        self.assertEqual(len(contents), 5)
        
        # Count files
        file_count = count_files_in_zip(self.zip_file)
        self.assertEqual(file_count, 5)
        
        # Extract
        extract_path = extract_zip(self.zip_file)
        self.assertTrue(os.path.exists(os.path.join(extract_path, "README.md")))
        self.assertTrue(os.path.exists(os.path.join(extract_path, "src", "main.py")))
        
        # Cleanup
        shutil.rmtree(extract_path)


if __name__ == '__main__':
    unittest.main()