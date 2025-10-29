import os
import sys
import unittest

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src")))

from Analysis.visualMediaAnalyzer import analyze_visual_project


class TestVisualMediaAnalyzer(unittest.TestCase):
    TEST_FOLDER = "PortfolioTest"

    @classmethod
    def setUpClass(cls):
        """Set up dummy test folder and files before all tests."""
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
        """Test that analyze_visual_project runs and returns expected keys."""
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
        """Clean up test folder after all tests (optional)."""
        for file_name in cls.dummy_files:
            os.remove(os.path.join(cls.TEST_FOLDER, file_name))
        os.rmdir(cls.TEST_FOLDER)


if __name__ == "__main__":
    unittest.main()
