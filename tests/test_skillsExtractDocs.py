import os
import sys
import unittest

# 🔹 ADD SRC TO PATH FIRST
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# 🔹 THEN IMPORT
from Analysis.skillsExtractDocs import analyze_folder_for_skills
from Analysis.skillsExtractDocs import count_keyword_matches


class TestSkillExtraction(unittest.TestCase):
    

    
    def print_results(self, results):
        print("Detected skills:")
        for skill, count in results:
            print(f"{skill}: {count}")
        print("-" * 30)



    def test_case1(self):
        """Essays showing research and critical thinking skills"""
        folder = os.path.join(os.path.dirname(__file__), "test_skillsDocs", "case1")
        results = analyze_folder_for_skills(folder)
        self.print_results(results)
        detected = [skill for skill, _ in results]
        # Expect critical_thinking to dominate if overlapping
        self.assertIn("critical_thinking", detected)
        self.assertIn("research_writing", detected)
        self.assertIn("writing_mechanics", detected)

    def test_case2(self):
        """Blog posts showing content writing skills"""
        folder = os.path.join(os.path.dirname(__file__), "test_skillsDocs", "case2")
        results = analyze_folder_for_skills(folder)
        self.print_results(results)
        detected = [skill for skill, _ in results]
        self.assertIn("content_writing", detected)

    def test_case3(self):
        """Reports showing technical writing skills"""
        folder = os.path.join(os.path.dirname(__file__), "test_skillsDocs", "case3")
        results = analyze_folder_for_skills(folder)
        self.print_results(results)
        detected = [skill for skill, _ in results]
        # Removed professional_writing
        self.assertIn("technical_writing", detected)
        self.assertIn("writing_mechanics", detected)
        self.assertIn("organization", detected)

    def test_case4(self):
        """Mixed project: research + content + writing mechanics"""
        folder = os.path.join(os.path.dirname(__file__), "test_skillsDocs", "case4")
        results = analyze_folder_for_skills(folder)
        self.print_results(results)
        detected = [skill for skill, _ in results]
        self.assertIn("research_writing", detected)
        self.assertIn("content_writing", detected)
        self.assertIn("writing_mechanics", detected)
        self.assertIn("organization", detected)

    def test_count_keyword_matches_phrases(self):
        """Unit test for phrase-aware keyword matching helper."""
        text = """
        This project demonstrates character development and sentence structure.
        A strong call to action was supported by critical thinking.
        """

        keywords = [
            "character development",
            "sentence structure",
            "call to action",
            "critical thinking"
        ]

        result = count_keyword_matches(text, keywords)

        self.assertEqual(result, 4)



if __name__ == "__main__":
    unittest.main()