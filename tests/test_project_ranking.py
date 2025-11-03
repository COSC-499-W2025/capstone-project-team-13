import sys, os
from src.Analysis.rank_projects_by_date import rank_projects_chronologically, format_project_timeline
import unittest
from datetime import datetime

class TestProjectRanking(unittest.TestCase):

    def setUp(self):
        """Prepare mock data for testing."""
        self.mock_projects = [
            {"name": "Project B", "created_at": "2024-05-10", "updated_at": "2024-06-01"},
            {"name": "Project A", "created_at": "2023-12-20", "updated_at": "2024-01-05"},
            {"name": "Project C", "created_at": "2025-01-02", "updated_at": "2025-03-11"},
        ]

    def test_rank_projects_chronologically(self):
        """Should sort projects from oldest to newest by created_at."""
        ranked = rank_projects_chronologically(self.mock_projects)
        self.assertEqual(ranked[0]["name"], "Project A")
        self.assertEqual(ranked[-1]["name"], "Project C")

    def test_format_project_timeline(self):
        """Should format project info into readable text."""
        ranked = rank_projects_chronologically(self.mock_projects)
        timeline = format_project_timeline(ranked)
        self.assertIn("1. Project A", timeline)
        self.assertIn("Created: 2023-12-20", timeline)
        self.assertIn("Last Updated: 2024-01-05", timeline)

    def test_handles_missing_dates(self):
        """Should handle missing or malformed dates gracefully."""
        projects = [{"name": "Untimed Project"}]
        ranked = rank_projects_chronologically(projects)
        self.assertEqual(ranked[0]["name"], "Untimed Project")  # still works
        output = format_project_timeline(ranked)
        self.assertIn("Unknown", output)

if __name__ == "__main__":
    unittest.main()
