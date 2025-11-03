# tests/test_mediaProjectScanner.py
"""
Tests for the visual media project scanner
(Photography, graphic design, video editing, 3D modeling, UI/UX design)
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from PIL import Image

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.mediaProjectScanner import MediaProjectScanner, scan_media_project
from src.Databases.database import db_manager


class TestMediaProjectScanner(unittest.TestCase):
    """Test cases for MediaProjectScanner"""
    
    def setUp(self):
        """Create a temporary test project directory"""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_media_project"
        self.project_dir.mkdir()
        
        # Create some test media files
        self._create_test_files()
        
        # Clean database before each test
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up test directory and database"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def _create_test_files(self):
        """Create sample media files for testing"""
        
        # Create PNG images
        img1 = self.project_dir / "photo1.png"
        img2 = self.project_dir / "design.png"
        self._create_test_image(img1, (800, 600))
        self._create_test_image(img2, (1920, 1080))
        
        # Create JPG images
        jpg1 = self.project_dir / "portrait.jpg"
        self._create_test_image(jpg1, (1200, 1600))
        
        # Create Photoshop file (just a dummy file)
        psd_file = self.project_dir / "artwork.psd"
        psd_file.write_bytes(b"PSD dummy content")
        
        # Create vector file
        svg_file = self.project_dir / "logo.svg"
        svg_file.write_text('<svg><circle cx="50" cy="50" r="40"/></svg>')
        
        # Create Blender file
        blend_file = self.project_dir / "model.blend"
        blend_file.write_bytes(b"BLEND dummy content")
        
        # Create a README
        readme = self.project_dir / "README.md"
        readme.write_text("""
# Portfolio Photography Project

This project showcases portrait photography work using natural lighting.
Keywords: portrait, natural light, outdoor photography, editorial
""")
        
        # Create a description file
        desc = self.project_dir / "description.txt"
        desc.write_text("""
Professional photography portfolio featuring landscape and portrait work.
""")
        
        # Create a nested directory with more media
        assets_dir = self.project_dir / "assets"
        assets_dir.mkdir()
        
        nested_img = assets_dir / "thumbnail.png"
        self._create_test_image(nested_img, (400, 400))
        
        # Create a directory that should be skipped
        cache_dir = self.project_dir / "Cache"
        cache_dir.mkdir()
        
        skip_file = cache_dir / "temp.png"
        self._create_test_image(skip_file, (100, 100))
    
    def _create_test_image(self, path: Path, size: tuple):
        """Helper to create a test image file"""
        img = Image.new('RGB', size, color='red')
        img.save(path)
    
    def test_initialization_valid_path(self):
        """Test scanner initialization with valid path"""
        scanner = MediaProjectScanner(str(self.project_dir))
        
        self.assertEqual(scanner.project_name, "test_media_project")
        self.assertTrue(scanner.project_path.exists())
    
    def test_initialization_invalid_path(self):
        """Test scanner initialization with invalid path"""
        with self.assertRaises(ValueError):
            MediaProjectScanner("/nonexistent/path")
    
    def test_initialization_file_not_directory(self):
        """Test scanner initialization with file instead of directory"""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test")
        
        with self.assertRaises(ValueError):
            MediaProjectScanner(str(test_file))
    
    def test_find_media_files(self):
        """Test that media files are found correctly"""
        scanner = MediaProjectScanner(str(self.project_dir))
        scanner._find_files()
        
        # Should find 7 media files (skip Cache directory)
        self.assertEqual(len(scanner.media_files), 7)
        
        # Check that Cache was skipped
        file_paths = [str(f) for f in scanner.media_files]
        self.assertFalse(any('Cache' in path for path in file_paths))
    
    def test_find_text_files(self):
        """Test that text files are found for keyword extraction"""
        scanner = MediaProjectScanner(str(self.project_dir))
        scanner._find_files()
        
        # Should find 2 text files (README.md and description.txt)
        self.assertEqual(len(scanner.text_files), 2)
    
    def test_analyze_media(self):
        """Test media analysis"""
        scanner = MediaProjectScanner(str(self.project_dir))
        scanner._find_files()
        scanner._analyze_media()
        
        # Should detect some software based on file extensions
        self.assertGreater(len(scanner.software_used), 0)
        
        # Should detect some skills
        self.assertGreater(len(scanner.skills_detected), 0)
    
    def test_extract_keywords(self):
        """Test keyword extraction from text files"""
        scanner = MediaProjectScanner(str(self.project_dir))
        scanner._find_files()
        scanner._extract_keywords()
        
        # Should extract some keywords
        self.assertGreater(len(scanner.all_keywords), 0)
        
        # Keywords should be tuples of (keyword, score)
        for keyword, score in scanner.all_keywords:
            self.assertIsInstance(keyword, str)
            self.assertIsInstance(score, (int, float))
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        scanner = MediaProjectScanner(str(self.project_dir))
        scanner._find_files()
        metrics = scanner._calculate_metrics()
        
        # Check that metrics are calculated
        self.assertIn('file_count', metrics)
        self.assertIn('total_size_bytes', metrics)
        self.assertIn('total_size_mb', metrics)
        
        # File count should match
        self.assertEqual(metrics['file_count'], 7)
        
        # Size should be > 0
        self.assertGreater(metrics['total_size_bytes'], 0)
    
    def test_scan_and_store(self):
        """Test complete scan and store workflow"""
        scanner = MediaProjectScanner(str(self.project_dir))
        project_id = scanner.scan_and_store()
        
        # Should return a valid project ID
        self.assertIsNotNone(project_id)
        self.assertIsInstance(project_id, int)
        
        # Verify project is in database
        project = db_manager.get_project(project_id)
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "test_media_project")
        self.assertEqual(project.project_type, "visual_media")
        
        # Verify software/skills were stored
        self.assertGreater(len(project.languages), 0)  # Software stored in languages
        self.assertGreater(len(project.skills), 0)
        
        # Verify keywords were stored
        keywords = db_manager.get_keywords_for_project(project_id)
        self.assertGreater(len(keywords), 0)
    
    def test_scan_media_project_function(self):
        """Test convenience function"""
        project_id = scan_media_project(str(self.project_dir))
        
        # Should return valid project ID
        self.assertIsNotNone(project_id)
        
        # Verify in database
        project = db_manager.get_project(project_id)
        self.assertIsNotNone(project)
    
    def test_scan_empty_directory(self):
        """Test scanning directory with no media files"""
        empty_dir = Path(self.test_dir) / "empty_project"
        empty_dir.mkdir()
        
        # Create only text files
        (empty_dir / "README.txt").write_text("This is a readme")
        (empty_dir / "notes.txt").write_text("Some notes")
        
        scanner = MediaProjectScanner(str(empty_dir))
        project_id = scanner.scan_and_store()
        
        # Should return None (no media files found)
        self.assertIsNone(project_id)
    
    def test_rescan_existing_project(self):
        """Test rescanning a project that already exists"""
        # First scan
        scanner1 = MediaProjectScanner(str(self.project_dir))
        project_id1 = scanner1.scan_and_store()
        
        # Verify it detects existing project
        existing = db_manager.get_project_by_path(str(scanner1.project_path))
        self.assertIsNotNone(existing)
        self.assertEqual(existing.id, project_id1)


class TestMediaProjectScannerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def test_mixed_media_types(self):
        """Test handling projects with various media types"""
        project_dir = Path(self.test_dir) / "mixed_media"
        project_dir.mkdir()
        
        # Create different media types
        # Image
        img = Image.new('RGB', (500, 500), color='blue')
        img.save(project_dir / "image.png")
        
        # PSD
        (project_dir / "design.psd").write_bytes(b"PSD content")
        
        # Video (dummy)
        (project_dir / "video.mp4").write_bytes(b"MP4 content")
        
        # 3D model
        (project_dir / "model.blend").write_bytes(b"BLEND content")
        
        scanner = MediaProjectScanner(str(project_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
        
        # Verify multiple software/skills detected
        project = db_manager.get_project(project_id)
        self.assertGreater(len(project.languages), 1)  # Multiple software
    
    def test_unicode_filenames(self):
        """Test handling files with unicode characters"""
        project_dir = Path(self.test_dir) / "unicode_project"
        project_dir.mkdir()
        
        # Create file with unicode name
        unicode_file = project_dir / "café_photo_你好.png"
        img = Image.new('RGB', (300, 300), color='green')
        img.save(unicode_file)
        
        scanner = MediaProjectScanner(str(project_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
    
    def test_very_large_project(self):
        """Test handling project with many files"""
        project_dir = Path(self.test_dir) / "large_project"
        project_dir.mkdir()
        
        # Create many small images
        for i in range(50):
            img_path = project_dir / f"photo_{i}.png"
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_path)
        
        scanner = MediaProjectScanner(str(project_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
        
        # Verify high file count
        project = db_manager.get_project(project_id)
        self.assertEqual(project.file_count, 50)


if __name__ == '__main__':
    unittest.main(verbosity=2)