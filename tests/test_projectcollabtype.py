import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.Analysis.projectcollabtype import identify_project_type
class TestProjectCollabType(unittest.TestCase):
    def setUp(self):
        # This mimics the real structure from fileParser output
        self.individual_project = {
            "project_name": "Solo App",
            "files": [
                {"owner": "Tolu", "editors": [], "lines": 100},
                {"owner": "Tolu", "editors": [], "lines": 80}
            ]
        }

        self.collab_project = {
            "project_name": "Group Web App",
            "files": [
                {"owner": "Tolu", "editors": ["Maya"], "lines": 120},
                {"owner": "Maya", "editors": ["Jackson"], "lines": 90}
            ]
        }

    def test_individual_project(self):
        result = identify_project_type(self.individual_project)
        self.assertEqual(result, "Individual Project")

    def test_collaborative_project(self):
        result = identify_project_type(self.collab_project)
        self.assertEqual(result, "Collaborative Project")

    def test_no_contributors(self):
        empty_project = {"files": []}
        result = identify_project_type(empty_project)
        self.assertEqual(result, "Unknown (no contributor data found)")

if __name__ == "__main__":
    unittest.main()

#To run the tests, use comand: python -m unittest tests/test_projectcollabtype.py
