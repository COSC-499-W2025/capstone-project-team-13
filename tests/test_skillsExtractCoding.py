import unittest
import os
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "analysis")))

from skillsExtractCoding import extract_skills_with_scores
from skillsExtractCoding import extract_skills_from_folder


class TestSkillExtraction(unittest.TestCase):

    # --- Basic Presence Tests ---
    def test_web_development_keywords(self):
        text = "This project uses HTML, CSS, and JavaScript with Flask for web applications."
        result = extract_skills_with_scores(text)
        self.assertIn("Web Development", result)
        self.assertTrue(result["Web Development"] > 0)

    def test_backend_and_database_skills(self):
        text = "The backend was built using Django and PostgreSQL with REST APIs."
        result = extract_skills_with_scores(text)
        self.assertIn("Backend Development", result)
        self.assertIn("Relational Databases", result)
        self.assertIn("API Development", result)

    def test_machine_learning_skills(self):
        text = "Model training with TensorFlow and Keras for regression tasks."
        result = extract_skills_with_scores(text)
        self.assertIn("Machine Learning", result)
        self.assertTrue(result["Machine Learning"] > 0)

    def test_devops_cloud_keywords(self):
        text = "The system runs on AWS with Docker containers and CI/CD pipelines."
        result = extract_skills_with_scores(text)
        self.assertIn("DevOps", result)
        self.assertIn("Cloud Computing", result)

    def test_game_and_3d_rendering(self):
        text = "Built using Unity and WebGL with shader programming for lighting and camera effects."
        result = extract_skills_with_scores(text)
        self.assertIn("Game Development", result)
        self.assertIn("3D Rendering", result)

    # --- New: Multi-word Keyword Handling ---
    def test_multiword_skill_ruby_on_rails(self):
        text = "This portfolio was developed using Ruby on Rails for the backend."
        result = extract_skills_with_scores(text)
        self.assertIn("Web Development", result)
        self.assertTrue(result["Web Development"] > 0)

    # --- Edge Cases ---
    def test_web_project_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # create multiple files
            file1 = Path(tmpdir) / "index.html"
            file1.write_text("<html><head></head><body>Hello</body></html>")

            file2 = Path(tmpdir) / "app.py"
            file2.write_text("from flask import Flask")

            result = extract_skills_from_folder(tmpdir, file_extensions=[".py", ".html"])
            self.assertIn("Web Development", result)
            self.assertIn("Frontend Development", result)
            self.assertIn("Backend Development", result)

    def test_empty_text_returns_empty_dict(self):
        result = extract_skills_with_scores("")
        self.assertEqual(result, {})

    def test_case_insensitivity(self):
        text = "HTML, Css, and JAVASCRIPT are used."
        result = extract_skills_with_scores(text)
        self.assertIn("Web Development", result)

    def test_no_matching_keywords(self):
        text = "This is a literature project analyzing novels and poems."
        result = extract_skills_with_scores(text)
        self.assertEqual(result, {})

    def test_tokenization_avoids_partial_matches(self):
        text = "We used NoSQL database."
        result = extract_skills_with_scores(text)
        self.assertIn("Non-Relational Databases", result)
        self.assertNotIn("Relational Databases", result)

    # --- Normalization ---
    def test_normalized_scores_sum_to_one(self):
        text = "Flask, Django, and PostgreSQL used together."
        result = extract_skills_with_scores(text)
        total = round(sum(result.values()), 2)
        # Should always sum exactly to 1.00 after rounding adjustment
        self.assertEqual(total, 1.00)


if __name__ == '__main__':
    unittest.main()