"""
Test Suite: AI-Enhanced Text Project Analyzer
====================================================

Tests for:
- AITextProjectAnalyzer functionality
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


class TestAITextProjectAnalyzer(unittest.TestCase):
    """Test the AI Text Project Analyzer"""

        
    def setUp(self):
        """Set up mock text project without caching"""
        self.mock_project = {
            "project_name": "Mental Health Essay",
            "content": "This essay explores emotional resilience and psychology...",
            "word_count": 1200,
            "file_type": "pdf"
        }
        shutil.rmtree("data/ai_text_project_cache", ignore_errors=True)
        
    @patch("src.AI.ai_text_project_analyzer.get_ai_service")
    def test_skills_extraction(self, mock_ai_service):
        """Test extraction of writing skills"""
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Critical thinking, Emotional analysis, Research"
        mock_ai_service.return_value = mock_ai
        analyzer = AITextProjectAnalyzer()
        skills = analyzer.extract_skills(self.mock_project)

        self.assertEqual(len(skills), 3)
        self.assertIn("Critical thinking", skills)
        mock_ai.generate_text.assert_called_once()

    @patch("src.AI.ai_text_project_analyzer.get_ai_service")
    def test_description_generation(self, mock_ai_service):
        """Test AI-generated project description"""
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "A thoughtful essay exploring mental health topics."
        mock_ai_service.return_value = mock_ai

        analyzer = AITextProjectAnalyzer()
        desc = analyzer.generate_description(self.mock_project, ["Critical thinking", "Emotional analysis", "Research" ])

        self.assertIsNotNone(desc)
        self.assertIn("essay", desc.lower())
        mock_ai.generate_text.assert_called_once()

    @patch("src.AI.ai_text_project_analyzer.get_ai_service")
    def test_contribution_score(self, mock_ai_service):
        """Test numeric contribution scoring"""
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Score: 8"
        mock_ai_service.return_value = mock_ai

        analyzer = AITextProjectAnalyzer()
        score = analyzer.estimate_contribution(self.mock_project, ["analysis"])

        self.assertEqual(score, 8.0)
        mock_ai.generate_text.assert_called_once()

    @patch("src.AI.ai_text_project_analyzer.get_ai_service")
    def test_complete_analysis(self, mock_ai_service):
        """Test full analyzer pipeline"""
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer

        mock_ai = Mock()
        # Use side_effect so each call returns the right string
        mock_ai.generate_text.side_effect = [
            "Critical thinking, Emotional analysis, Research",   # skills
            "A thoughtful essay exploring mental health topics.",  # description
            "8"  # score
        ]
        mock_ai_service.return_value = mock_ai
        analyzer = AITextProjectAnalyzer()
        output = analyzer.analyze_project_complete(self.mock_project)

        self.assertIn("extracted_skills", output)
        self.assertIn("ai_description", output)
        self.assertIn("contribution_score", output)

        self.assertEqual(len(output["extracted_skills"]), 3)
        self.assertIn("essay", output["ai_description"].lower())
        self.assertEqual(output["contribution_score"], 8.0)

    @patch("src.AI.ai_text_project_analyzer.get_ai_service") 
    def test_cache_usage(self, mock_ai_service): 
        """Test caching reduces repeated API calls""" 
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer
        mock_ai = Mock() 
        mock_ai.generate_text.return_value = "Skill A, Skill B" 
        mock_ai_service.return_value = mock_ai
        analyzer = AITextProjectAnalyzer() # First call → hits API 
        skills1 = analyzer.extract_skills(self.mock_project) 
        call_count_1 = mock_ai.generate_text.call_count
        # Second call → should load from cache 
        skills2 = analyzer.extract_skills(self.mock_project) 
        call_count_2 = mock_ai.generate_text.call_count
        self.assertEqual(skills1, skills2) 
        self.assertEqual(call_count_1, call_count_2) # no extra calls 
        self.assertGreaterEqual(analyzer.cache_hits, 1)
    
    @patch("src.AI.ai_service.get_ai_service") 
    def test_batch_analysis(self, mock_ai_service): 
        """Test processing multiple text projects""" 
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer
        mock_ai = Mock() 
        mock_ai.generate_text.return_value = "Skill A, Skill B" 
        mock_ai_service.return_value = mock_ai
        project_list = [self.mock_project, self.mock_project] 
        analyzer = AITextProjectAnalyzer() 
        results = analyzer.analyze_batch(project_list)
        self.assertEqual(len(results), 2) 
        self.assertIn("extracted_skills", results[0])

    @patch("src.Databases.database.db_manager.update_project")
    @patch("src.Databases.database.db_manager.get_all_projects")
    @patch("src.AI.ai_text_project_analyzer.get_ai_service")
    def test_database_update(self, mock_ai_service, mock_get_all, mock_update):
        """Test that analysis results update DB correctly"""
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer

        mock_ai = Mock()
        mock_ai.generate_text.side_effect = [
            "Writing, Analysis",
            "This is a description",
            "8"
        ]
        mock_ai_service.return_value = mock_ai

        mock_db_project = Mock()
        mock_db_project.name = "Mental Health Essay"
        mock_db_project.id = 1

        mock_get_all.return_value = [mock_db_project]

        analyzer = AITextProjectAnalyzer()
        analyzer.analyze_and_update_db(self.mock_project)

        mock_update.assert_called_once()
        args, kwargs = mock_update.call_args
        self.assertEqual(args[0], 1)  # correct project id

    @patch("src.AI.ai_text_project_analyzer.get_ai_service")
    def test_prompt_templates_exist(self, mock_ai_service):
        """Test prompts exist and contain expected length"""
        from src.AI.ai_text_project_analyzer import AITextProjectAnalyzer

        analyzer = AITextProjectAnalyzer()

        templates = [
            analyzer.DESCRIPTION_PROMPT,
            analyzer.SKILLS_PROMPT,
            analyzer.CONTRIBUTION_PROMPT
        ]

        for t in templates:
            self.assertIsInstance(t, str)
            self.assertGreater(len(t), 50)

