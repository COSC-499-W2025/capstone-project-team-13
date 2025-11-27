"""
Test Suite: AI-Enhanced Visual Media Project Analyzer
====================================================

Tests for:
- AIVideoMediaAnalyzer functionality
- Caching behavior
- Batch processing
- Database integration
- Prompt templates
"""

import shutil
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)


class TestAIVideoMediaAnalyzer(unittest.TestCase):
    """Test the AI Visual Media Analyzer"""

    def setUp(self):
        """Set up mock media project without caching"""
        self.mock_media_project = {
            "project_name": "Mental Health Awareness Video",
            "media_summary": "A 3-minute video combining narration, motion graphics, and background music.",
            "duration_seconds": 180,
            "file_type": "mp4"
        }

        # Remove old cache
        shutil.rmtree("data/ai_media_project_cache", ignore_errors=True)

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_skills_extraction(self, mock_ai_service):
        """Test extraction of video/media creation skills"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Editing, Motion graphics, Sound design"
        mock_ai_service.return_value = mock_ai

        analyzer = AIMediaProjectAnalyzer()
        skills = analyzer.extract_skills(self.mock_media_project)

        self.assertEqual(len(skills), 3)
        self.assertIn("Editing", skills)
        mock_ai.generate_text.assert_called_once()

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_description_generation(self, mock_ai_service):
        """Test AI-generated project description"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "A short video blending narration and motion graphics to raise awareness."
        mock_ai_service.return_value = mock_ai

        analyzer = AIMediaProjectAnalyzer()
        desc = analyzer.generate_description(
            self.mock_media_project,
            ["Editing", "Motion graphics", "Sound design"]
        )

        self.assertIsNotNone(desc)
        self.assertIn("video", desc.lower())
        mock_ai.generate_text.assert_called_once()

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_contribution_score(self, mock_ai_service):
        """Test numeric contribution scoring"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Score: 7"
        mock_ai_service.return_value = mock_ai

        analyzer = AIMediaProjectAnalyzer()
        score = analyzer.estimate_contribution(self.mock_media_project, ["Editing"])

        self.assertEqual(score, 7.0)
        mock_ai.generate_text.assert_called_once()

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_complete_analysis(self, mock_ai_service):
        """Test full analyzer pipeline"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.side_effect = [
            "Editing, Animation, Sound design",      # skills
            "A dynamic awareness video combining animation and narration.",  # desc
            "9"  # score
        ]
        mock_ai_service.return_value = mock_ai

        analyzer = AIMediaProjectAnalyzer()
        output = analyzer.analyze_project_complete(self.mock_media_project)

        self.assertIn("extracted_skills", output)
        self.assertIn("ai_description", output)
        self.assertIn("contribution_score", output)

        self.assertEqual(len(output["extracted_skills"]), 3)
        self.assertIn("video", output["ai_description"].lower())
        self.assertEqual(output["contribution_score"], 9.0)

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_cache_usage(self, mock_ai_service):
        """Test caching reduces repeated API calls"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Editing, Animation"
        mock_ai_service.return_value = mock_ai

        analyzer = AIMediaProjectAnalyzer()

        # First call: should hit API
        skills1 = analyzer.extract_skills(self.mock_media_project)
        first_call_count = mock_ai.generate_text.call_count

        # Second call: should come from cache
        skills2 = analyzer.extract_skills(self.mock_media_project)
        second_call_count = mock_ai.generate_text.call_count

        self.assertEqual(skills1, skills2)
        self.assertEqual(first_call_count, second_call_count)
        self.assertGreaterEqual(analyzer.cache_hits, 1)

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_batch_analysis(self, mock_ai_service):
        """Test processing multiple media projects"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Editing, Animation"
        mock_ai_service.return_value = mock_ai

        project_list = [self.mock_media_project, self.mock_media_project]

        analyzer = AIMediaProjectAnalyzer()
        results = analyzer.analyze_batch(project_list)

        self.assertEqual(len(results), 2)
        self.assertIn("extracted_skills", results[0])

    # -------------------------------------------------------------
    @patch("src.Databases.database.db_manager.update_project")
    @patch("src.Databases.database.db_manager.get_all_projects")
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_database_update(self, mock_ai_service, mock_get_all, mock_update):
        """Test that media analysis updates DB entries correctly"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.side_effect = [
            "Editing, Animation",
            "This is a media description",
            "7"
        ]
        mock_ai_service.return_value = mock_ai

        mock_db_project = Mock()
        mock_db_project.name = "Mental Health Awareness Video"
        mock_db_project.id = 1
        mock_get_all.return_value = [mock_db_project]

        analyzer = AIMediaProjectAnalyzer()
        analyzer.analyze_and_update_db(self.mock_media_project)

        mock_update.assert_called_once()
        args, kwargs = mock_update.call_args
        self.assertEqual(args[0], 1)

    # -------------------------------------------------------------
    @patch("src.AI.ai_media_project_analyzer.get_ai_service")
    def test_prompt_templates_exist(self, mock_ai_service):
        """Test prompts exist and contain expected length"""
        from src.AI.ai_media_project_analyzer import AIMediaProjectAnalyzer

        analyzer = AIMediaProjectAnalyzer()

        templates = [
            analyzer.DESCRIPTION_PROMPT,
            analyzer.SKILLS_PROMPT,
            analyzer.CONTRIBUTION_PROMPT
        ]

        for t in templates:
            self.assertIsInstance(t, str)
            self.assertGreater(len(t), 50)
