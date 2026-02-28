"""
Unit tests for the updated ai_enhanced_summarizer module.

Covers:
  - _parse_bullets_from_text          (pure function, no mocks needed)
  - _ai_rewrite_bullets               (mocked AI service)
  - generate_bullets_for_project      (mocked generators + AI + db)
  - generate_resume_bullets           (legacy dict path, mocked AI)
  - ai_enhance_project_summary        (mocked AI)
  - summarize_projects_with_ai        (mocked AI + scorer)

All external I/O (AIService, db_manager, generators, scorer) is mocked so
the tests run offline without a real API key or database.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(
    project_id: int = 1,
    name: str = "Test Project",
    project_type: str = "code",
    skills: list = None,
):
    """Return a lightweight mock that looks like a Project ORM object."""
    p = MagicMock()
    p.id = project_id
    p.name = name
    p.project_type = project_type
    p.skills = skills or ["Python", "FastAPI", "SQLite"]
    p.languages = ["Python"]
    p.frameworks = ["FastAPI"]
    p.lines_of_code = 1200
    p.file_count = 15
    p.collaboration_type = "individual"
    return p


# ---------------------------------------------------------------------------
# Tests: _parse_bullets_from_text
# ---------------------------------------------------------------------------

class TestParseBulletsFromText(unittest.TestCase):

    def _parse(self, text, expected):
        from src.AI.ai_enhanced_summarizer import _parse_bullets_from_text
        return _parse_bullets_from_text(text, expected)

    def test_numbered_list(self):
        text = (
            "1. Built a REST API with FastAPI and SQLite\n"
            "2. Wrote unit tests achieving 90% coverage\n"
            "3. Deployed containerised app using Docker\n"
        )
        result = self._parse(text, 3)
        self.assertEqual(len(result), 3)
        self.assertTrue(result[0].startswith("Built"))
        self.assertTrue(result[1].startswith("Wrote"))

    def test_dash_list(self):
        text = (
            "- Designed scalable database schema\n"
            "- Implemented authentication middleware\n"
        )
        result = self._parse(text, 2)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0].startswith("Designed"))

    def test_skips_short_lines(self):
        text = "1. Hi\n2. Developed a full-stack application with React and Django\n"
        result = self._parse(text, 2)
        self.assertEqual(len(result), 1)
        self.assertIn("Developed", result[0])

    def test_skips_code_fences(self):
        text = "```\nsome code\n```\n1. Engineered a data pipeline processing 1M rows daily\n"
        result = self._parse(text, 1)
        self.assertEqual(len(result), 1)
        self.assertIn("Engineered", result[0])

    def test_stops_at_expected_count_and_empty_input(self):
        text = "\n".join(f"{i+1}. Built feature number {i+1} for the platform" for i in range(10))
        self.assertEqual(len(self._parse(text, 3)), 3)
        self.assertEqual(self._parse("", 3), [])


# ---------------------------------------------------------------------------
# Tests: _ai_rewrite_bullets
# ---------------------------------------------------------------------------

class TestAiRewriteBullets(unittest.TestCase):

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    def test_returns_rewritten_when_count_matches(self, mock_get_ai):
        ai = MagicMock()
        ai.generate_text.return_value = (
            "1. Architected REST API serving 10k requests/day\n"
            "2. Boosted test coverage from 60% to 95% via pytest\n"
            "3. Reduced query latency by 40% through index optimisation\n"
        )
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import _ai_rewrite_bullets
        original = [
            "Built REST API",
            "Wrote tests",
            "Improved queries",
        ]
        result = _ai_rewrite_bullets(original, "My Project", ["Python", "FastAPI"])
        self.assertEqual(len(result), 3)
        self.assertNotEqual(result, original)

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    def test_falls_back_when_count_mismatch(self, mock_get_ai):
        ai = MagicMock()
        # AI returns only one usable bullet
        ai.generate_text.return_value = "1. Single bullet only here in the response"
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import _ai_rewrite_bullets
        original = ["Bullet one for testing", "Bullet two for testing", "Bullet three"]
        result = _ai_rewrite_bullets(original, "Project", [])
        self.assertEqual(result, original)  # fallback

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    def test_falls_back_on_exception(self, mock_get_ai):
        ai = MagicMock()
        ai.generate_text.side_effect = RuntimeError("API down")
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import _ai_rewrite_bullets
        original = ["Original bullet one here", "Original bullet two here"]
        result = _ai_rewrite_bullets(original, "P", [])
        self.assertEqual(result, original)


# ---------------------------------------------------------------------------
# Tests: generate_bullets_for_project  (primary ORM path)
# ---------------------------------------------------------------------------

class TestGenerateBulletsForProject(unittest.TestCase):

    def _patch_all(self):
        """Return a dict of patchers that cover every external dependency."""
        patches = {
            "code_gen": patch(
                "src.AI.ai_enhanced_summarizer.CodeBulletGenerator"
            ),
            "media_gen": patch(
                "src.AI.ai_enhanced_summarizer.MediaBulletGenerator"
            ),
            "text_gen": patch(
                "src.AI.ai_enhanced_summarizer.TextBulletGenerator"
            ),
            "score": patch(
                "src.AI.ai_enhanced_summarizer.score_all_bullets",
                return_value={"overall_score": 78.5},
            ),
            "db": patch(
                "src.AI.ai_enhanced_summarizer.db_manager"
            ),
            "ai_rewrite": patch(
                "src.AI.ai_enhanced_summarizer._ai_rewrite_bullets",
                side_effect=lambda bullets, *a, **kw: bullets,  # no-op
            ),
        }
        return patches

    def _start(self, patches):
        return {k: p.start() for k, p in patches.items()}

    def _stop(self, patches):
        for p in patches.values():
            p.stop()

    def test_success_code_project(self):
        patchers = self._patch_all()
        mocks = self._start(patchers)
        try:
            gen_instance = MagicMock()
            gen_instance.generate_resume_bullets.return_value = [
                "Engineered a REST API with FastAPI",
                "Implemented SHA-256 duplicate detection",
                "Achieved 95% test coverage with pytest",
            ]
            gen_instance.generate_project_header.return_value = "Test Project | Python, FastAPI"
            mocks["code_gen"].return_value = gen_instance

            from src.AI.ai_enhanced_summarizer import generate_bullets_for_project
            project = _make_project(project_type="code")
            result = generate_bullets_for_project(project, num_bullets=3, use_ai=False)

            self.assertTrue(result["success"])
            self.assertEqual(result["project_id"], 1)
            self.assertEqual(len(result["bullets"]), 3)
            self.assertEqual(result["ats_score"], 78.5)
            self.assertFalse(result["ai_enhanced"])
        finally:
            self._stop(patchers)

    def test_success_media_project(self):
        patchers = self._patch_all()
        mocks = self._start(patchers)
        try:
            gen_instance = MagicMock()
            gen_instance.generate_resume_bullets.return_value = [
                "Produced 20+ promotional videos for brand campaigns",
                "Edited multi-track audio achieving broadcast quality",
            ]
            gen_instance.generate_project_header.return_value = "Media Project | Premiere Pro"
            mocks["media_gen"].return_value = gen_instance

            from src.AI.ai_enhanced_summarizer import generate_bullets_for_project
            project = _make_project(project_type="visual_media")
            result = generate_bullets_for_project(project, num_bullets=2, use_ai=False)

            self.assertTrue(result["success"])
            self.assertEqual(len(result["bullets"]), 2)
        finally:
            self._stop(patchers)

    def test_ai_enhancement_called_when_use_ai_true(self):
        patchers = self._patch_all()
        mocks = self._start(patchers)
        try:
            base_bullets = [
                "Built feature A",
                "Built feature B",
                "Built feature C",
            ]
            rewritten_bullets = [
                "Architected feature A increasing throughput by 30%",
                "Delivered feature B reducing error rate to < 1%",
                "Shipped feature C ahead of schedule",
            ]
            gen_instance = MagicMock()
            gen_instance.generate_resume_bullets.return_value = base_bullets
            gen_instance.generate_project_header.return_value = "Header"
            mocks["code_gen"].return_value = gen_instance
            # Override the no-op rewrite with an actual rewrite
            patchers["ai_rewrite"].stop()
            rewrite_patcher = patch(
                "src.AI.ai_enhanced_summarizer._ai_rewrite_bullets",
                return_value=rewritten_bullets,
            )
            mock_rewrite = rewrite_patcher.start()

            from src.AI.ai_enhanced_summarizer import generate_bullets_for_project
            project = _make_project(project_type="code")
            result = generate_bullets_for_project(project, num_bullets=3, use_ai=True)

            self.assertTrue(result["ai_enhanced"])
            self.assertEqual(result["bullets"], rewritten_bullets)
            mock_rewrite.assert_called_once()
            rewrite_patcher.stop()
        finally:
            # Avoid double-stop on ai_rewrite
            for k, p in patchers.items():
                if k != "ai_rewrite":
                    try:
                        p.stop()
                    except RuntimeError:
                        pass

    def test_invalid_num_bullets_returns_error(self):
        from src.AI.ai_enhanced_summarizer import generate_bullets_for_project
        project = _make_project()
        result = generate_bullets_for_project(project, num_bullets=1)
        self.assertFalse(result["success"])
        self.assertIn("num_bullets", result["error"])

    def test_unsupported_project_type_returns_error(self):
        from src.AI.ai_enhanced_summarizer import generate_bullets_for_project
        project = _make_project(project_type="unknown_type")
        result = generate_bullets_for_project(project, num_bullets=3)
        self.assertFalse(result["success"])
        self.assertIn("unknown_type", result["error"])

    def test_persist_false_skips_db(self):
        patchers = self._patch_all()
        mocks = self._start(patchers)
        try:
            gen_instance = MagicMock()
            gen_instance.generate_resume_bullets.return_value = ["Bullet A test here", "Bullet B test here"]
            gen_instance.generate_project_header.return_value = "Header"
            mocks["code_gen"].return_value = gen_instance

            from src.AI.ai_enhanced_summarizer import generate_bullets_for_project
            project = _make_project()
            generate_bullets_for_project(project, num_bullets=2, use_ai=False, persist=False)

            mocks["db"].save_resume_bullets.assert_not_called()
        finally:
            self._stop(patchers)


# ---------------------------------------------------------------------------
# Tests: generate_resume_bullets  (legacy dict path)
# ---------------------------------------------------------------------------

class TestGenerateResumeBulletsLegacy(unittest.TestCase):

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    def test_returns_parsed_bullets(self, mock_get_ai):
        ai = MagicMock()
        ai.generate_text.return_value = (
            "1. Designed full-stack web application with Django\n"
            "2. Integrated PostgreSQL reducing query time by 50%\n"
            "3. Deployed on AWS achieving 99.9% uptime\n"
        )
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import generate_resume_bullets
        project = {
            "project_name": "Web App",
            "skills": ["Django", "PostgreSQL", "AWS"],
        }
        result = generate_resume_bullets(project, num_bullets=3)
        self.assertEqual(len(result), 3)
        self.assertTrue(result[0].startswith("Designed"))

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    def test_fallback_on_empty_response(self, mock_get_ai):
        ai = MagicMock()
        ai.generate_text.return_value = None
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import generate_resume_bullets
        project = {"project_name": "My Project", "skills": ["Python"]}
        result = generate_resume_bullets(project, num_bullets=2)
        self.assertEqual(len(result), 2)
        self.assertIn("My Project", result[0])


# ---------------------------------------------------------------------------
# Tests: ai_enhance_project_summary
# ---------------------------------------------------------------------------

class TestAiEnhanceProjectSummary(unittest.TestCase):

    def test_adds_ai_description(self):
        ai = MagicMock()
        ai.generate_text.return_value = "A robust data pipeline built with Apache Spark."

        from src.AI.ai_enhanced_summarizer import ai_enhance_project_summary
        project = {"project_name": "Pipeline", "skills": ["Spark", "Python"]}
        result = ai_enhance_project_summary(project, ai_service=ai)

        self.assertIn("ai_description", result)
        self.assertEqual(result["ai_description"], "A robust data pipeline built with Apache Spark.")

    def test_adds_technical_insights_when_requested(self):
        ai = MagicMock()
        ai.generate_text.side_effect = [
            "Description text here.",    # description call
            "Uses producer-consumer pattern.",  # technical_insights call
        ]

        from src.AI.ai_enhanced_summarizer import ai_enhance_project_summary
        project = {"project_name": "Queue Service", "skills": ["RabbitMQ"]}
        result = ai_enhance_project_summary(project, ai_service=ai, include_technical_depth=True)

        self.assertIn("ai_description", result)
        self.assertIn("technical_insights", result)

    def test_fallback_description_on_exception(self):
        ai = MagicMock()
        ai.generate_text.side_effect = Exception("API error")

        from src.AI.ai_enhanced_summarizer import ai_enhance_project_summary
        project = {"project_name": "Broken", "skills": ["Go"]}
        result = ai_enhance_project_summary(project, ai_service=ai)

        self.assertIn("ai_description", result)
        # Fallback should mention skill
        self.assertIn("Go", result["ai_description"])


# ---------------------------------------------------------------------------
# Tests: summarize_projects_with_ai
# ---------------------------------------------------------------------------

class TestSummarizeProjectsWithAi(unittest.TestCase):

    def _sample_projects(self):
        return [
            {
                "project_name": "Alpha",
                "time_spent": 100,
                "success_score": 0.9,
                "contribution_score": 0.8,
                "skills": ["Python", "Django"],
                "file_count": 40,
                "lines_of_code": 5000,
            },
            {
                "project_name": "Beta",
                "time_spent": 60,
                "success_score": 0.7,
                "contribution_score": 0.6,
                "skills": ["React", "TypeScript"],
                "file_count": 25,
                "lines_of_code": 3000,
            },
            {
                "project_name": "Gamma",
                "time_spent": 30,
                "success_score": 0.5,
                "contribution_score": 0.9,
                "skills": ["Go", "gRPC"],
                "file_count": 10,
                "lines_of_code": 1500,
            },
        ]

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    @patch("src.AI.ai_enhanced_summarizer._original_summarize")
    def test_non_ai_mode_no_ai_calls(self, mock_summarize, mock_get_ai):
        mock_summarize.return_value = {
            "selected_projects": self._sample_projects()[:2],
            "all_projects_scored": self._sample_projects(),
            "summary": "Summary text",
            "unique_skills": ["Python", "React"],
            "average_score": 0.7,
        }

        from src.AI.ai_enhanced_summarizer import summarize_projects_with_ai
        result = summarize_projects_with_ai(self._sample_projects(), top_k=2, use_ai=False)

        self.assertIn("selected_projects", result)
        self.assertNotIn("ai_summary", result)
        mock_get_ai.assert_not_called()

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    @patch("src.AI.ai_enhanced_summarizer._get_cached_ai_description", return_value=None)
    @patch("src.AI.ai_enhanced_summarizer._cache_ai_description")
    @patch("src.AI.ai_enhanced_summarizer._original_summarize")
    def test_ai_mode_adds_descriptions_and_summary(
        self, mock_summarize, mock_cache_write, mock_cache_read, mock_get_ai
    ):
        projects = self._sample_projects()
        mock_summarize.return_value = {
            "selected_projects": projects[:2],
            "all_projects_scored": projects,
            "summary": "Base summary",
            "unique_skills": ["Python", "React", "Go"],
            "average_score": 0.7,
        }
        ai = MagicMock()
        ai.generate_text.return_value = "AI-generated text for the project."
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import summarize_projects_with_ai
        result = summarize_projects_with_ai(projects, top_k=2, use_ai=True)

        self.assertIn("ai_summary", result)
        for proj in result["selected_projects"]:
            self.assertIn("ai_description", proj)

    @patch("src.AI.ai_enhanced_summarizer.get_ai_service")
    @patch("src.AI.ai_enhanced_summarizer._get_cached_ai_description")
    @patch("src.AI.ai_enhanced_summarizer._original_summarize")
    def test_cache_hit_skips_ai_call(self, mock_summarize, mock_cache_read, mock_get_ai):
        projects = self._sample_projects()[:1]
        mock_summarize.return_value = {
            "selected_projects": projects,
            "all_projects_scored": projects,
            "summary": "Base",
            "unique_skills": [],
            "average_score": 0.8,
        }
        mock_cache_read.return_value = "Cached description text here."
        ai = MagicMock()
        # generate_text still called for portfolio summary
        ai.generate_text.return_value = "Portfolio narrative."
        mock_get_ai.return_value = ai

        from src.AI.ai_enhanced_summarizer import summarize_projects_with_ai
        result = summarize_projects_with_ai(projects, top_k=1, use_ai=True)

        # Description came from cache
        self.assertEqual(result["selected_projects"][0]["ai_description"], "Cached description text here.")
        # generate_text only called once (for portfolio narrative, not per-project description)
        self.assertEqual(ai.generate_text.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)