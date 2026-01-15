"""
Unit tests for file_hasher.py
Tests SHA-256 file hashing functionality
"""

import unittest
import os
import tempfile
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestFileHasher(unittest.TestCase):
    """Test file hashing functionality"""
    
    def setUp(self):
        """Create temporary directory and test files"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test file with known content
        self.test_file1 = os.path.join(self.test_dir, "test1.txt")
        with open(self.test_file1, 'w') as f:
            f.write("Hello, World!")
        
        # Create identical file
        self.test_file2 = os.path.join(self.test_dir, "test2.txt")
        with open(self.test_file2, 'w') as f:
            f.write("Hello, World!")
        
        # Create different file
        self.test_file3 = os.path.join(self.test_dir, "test3.txt")
        with open(self.test_file3, 'w') as f:
            f.write("Different content")
        
        # Create binary file
        self.test_binary = os.path.join(self.test_dir, "test.bin")
        with open(self.test_binary, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')
        
        # Create large file (for chunk testing)
        self.large_file = os.path.join(self.test_dir, "large.txt")
        with open(self.large_file, 'w') as f:
            # Write 100KB of data
            f.write("x" * 100000)
    
    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir)
    
    def test_import(self):
        """Test that file_hasher can be imported"""
        try:
            from src.Analysis.file_hasher import compute_file_hash
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import compute_file_hash")
    
    def test_hash_returns_string(self):
        """Test that hash function returns a string"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash_result = compute_file_hash(self.test_file1)
        self.assertIsInstance(hash_result, str)
    
    def test_hash_length(self):
        """Test that hash is correct length (SHA-256 = 64 hex chars)"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash_result = compute_file_hash(self.test_file1)
        self.assertEqual(len(hash_result), 64)
    
    def test_hash_is_hexadecimal(self):
        """Test that hash contains only hexadecimal characters"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash_result = compute_file_hash(self.test_file1)
        # Should only contain 0-9 and a-f
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
    
    def test_identical_files_same_hash(self):
        """Test that identical files produce identical hashes"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash1 = compute_file_hash(self.test_file1)
        hash2 = compute_file_hash(self.test_file2)
        
        self.assertEqual(hash1, hash2)
    
    def test_different_files_different_hash(self):
        """Test that different files produce different hashes"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash1 = compute_file_hash(self.test_file1)
        hash3 = compute_file_hash(self.test_file3)
        
        self.assertNotEqual(hash1, hash3)
    
    def test_hash_consistency(self):
        """Test that hashing same file twice gives same result"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash1 = compute_file_hash(self.test_file1)
        hash2 = compute_file_hash(self.test_file1)
        
        self.assertEqual(hash1, hash2)
    
    def test_binary_file_hash(self):
        """Test that binary files can be hashed"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash_result = compute_file_hash(self.test_binary)
        
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 64)
    
    def test_large_file_hash(self):
        """Test that large files can be hashed (chunk reading)"""
        from src.Analysis.file_hasher import compute_file_hash
        
        hash_result = compute_file_hash(self.large_file)
        
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 64)
    
    def test_empty_file_hash(self):
        """Test that empty files can be hashed"""
        from src.Analysis.file_hasher import compute_file_hash
        
        empty_file = os.path.join(self.test_dir, "empty.txt")
        open(empty_file, 'w').close()
        
        hash_result = compute_file_hash(empty_file)
        
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 64)
        # SHA-256 of empty file is known constant
        self.assertEqual(hash_result, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    
    def test_nonexistent_file(self):
        """Test behavior with nonexistent file"""
        from src.Analysis.file_hasher import compute_file_hash
        
        nonexistent = os.path.join(self.test_dir, "does_not_exist.txt")
        
        # Should return empty string or handle gracefully
        hash_result = compute_file_hash(nonexistent)
        self.assertEqual(hash_result, "")
    
    def test_known_hash_value(self):
        """Test against a known SHA-256 hash"""
        from src.Analysis.file_hasher import compute_file_hash
        
        # "Hello, World!" has a known SHA-256 hash
        hash_result = compute_file_hash(self.test_file1)
        
        # Expected SHA-256 hash of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(hash_result, expected)


if __name__ == '__main__':
    unittest.main()