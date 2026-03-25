import sys
import os
import unittest
from datetime import datetime, timezone, timedelta

# Add project root to path so both `src.X` and internal `from src.X` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.importanceScores import calculate_importance_score

class SimpleProject:
    """Lightweight project class for unit testing importance scoring"""
    def __init__(self, name):
        self.id = None  
        self.name = name
        self.date_modified = None
        self.lines_of_code = 0
        self.word_count = 0
        self.file_count = 0
        self.total_size_bytes = 0
        self.project_type = 'text'  # Default to text project for testing
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


class TestCodingImportanceScoring(unittest.TestCase):
    """Tests for the coding project scorer (_score_coding_project)."""

    def setUp(self):
        self.now = datetime.now(timezone.utc)

    def _make(self, **kwargs):
        p = SimpleProject("test")
        p.project_type = "code"
        for k, v in kwargs.items():
            setattr(p, k, v)
        return p

    def test_coding_project_zero_loc_gives_low_score(self):
        p = self._make(lines_of_code=0, file_count=0)
        score = calculate_importance_score(p)
        self.assertGreaterEqual(score, 0)
        self.assertLess(score, 15)  # recency-only contribution at most

    def test_coding_project_large_gets_high_score(self):
        p = self._make(
            lines_of_code=5000,
            file_count=25,
            languages=["Python", "JavaScript"],
            tags=["backend", "api", "react"],
            skills=["Django", "REST", "SQL", "Docker"],
            date_modified=self.now,
        )
        score = calculate_importance_score(p)
        self.assertGreater(score, 60)
        self.assertLessEqual(score, 100)

    def test_coding_score_higher_than_equivalent_text_score(self):
        """A project with 5000 LOC should score better as 'code' than as 'text'
        (where word_count=0 would dominate)."""
        code_p = self._make(lines_of_code=5000, file_count=20, date_modified=self.now)
        text_p = self._make(lines_of_code=5000, file_count=20, date_modified=self.now)
        text_p.project_type = "text"
        text_p.word_count = 0  # code files have no word_count

        code_score = calculate_importance_score(code_p)
        text_score = calculate_importance_score(text_p)
        self.assertGreater(code_score, text_score)

    def test_coding_score_in_valid_range(self):
        for loc, files in [(0, 0), (100, 5), (1000, 10), (5000, 30)]:
            p = self._make(lines_of_code=loc, file_count=files, date_modified=self.now)
            score = calculate_importance_score(p)
            self.assertGreaterEqual(score, 0, f"Score < 0 for loc={loc}")
            self.assertLessEqual(score, 100, f"Score > 100 for loc={loc}")

    def test_directory_type_detection_routes_to_coding_scorer(self):
        """Ensure 'code' project_type doesn't fall through to text scorer."""
        p = self._make(lines_of_code=2000, file_count=15, date_modified=self.now)
        p.project_type = "code"
        score = calculate_importance_score(p)
        # With 2000 LOC: loc_score = 40, file_score = 60*0.2=12, recency=10 → ~42+
        self.assertGreater(score, 20)


if __name__ == "__main__":
    unittest.main()
