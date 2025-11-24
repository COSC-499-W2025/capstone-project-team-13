import sys
import os
import unittest
from datetime import datetime, timezone, timedelta

# Add src folder to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from Analysis.importanceScores import calculate_importance_score

class SimpleProject:
    """Lightweight project class for unit testing importance scoring"""
    def __init__(self, name):
        self.name = name
        self.date_modified = None
        self.lines_of_code = 0
        self.word_count = 0
        self.file_count = 0
        self.contributors = []
        self.keywords = []
        self.files = []
        self.skills = []
        self.languages = []
        self.tags = []

class TestImportanceScoring(unittest.TestCase):
    """Unit tests for importance scoring"""

    def setUp(self):
        self.now = datetime.now(timezone.utc)
        
        # Empty project
        self.empty_project = SimpleProject("Empty")

        # Large recent project
        self.large_project = SimpleProject("Large")
        self.large_project.date_modified = self.now
        self.large_project.lines_of_code = 5000
        self.large_project.word_count = 2000
        self.large_project.file_count = 50
        self.large_project.contributors = ["Alice", "Bob"]
        self.large_project.keywords = ["AI", "ML"]
        self.large_project.files = ["f1", "f2"]
        self.large_project.skills = ["Python", "SQL"]
        self.large_project.languages = ["Python"]
        self.large_project.tags = ["backend", "data"]

        # Old project
        self.old_project = SimpleProject("Old")
        self.old_project.date_modified = self.now - timedelta(days=400)
        self.old_project.lines_of_code = 100
        self.old_project.word_count = 50
        self.old_project.file_count = 1

    def test_score_empty_project(self):
        score = calculate_importance_score(self.empty_project)
        self.assertGreaterEqual(score, 0)
        self.assertLess(score, 10)

    def test_score_large_recent_project(self):
        score = calculate_importance_score(self.large_project)
        self.assertGreater(score, 40)
        self.assertLessEqual(score, 100)

    def test_score_old_project(self):
        score = calculate_importance_score(self.old_project)
        self.assertGreater(score, 0)
        self.assertLess(score, 30)

    def test_score_range(self):
        for project in [self.empty_project, self.large_project, self.old_project]:
            score = calculate_importance_score(project)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

if __name__ == "__main__":
    unittest.main()
