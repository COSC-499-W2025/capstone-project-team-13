import unittest
import os
import sys

# Add src/portfolio to path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "portfolio"))
)
from showcaseSelect import process_showcase 

class TestShowcaseSelection(unittest.TestCase):
    def setUp(self):
        self.projects = [
            {
                "id": 1,
                "name": "AI Chatbot",
                "year": 2022,
                "impact": 90,
                "complexity": 7,
                "skills": ["Python", "NLP", "API"]
            },
            {
                "id": 2,
                "name": "Portfolio Website",
                "year": 2021,
                "impact": 70,
                "complexity": 4,
                "skills": ["HTML", "CSS", "JavaScript"]
            },
            {
                "id": 3,
                "name": "Data Analyzer",
                "year": 2023,
                "impact": 85,
                "complexity": 6,
                "skills": ["Python", "Pandas"]
            }
        ]

    def test_project_selection(self):
        result = process_showcase(
            self.projects,
            selected_ids=[1, 3],
            attribute_map={},
            skill_map={}
        )
        self.assertEqual(len(result), 2)

    def test_attribute_filtering(self):
        result = process_showcase(
            self.projects,
            selected_ids=[1],
            attribute_map={1: ["name", "impact"]},
            skill_map={}
        )
        self.assertEqual(result[0], {
            "name": "AI Chatbot",
            "impact": 90
        })

    def test_skill_highlighting(self):
        result = process_showcase(
            self.projects,
            selected_ids=[3],
            attribute_map={3: ["name", "skills"]},
            skill_map={3: ["Python"]}
        )
        self.assertEqual(result[0]["highlighted_skills"], ["Python"])

    def test_reranking(self):
        result = process_showcase(
            self.projects,
            selected_ids=[1, 2, 3],
            attribute_map={
                1: ["name", "impact"],
                2: ["name", "impact"],
                3: ["name", "impact"]
            },
            skill_map={},
            rank_attr="impact"
        )

        impacts = [p["impact"] for p in result]
        self.assertEqual(impacts, sorted(impacts, reverse=True))

if __name__ == "__main__":
    unittest.main()
