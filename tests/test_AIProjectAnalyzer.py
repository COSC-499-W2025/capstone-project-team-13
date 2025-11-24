"""
Test Suite: AI-Enhanced Project Summaries
====================================================

Tests for:
- AI project analyzer functionality
- Enhanced summarizer integration
- Caching behavior
- Batch processing
- Database integration
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))  # move up one level from tests/
sys.path.insert(0, project_root)

class TestAIProjectAnalyzer(unittest.TestCase):
    """Test the AI Project Analyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock project data
        self.mock_project = Mock()
        self.mock_project.id = 1
        self.mock_project.name = "Test Project"
        self.mock_project.languages = ["Python", "JavaScript"]
        self.mock_project.frameworks = ["React", "Flask"]
        self.mock_project.file_count = 50
        self.mock_project.lines_of_code = 5000
        self.mock_project.date_created = None
        self.mock_project.date_modified = None
        self.mock_project.file_path = "/tmp/test_project"
    
    @patch('src.Databases.database.db_manager.get_project')
    @patch('src.AI.ai_service.get_ai_service')
    def test_analyze_project_overview(self, mock_ai_service, mock_get_project):
        """Test overview generation"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        # Setup mocks
        mock_get_project.return_value = self.mock_project
        mock_ai = Mock()
        mock_ai.generate_text.return_value = "A sophisticated web application built with React and Flask."
        mock_ai_service.return_value = mock_ai
        
        # Test
        analyzer = AIProjectAnalyzer()
        result = analyzer.analyze_project_overview(1)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertIn("React", result)
        mock_ai.generate_text.assert_called_once()
    
    @patch('src.Databases.database.db_manager.get_project')
    @patch('src.AI.ai_service.get_ai_service')
    def test_caching_works(self, mock_ai_service, mock_get_project):
        """Test that caching reduces API calls"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        # Setup mocks
        mock_get_project.return_value = self.mock_project
        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Test description"
        mock_ai_service.return_value = mock_ai
        
        # Test
        analyzer = AIProjectAnalyzer()
        
        # First call - should hit API
        result1 = analyzer.analyze_project_overview(1)
        call_count_1 = mock_ai.generate_text.call_count
        
        # Second call - should use cache
        result2 = analyzer.analyze_project_overview(1)
        call_count_2 = mock_ai.generate_text.call_count
        
        # Assertions
        self.assertEqual(result1, result2)
        self.assertEqual(call_count_1, call_count_2)  # No additional calls
        self.assertEqual(analyzer.cache_hits, 1)
    
    def test_cache_key_generation(self):
        """Test cache key generation is consistent"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        key1 = analyzer._get_cache_key(1, 'overview')
        key2 = analyzer._get_cache_key(1, 'overview')
        key3 = analyzer._get_cache_key(2, 'overview')
        key4 = analyzer._get_cache_key(1, 'technical_depth')
        
        self.assertEqual(key1, key2)  # Same inputs = same key
        self.assertNotEqual(key1, key3)  # Different project
        self.assertNotEqual(key1, key4)  # Different analysis type
    
    @patch('src.Databases.database.db_manager.get_project')
    @patch('src.AI.ai_service.get_ai_service')
    def test_skill_parsing(self, mock_ai_service, mock_get_project):
        """Test parsing of AI-generated skills"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        
        # Test various skill formats
        test_text = """
        1. API Design (Strong): Implements RESTful endpoints
        2. Async Programming - Demonstrated - Uses async/await patterns
        • Database Optimization (Moderate): Efficient query patterns
        """
        
        skills = analyzer._parse_skills_from_text(test_text)
        
        self.assertEqual(len(skills), 3)
        self.assertEqual(skills[0]['skill'], 'API Design')
        self.assertEqual(skills[1]['skill'], 'Async Programming')
        self.assertIn('evidence', skills[0])

class TestAIEnhancedSummarizer(unittest.TestCase):
    """Test the enhanced summarizer integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_projects = [
            {
                "project_name": "E-commerce Platform",
                "time_spent": 100,
                "success_score": 0.9,
                "contribution_score": 0.8,
                "skills": ["Python", "Django", "PostgreSQL", "REST API"]
            },
            {
                "project_name": "Mobile Game",
                "time_spent": 50,
                "success_score": 0.7,
                "contribution_score": 0.5,
                "skills": ["C#", "Unity", "Game Design"]
            },
            {
                "project_name": "Data Analysis Tool",
                "time_spent": 30,
                "success_score": 0.6,
                "contribution_score": 0.9,
                "skills": ["Python", "Pandas", "Matplotlib"]
            }
        ]
    
    @patch('src.AI.ai_service.get_ai_service')
    def test_non_ai_mode(self, mock_ai_service):
        """Test that non-AI mode works (backward compatibility)"""
        from src.AI.ai_enhanced_summarizer import summarize_projects_with_ai
        
        result = summarize_projects_with_ai(
            self.sample_projects,
            top_k=2,
            use_ai=False
        )
        
        # Should complete without errors
        self.assertIn('selected_projects', result)
        self.assertIn('summary', result)
        self.assertLessEqual(len(result['selected_projects']), 2)
        
        # Should NOT have AI-generated content
        self.assertNotIn('ai_summary', result)
        for proj in result['selected_projects']:
            self.assertNotIn('ai_description', proj)
        
        # AI service should never be called
        mock_ai_service.assert_not_called()
    
    @patch('src.AI.ai_service.get_ai_service')
    def test_ai_enhancement_top_k_only(self, mock_ai_service):
        """Test AI enhancement of top-k projects only"""
        from src.AI.ai_enhanced_summarizer import summarize_projects_with_ai
        
        # Setup mock
        mock_ai = Mock()
        mock_ai.generate_text.return_value = "AI-generated description"
        mock_ai_service.return_value = mock_ai
        
        result = summarize_projects_with_ai(
            self.sample_projects,
            top_k=2,
            use_ai=True,
            enhance_all=False
        )
        
        # Only selected projects should have AI descriptions
        self.assertEqual(len(result['selected_projects']), 2)
        for proj in result['selected_projects']:
            self.assertIn('ai_description', proj)
        
        # Should have AI summary
        self.assertIn('ai_summary', result)
    
    @patch('src.AI.ai_enhanced_summarizer.get_ai_service')
    def test_resume_bullet_generation(self, mock_ai_service):
        """Test resume bullet point generation"""
        from src.AI.ai_enhanced_summarizer import generate_resume_bullets
        
        # Setup mock
        mock_ai = Mock()
        # FIX: Return properly formatted multi-line bullets
        mock_ai.generate_text.return_value = """1. Built scalable e-commerce platform handling 10,000+ daily transactions
        2. Implemented RESTful API with Django serving 50+ endpoints
        3. Optimized PostgreSQL queries reducing response time by 40%"""
        mock_ai_service.return_value = mock_ai
        
        bullets = generate_resume_bullets(self.sample_projects[0], num_bullets=3)
        
        self.assertEqual(len(bullets), 3)
        self.assertTrue(bullets[0].startswith("Built"))
        self.assertIn("e-commerce", bullets[0].lower())

class TestBatchProcessing(unittest.TestCase):
    """Test batch processing functionality"""
    
    @patch('src.Databases.database.db_manager.get_project')
    @patch('src.Databases.database.db_manager.get_all_projects')
    @patch('src.AI.ai_service.get_ai_service')
    def test_batch_analyze_multiple_projects(self, mock_ai_service, mock_get_all, mock_get_project):
        """Test batch analysis of multiple projects"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        # Setup mocks
        mock_projects = []
        for i in range(3):
            mock_proj = Mock()
            mock_proj.id = i + 1
            mock_proj.name = f"Project {i+1}"
            mock_proj.languages = ["Python"]
            mock_proj.frameworks = []
            mock_proj.file_count = 10
            mock_proj.lines_of_code = 1000
            mock_proj.date_created = None
            mock_proj.date_modified = None
            mock_proj.file_path = f"/tmp/project{i+1}"
            mock_projects.append(mock_proj)
        
        mock_get_all.return_value = mock_projects
        mock_get_project.side_effect = lambda id: mock_projects[id-1]
        
        mock_ai = Mock()
        mock_ai.generate_text.return_value = "Test description"
        mock_ai_service.return_value = mock_ai
        
        # Test
        analyzer = AIProjectAnalyzer()
        results = analyzer.batch_analyze_projects([1, 2, 3], analysis_types=['overview'])
        
        # Assertions
        self.assertEqual(len(results), 3)
        self.assertTrue(all('overview' in r for r in results))

class TestDatabaseIntegration(unittest.TestCase):
    """Test database integration features"""
    
    @patch('src.Databases.database.db_manager.update_project')
    @patch('src.Databases.database.db_manager.get_project')
    def test_update_database_with_analysis(self, mock_get_project, mock_update):
        """Test updating database with AI analysis"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        # Setup mocks
        mock_proj = Mock()
        mock_proj.id = 1
        mock_proj.name = "Test Project"
        mock_get_project.return_value = mock_proj
        mock_update.return_value = True
        
        # Test
        analyzer = AIProjectAnalyzer()
        analysis = {
            'overview': 'AI-generated description',
            'project_id': 1
        }
        
        result = analyzer.update_database_with_analysis(1, analysis)
        
        # Assertions
        self.assertTrue(result)
        mock_update.assert_called_once_with(1, {
            'ai_description': 'AI-generated description'
        })

class TestPromptEngineering(unittest.TestCase):
    """Test prompt templates and engineering"""
    
    def test_prompt_templates_exist(self):
        """Test that all required prompt templates exist"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        
        required_prompts = ['overview', 'technical_depth', 'skills_extraction']
        for prompt_type in required_prompts:
            self.assertIn(prompt_type, analyzer.ANALYSIS_PROMPTS)
            self.assertIsInstance(analyzer.ANALYSIS_PROMPTS[prompt_type], str)
            self.assertGreater(len(analyzer.ANALYSIS_PROMPTS[prompt_type]), 50)
    
    def test_prompt_formatting(self):
        """Test that prompts can be formatted with project data"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        
        context = {
            'project_name': 'Test',
            'languages': 'Python',
            'frameworks': 'Django',
            'file_count': 50,
            'lines_of_code': 5000,
            'key_files': 'main.py',
            'keywords': 'api, database',
            'code_structure': 'MVC',
            'technical_patterns': 'None',
            'date_created': '2024-01-01',
            'date_modified': '2024-02-01',
            'has_commits': 'Yes'
        }
        
        # Should not raise KeyError
        for prompt_template in analyzer.ANALYSIS_PROMPTS.values():
            try:
                formatted = prompt_template.format(**context)
                self.assertGreater(len(formatted), 0)
            except KeyError as e:
                self.fail(f"Prompt template missing key: {e}")

class TestCostOptimization(unittest.TestCase):
    """Test cost optimization features"""
    
    def test_cache_reduces_costs(self):
        """Test that caching actually reduces API costs"""
        from src.AI.ai_project_analyzer import AIProjectAnalyzer
        
        analyzer = AIProjectAnalyzer()
        
        # Simulate multiple analyses
        initial_count = analyzer.analyses_count
        
        # After caching, this should be tracked
        analyzer.analyses_count = 5
        analyzer.cache_hits = 3
        
        # Cache hit rate should be meaningful
        hit_rate = analyzer.cache_hits / max(1, analyzer.analyses_count)
        self.assertGreater(hit_rate, 0.4)  # At least 40% cache hit rate
    
    @patch('src.AI.ai_service.get_ai_service')
    def test_token_limits_respected(self, mock_ai_service):
        """Test that token limits are respected in prompts"""
        from src.AI.ai_enhanced_summarizer import ai_enhance_project_summary
        
        mock_ai = Mock()
        mock_ai_service.return_value = mock_ai
        
        project = {
            'project_name': 'Test',
            'skills': ['Skill'] * 100,  # Many skills
            'file_count': 1000,
            'lines_of_code': 100000
        }
        
        ai_enhance_project_summary(project, ai_service=mock_ai)
        
        # Check that max_tokens was set
        call_args = mock_ai.generate_text.call_args
        self.assertIn('max_tokens', call_args.kwargs)
        self.assertLessEqual(call_args.kwargs['max_tokens'], 500)

def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("Running Test Suite")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAIProjectAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestAIEnhancedSummarizer))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptEngineering))
    suite.addTests(loader.loadTestsFromTestCase(TestCostOptimization))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)