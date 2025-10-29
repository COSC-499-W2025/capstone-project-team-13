import unittest
from src.Analysis.summarizeProjects import summarize_projects


class TestSummarizeProjects(unittest.TestCase):
    """Unit tests for summarize_projects function."""

    def test_summarize_projects_basic(self):
        projects = [
            {"project_name": "Proj A", "time_spent": 50, "success_score": 0.8, "contribution_score": 0.9, "skills": ["Python", "Flask"]},
            {"project_name": "Proj B", "time_spent": 20, "success_score": 0.6, "contribution_score": 0.7, "skills": ["HTML", "CSS"]},
            {"project_name": "Proj C", "time_spent": 100, "success_score": 0.9, "contribution_score": 0.95, "skills": ["Python", "Data Analysis"]}
        ]

        result = summarize_projects(projects, top_k=2)

        self.assertIn("selected_projects", result)
        self.assertIn("summary", result)
        self.assertIsInstance(result["selected_projects"], list)
        self.assertLessEqual(len(result["selected_projects"]), 2)

        for proj in result["selected_projects"]:
            self.assertGreaterEqual(proj["overall_score"], 0)
            self.assertLessEqual(proj["overall_score"], 1)

        self.assertIn(str(len(result["selected_projects"])), result["summary"])

    def test_empty_project_list(self):
        result = summarize_projects([])
        self.assertEqual(result["selected_projects"], [])
        self.assertIn("no projects", result["summary"].lower())

    def test_single_project(self):
        single = [
            {"project_name": "SoloProj", "time_spent": 30, "success_score": 0.8, "contribution_score": 0.85, "skills": ["Python"]},
        ]
        result = summarize_projects(single)
        self.assertEqual(len(result["selected_projects"]), 1)
        self.assertEqual(result["selected_projects"][0]["project_name"], "SoloProj")

    def test_identical_scores(self):
        projects = [
            {"project_name": "Proj A", "time_spent": 10, "success_score": 0.8, "contribution_score": 0.8, "skills": ["Python"]},
            {"project_name": "Proj B", "time_spent": 10, "success_score": 0.8, "contribution_score": 0.8, "skills": ["HTML"]},
        ]
        result = summarize_projects(projects, top_k=2)
        self.assertEqual(len(result["selected_projects"]), 2)
        for p in result["selected_projects"]:
            self.assertGreaterEqual(p["overall_score"], 0)
            self.assertLessEqual(p["overall_score"], 1)

    def test_diversity_selection_prefers_unique_skills(self):
        projects = [
            {"project_name": "Proj A", "time_spent": 40, "success_score": 0.9, "contribution_score": 0.9, "skills": ["Python", "ML"]},
            {"project_name": "Proj B", "time_spent": 50, "success_score": 0.88, "contribution_score": 0.85, "skills": ["Python", "Flask"]},
            {"project_name": "Proj C", "time_spent": 60, "success_score": 0.92, "contribution_score": 0.9, "skills": ["React", "UI"]},
        ]

        result = summarize_projects(projects, top_k=2)
        selected = result["selected_projects"]
        all_skills = set(skill for p in selected for skill in p["skills"])

        self.assertLessEqual(len(selected), 2)
        self.assertGreater(len(all_skills), 2, "Expected diverse skill sets in selected projects")


if __name__ == "__main__":
    unittest.main()
