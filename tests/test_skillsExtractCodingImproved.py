import unittest
import os
import sys
from pathlib import Path
import tempfile
from pprint import pprint

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.skillsExtractCodingImproved import analyze_coding_skills_refined

class TestCodingSkillAnalyzer(unittest.TestCase):

    def setUp(self):
        # testing project structure
        self.test_dir = tempfile.TemporaryDirectory()
        root = self.test_dir.name
        os.makedirs(os.path.join(root, "src"), exist_ok=True)
        os.makedirs(os.path.join(root, "app"), exist_ok=True)
        os.makedirs(os.path.join(root, "tests"), exist_ok=True)
        os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(root, "docs"), exist_ok=True)

        # Test File content
        files_content = {
            "src/main.py": """
import pandas as pd
import numpy as np
async def process_data():
    pass
""",
            "src/ml_model.py": """
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
# machine learning pipeline
""",
            "app/web_app.js": """
import React from 'react';
// REST API call
fetch('/api/data')
""",
            "tests/test_main.py": """
import pytest
def test_example():
    assert True
""",
            "scripts/db_setup.sql": """
CREATE TABLE users (id INT, name VARCHAR(100));
SELECT * FROM users JOIN orders ON users.id = orders.user_id;
""",
        }

        # Write files
        for path, content in files_content.items():
            file_path = os.path.join(root, path)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        self.root = root

    def tearDown(self):
        # Clean up temporary directory
        self.test_dir.cleanup()

    def test_python_detection(self):
        result = analyze_coding_skills_refined(self.root)
        python_skill = result["skills"].get("Python")
        self.assertIsNotNone(python_skill, "Python skill should be detected")
        self.assertIn("pandas", python_skill["subskills"]["libraries"])
        self.assertIn("numpy", python_skill["subskills"]["libraries"])
        self.assertIn("async", python_skill["subskills"]["language_features"])

    def test_ml_detection(self):
        result = analyze_coding_skills_refined(self.root)
        ml_skill = result["skills"].get("Machine Learning")
        self.assertIsNotNone(ml_skill, "Machine Learning skill should be detected")
        self.assertIn("tensorflow", ml_skill["subskills"]["libraries"])
        self.assertIn("sklearn", ml_skill["subskills"]["libraries"])
        self.assertIn("RandomForestClassifier", ml_skill["subskills"]["algorithms"])

    def test_web_dev_detection(self):
        result = analyze_coding_skills_refined(self.root)
        web_skill = result["skills"].get("Web Development")
        self.assertIsNotNone(web_skill, "Web Development should be detected")
        self.assertIn("react", web_skill["subskills"]["libraries"])
        self.assertIn("rest api", web_skill["subskills"]["multi_word"])

    def test_sql_detection(self):
        result = analyze_coding_skills_refined(self.root)
        sql_skill = result["skills"].get("SQL")
        self.assertIsNotNone(sql_skill, "SQL should be detected")
        self.assertIn("join", sql_skill["subskills"]["commands"])
        self.assertIn("select", sql_skill["subskills"]["commands"])

    def test_folder_weighting(self):
        # Core folder "src" should give higher weight
        result = analyze_coding_skills_refined(self.root)
        python_score = result["skills"]["Python"]["score"]
        ml_score = result["skills"]["Machine Learning"]["score"]
        web_score = result["skills"]["Web Development"]["score"]
        sql_score = result["skills"]["SQL"]["score"]

        # Python and ML in "src" should be higher than Web in "app" or SQL in "scripts"
        self.assertTrue(python_score > web_score)
        self.assertTrue(ml_score > sql_score)

    def test_python_subskills_structure(self):
        result = analyze_coding_skills_refined(self.root)
        python_skill = result["skills"]["Python"]

    # At least one meaningful subskill category must exist
        self.assertTrue(
            any(
                category in python_skill["subskills"]
                for category in ["libraries", "language_features", "keywords"]
            ),
            "Python should have at least one subskill category"
    )

    def test_relational_db_detection(self):
        result = analyze_coding_skills_refined(self.root)
        db = result["skills"].get("Relational Databases")
        self.assertIsNotNone(db)

    def test_multi_word_case_insensitive(self):
        file_path = os.path.join(self.root, "src", "api.js")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("REST API endpoint")

        result = analyze_coding_skills_refined(self.root)
        web_skill = result["skills"].get("Web Development")

        self.assertIsNotNone(web_skill)
        self.assertIn("multi_word", web_skill["subskills"])
        self.assertIn("rest api", web_skill["subskills"]["multi_word"])



    def test_skill_combinations(self):
        result = analyze_coding_skills_refined(self.root)
        combos = result["skill_combinations"]
        # Python and ML co-occur in src -> combination should exist
        self.assertIn(tuple(sorted(["Machine Learning", "Python"])), combos)
        # Python and Web should co-occur in different folders -> smaller normalized combo
        self.assertIn(tuple(sorted(["Python", "Web Development"])), combos)
        # Python and SQL co-occur in different folders
        self.assertIn(tuple(sorted(["Python", "SQL"])), combos)


if __name__ == "__main__":
    unittest.main()
