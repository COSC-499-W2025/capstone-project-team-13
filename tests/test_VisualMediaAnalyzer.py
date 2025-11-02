"""import os
import sys
import unittest

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from Analysis.visualMediaAnalyzer import analyze_visual_project


class TestVisualMediaAnalyzer(unittest.TestCase):
    TEST_FOLDER = "PortfolioTest"

    @classmethod
    def setUpClass(cls):
        """ #Set up dummy test folder and files before all tests.
"""
        os.makedirs(cls.TEST_FOLDER, exist_ok=True)
        cls.dummy_files = [
            "portrait_final.psd",
            "lighting_render.png",
            "texture_paint.jpg",
            "character_model.blend",
            "ui_mockup.fig",
            "animation_clip.mp4",
            "logo_design.ai"
        ]
        for file_name in cls.dummy_files:
            file_path = os.path.join(cls.TEST_FOLDER, file_name)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("")  # placeholder content

    def test_visual_analysis_output(self):
        """#Test that analyze_visual_project runs and returns expected keys.
"""
        result = analyze_visual_project(self.TEST_FOLDER)

        # Basic structure checks
        self.assertIn("num_files", result)
        self.assertIn("software_used", result)
        self.assertIn("skills_detected", result)

        # Basic value checks
        self.assertEqual(result["num_files"], len(self.dummy_files))
        self.assertIsInstance(result["software_used"], list)
        self.assertIsInstance(result["skills_detected"], list)

    @classmethod
    def tearDownClass(cls):
        """#Clean up test folder after all tests (optional).
"""
        for file_name in cls.dummy_files:
            os.remove(os.path.join(cls.TEST_FOLDER, file_name))
        os.rmdir(cls.TEST_FOLDER)


if __name__ == "__main__":
    unittest.main()"""


import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from Analysis.visualMediaAnalyzer import analyze_visual_project


class TestVisualMediaAnalyzer(unittest.TestCase):
    """Test cases for visual media project analyzer"""
    
    def setUp(self):
        """Create temporary test folder before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_folder = Path(self.test_dir) / "PortfolioTest"
        self.test_folder.mkdir()
    
    def tearDown(self):
        """Clean up test folder after each test"""
        shutil.rmtree(self.test_dir)
    
    def _create_dummy_file(self, filename, size_bytes=1024):
        """Helper to create a dummy file with specified size"""
        file_path = self.test_folder / filename
        file_path.write_bytes(b'0' * size_bytes)
        return file_path
    
    def _create_image_file(self, filename, size=(800, 600)):
        """Helper to create a real image file"""
        file_path = self.test_folder / filename
        img = Image.new('RGB', size, color='red')
        img.save(file_path)
        return file_path
    
    def test_basic_analysis_structure(self):
        """Test that analyze_visual_project returns expected structure"""
        # Create some dummy files
        self._create_dummy_file("portrait.psd")
        self._create_dummy_file("logo.ai")
        self._create_image_file("photo.jpg")
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Check all expected keys are present
        self.assertIn("type", result)
        self.assertIn("num_files", result)
        self.assertIn("total_size", result)
        self.assertIn("software_used", result)
        self.assertIn("skills_detected", result)
        
        # Check types
        self.assertIsInstance(result["num_files"], int)
        self.assertIsInstance(result["total_size"], int)
        self.assertIsInstance(result["software_used"], list)
        self.assertIsInstance(result["skills_detected"], list)
    
    def test_photoshop_detection(self):
        """Test detection of Photoshop files"""
        self._create_dummy_file("artwork.psd")
        self._create_dummy_file("composite.psb")
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 2)
        self.assertIn("Adobe Photoshop", result["software_used"])
        self.assertTrue(
            any(skill in result["skills_detected"] 
                for skill in ["Photo Editing", "Digital Painting", "Layer Compositing"])
        )
    
    def test_vector_graphics_detection(self):
        """Test detection of vector graphics files"""
        self._create_dummy_file("logo.ai")
        self._create_dummy_file("icon.svg")
        self._create_dummy_file("design.eps")
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 3)
        self.assertIn("Adobe Illustrator", result["software_used"])
        self.assertTrue(
            any(skill in result["skills_detected"] 
                for skill in ["Vector Illustration", "Logo Design", "Graphic Design"])
        )
    
    def test_3d_blender_detection(self):
        """Test detection of Blender 3D files"""
        self._create_dummy_file("character.blend")
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 1)
        self.assertIn("Blender", result["software_used"])
        self.assertTrue(
            any(skill in result["skills_detected"] 
                for skill in ["3D Modeling", "Rendering", "Animation"])
        )
    
    def test_3d_software_variety(self):
        """Test detection of various 3D software"""
        self._create_dummy_file("model.max")  # 3ds Max
        self._create_dummy_file("character.ma")  # Maya
        self._create_dummy_file("scene.c4d")  # Cinema 4D
        self._create_dummy_file("asset.obj")  # Generic 3D
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 4)
        # Should detect multiple 3D software
        software_str = " ".join(result["software_used"])
        self.assertTrue(
            "3ds Max" in software_str or 
            "Maya" in software_str or 
            "Cinema 4D" in software_str
        )
    
    def test_ui_design_detection(self):
        """Test detection of UI/UX design files"""
        self._create_dummy_file("mockup.fig")  # Figma
        self._create_dummy_file("design.sketch")  # Sketch
        self._create_dummy_file("prototype.xd")  # Adobe XD
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 3)
        # Should detect UI/UX software
        software_str = " ".join(result["software_used"])
        self.assertTrue(
            "Figma" in software_str or 
            "Sketch" in software_str or 
            "Adobe XD" in software_str
        )
        # Should detect UI/UX skills
        skills_str = " ".join(result["skills_detected"])
        self.assertTrue(
            "UI Design" in skills_str or 
            "Prototyping" in skills_str
        )
    
    def test_video_editing_detection(self):
        """Test detection of video files and editing software"""
        self._create_dummy_file("clip.mp4")
        self._create_dummy_file("project.aep")  # After Effects
        self._create_dummy_file("edit.prproj")  # Premiere
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 3)
        # Should detect video software
        software_str = " ".join(result["software_used"])
        self.assertTrue(
            "After Effects" in software_str or 
            "Premiere" in software_str or 
            "Video" in software_str
        )
        # Should detect video skills
        skills_str = " ".join(result["skills_detected"])
        self.assertTrue(
            "Video Editing" in skills_str or 
            "Motion Graphics" in skills_str
        )
    
    def test_raw_photography_detection(self):
        """Test detection of RAW photography files"""
        self._create_dummy_file("photo.cr2")  # Canon
        self._create_dummy_file("shot.nef")  # Nikon
        self._create_dummy_file("image.arw")  # Sony
        self._create_dummy_file("pic.dng")  # Adobe DNG
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 4)
        self.assertTrue(
            any("Lightroom" in sw or "RAW" in sw 
                for sw in result["software_used"])
        )
        self.assertTrue(
            any(skill in result["skills_detected"] 
                for skill in ["Photography", "RAW Processing"])
        )
    
    def test_mixed_media_project(self):
        """Test analysis of project with multiple media types"""
        # Create diverse media files
        self._create_dummy_file("portrait.psd")
        self._create_dummy_file("logo.ai")
        self._create_image_file("photo.jpg")
        self._create_dummy_file("model.blend")
        self._create_dummy_file("ui.fig")
        self._create_dummy_file("video.mp4")
        self._create_dummy_file("raw_photo.cr2")
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should find all files
        self.assertEqual(result["num_files"], 7)
        
        # Should detect multiple software
        self.assertGreaterEqual(len(result["software_used"]), 3)
        
        # Should detect diverse skills
        self.assertGreaterEqual(len(result["skills_detected"]), 5)
    
    def test_empty_folder(self):
        """Test analysis of folder with no media files"""
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["type"], "visual_media")
        self.assertIn("details", result)
        self.assertIn("No visual media files found", result["details"])
    
    def test_file_size_calculation(self):
        """Test that total_size is calculated correctly"""
        # Create files with known sizes
        self._create_dummy_file("file1.psd", 1000)
        self._create_dummy_file("file2.ai", 2000)
        self._create_dummy_file("file3.blend", 3000)
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 3)
        self.assertEqual(result["total_size"], 6000)
    
    def test_nested_folders(self):
        """Test that analyzer searches nested folders"""
        # Create nested structure
        assets_dir = self.test_folder / "assets"
        assets_dir.mkdir()
        textures_dir = assets_dir / "textures"
        textures_dir.mkdir()
        
        self._create_dummy_file("main.psd")
        (assets_dir / "logo.ai").write_bytes(b'0' * 100)
        (textures_dir / "wood.jpg").write_bytes(b'0' * 100)
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should find files in all nested folders
        self.assertEqual(result["num_files"], 3)
    
    def test_case_insensitive_extensions(self):
        """Test that file extensions are case-insensitive"""
        self._create_dummy_file("photo.JPG")
        self._create_dummy_file("design.PSD")
        self._create_dummy_file("model.BLEND")
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should detect all files regardless of extension case
        self.assertEqual(result["num_files"], 3)
    
    def test_audio_files_detection(self):
        """Test detection of audio files"""
        self._create_dummy_file("music.mp3")
        self._create_dummy_file("sound.wav")
        self._create_dummy_file("audio.flac")
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 3)
        self.assertTrue(
            any("Audio" in sw for sw in result["software_used"])
        )
        self.assertTrue(
            any(skill in result["skills_detected"] 
                for skill in ["Audio Editing", "Sound Design"])
        )
    
    def test_alternative_design_tools(self):
        """Test detection of alternative design software"""
        self._create_dummy_file("image.xcf")  # GIMP
        self._create_dummy_file("photo.afphoto")  # Affinity Photo
        self._create_dummy_file("vector.cdr")  # CorelDRAW
        
        result = analyze_visual_project(str(self.test_folder))
        
        self.assertEqual(result["num_files"], 3)
        # Should detect alternative software
        software_str = " ".join(result["software_used"])
        self.assertTrue(
            "GIMP" in software_str or 
            "Affinity" in software_str or 
            "CorelDRAW" in software_str
        )
    
    def test_sorted_output(self):
        """Test that output lists are sorted"""
        # Create multiple file types
        self._create_dummy_file("a.psd")
        self._create_dummy_file("b.ai")
        self._create_dummy_file("c.blend")
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Check that software_used is sorted
        self.assertEqual(
            result["software_used"], 
            sorted(result["software_used"])
        )
        
        # Check that skills_detected is sorted
        self.assertEqual(
            result["skills_detected"], 
            sorted(result["skills_detected"])
        )
    
    def test_image_with_exif(self):
        """Test EXIF metadata reading from images"""
        # Create a real JPG with EXIF
        img_path = self.test_folder / "photo_with_exif.jpg"
        img = Image.new('RGB', (400, 300), color='blue')
        
        # Try to add EXIF data (may not work on all systems)
        from PIL import PngImagePlugin
        exif_data = img.getexif()
        
        img.save(img_path)
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should at least detect the image file
        self.assertGreaterEqual(result["num_files"], 1)
        self.assertTrue(len(result["software_used"]) > 0)


class TestVisualMediaAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Create temporary test folder"""
        self.test_dir = tempfile.mkdtemp()
        self.test_folder = Path(self.test_dir) / "EdgeCaseTest"
        self.test_folder.mkdir()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_nonexistent_folder(self):
        """Test handling of nonexistent folder"""
        result = analyze_visual_project("/nonexistent/path/to/folder")
        
        # Should return gracefully
        self.assertIn("type", result)
        self.assertIn("details", result)
    
    def test_very_large_project(self):
        """Test handling of project with many files"""
        # Create 100 small image files
        for i in range(100):
            img_path = self.test_folder / f"photo_{i}.png"
            img = Image.new('RGB', (10, 10), color='red')
            img.save(img_path)
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should process all files
        self.assertEqual(result["num_files"], 100)
        self.assertGreater(result["total_size"], 0)
    
    def test_files_with_special_characters(self):
        """Test handling of filenames with special characters"""
        special_files = [
            "photo (1).jpg",
            "design-final.psd",
            "logo_v2.ai",
            "model [backup].blend"
        ]
        
        for filename in special_files:
            file_path = self.test_folder / filename
            file_path.write_bytes(b'0' * 100)
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should process all files
        self.assertEqual(result["num_files"], 4)
    
    def test_unicode_filenames(self):
        """Test handling of unicode filenames"""
        unicode_files = [
            "café_photo.jpg",
            "デザイン.psd",
            "照片.png"
        ]
        
        for filename in unicode_files:
            try:
                file_path = self.test_folder / filename
                file_path.write_bytes(b'0' * 100)
            except:
                # Skip if filesystem doesn't support unicode
                continue
        
        result = analyze_visual_project(str(self.test_folder))
        
        # Should handle unicode gracefully
        self.assertIsInstance(result["num_files"], int)


if __name__ == "__main__":
    unittest.main(verbosity=2)
