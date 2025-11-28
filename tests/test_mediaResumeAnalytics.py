"""
Comprehensive test suite for media-specific resume analytics.

Tests:
- Visual media analysis integration
- Portfolio impact scoring
- Software proficiency detection
- Portfolio readiness validation
"""

import os
import sys
import pytest
import tempfile
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.mediaResumeAnalytics import (
    analyze_media_project,
    calculate_portfolio_impact,
    detect_software_skill_level,
    validate_portfolio_readiness,
    analyze_media_project_comprehensive,
    get_portfolio_quality_phrase,
    should_emphasize_software_proficiency
)
from src.Databases.database import db_manager, Project


class TestMediaResumeAnalytics:
    """Test suite for media-specific resume analytics"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def temp_media_project(self):
        """Create a temporary project with actual media files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create sample image files
        for i in range(5):
            img_path = os.path.join(temp_dir, f'image{i}.png')
            with open(img_path, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)  # Minimal PNG
        
        # Create project
        project_data = {
            'name': 'Portfolio Project',
            'file_path': temp_dir,
            'project_type': 'visual_media',
            'file_count': 5,
            'total_size_bytes': 5000,
            'languages': ['Adobe Photoshop'],
            'skills': ['Photo Editing']
        }
        project = db_manager.create_project(project_data)
        
        yield project
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def beginner_media_project(self):
        """Create a beginner-level media project"""
        project_data = {
            'name': 'Beginner Portfolio',
            'file_path': '/test/beginner',
            'project_type': 'visual_media',
            'file_count': 8,
            'total_size_bytes': 30 * 1024 * 1024,  # 30 MB
            'languages': ['Canva'],
            'skills': ['Graphic Design']
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def professional_media_project(self):
        """Create a professional-level media project"""
        project_data = {
            'name': 'Professional Portfolio',
            'file_path': '/test/professional',
            'project_type': 'visual_media',
            'file_count': 60,
            'total_size_bytes': 2 * 1024 * 1024 * 1024,  # 2 GB
            'languages': ['Adobe Photoshop', 'Adobe Illustrator', 'Blender'],
            'skills': ['Photo Editing', 'Vector Illustration', '3D Modeling', 'Typography']
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # MEDIA ANALYSIS TESTS
    # ============================================
    
    def test_analyze_media_project_basic(self, temp_media_project):
        """Test basic media project analysis"""
        result = analyze_media_project(temp_media_project)
        
        assert 'analysis_available' in result
    
    def test_analyze_media_project_wrong_type(self):
        """Test media analysis with wrong project type"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        result = analyze_media_project(project)
        
        assert result['analysis_available'] is False
        assert 'error' in result
    
    def test_analyze_media_project_invalid_path(self):
        """Test media analysis with invalid path"""
        project_data = {
            'name': 'Invalid Project',
            'file_path': '/nonexistent/path',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        
        result = analyze_media_project(project)
        
        assert result['analysis_available'] is False
    
    # ============================================
    # PORTFOLIO IMPACT TESTS
    # ============================================
    
    def test_calculate_portfolio_impact_beginner(self, beginner_media_project):
        """Test portfolio impact for beginner"""
        result = calculate_portfolio_impact(beginner_media_project)
        
        assert result['impact_available'] is True
        assert result['impact_score'] < 60
        assert result['grade'] in ['Beginner', 'Developing']
    
    def test_calculate_portfolio_impact_professional(self, professional_media_project):
        """Test portfolio impact for professional"""
        result = calculate_portfolio_impact(professional_media_project)
        
        assert result['impact_available'] is True
        assert result['impact_score'] >= 80
        assert result['grade'] == 'Professional'
    
    def test_calculate_portfolio_impact_wrong_type(self):
        """Test portfolio impact with wrong project type"""
        project_data = {
            'name': 'Text Project',
            'file_path': '/test/text',
            'project_type': 'text'
        }
        project = db_manager.create_project(project_data)
        
        result = calculate_portfolio_impact(project)
        
        assert result['impact_available'] is False
        assert 'error' in result
    
    def test_calculate_portfolio_impact_insights(self, professional_media_project):
        """Test that portfolio impact provides insights"""
        result = calculate_portfolio_impact(professional_media_project)
        
        assert 'insights' in result
        assert isinstance(result['insights'], list)
        assert len(result['insights']) > 0
    
    def test_calculate_portfolio_impact_recommendation(self, beginner_media_project):
        """Test that portfolio impact provides recommendations"""
        result = calculate_portfolio_impact(beginner_media_project)
        
        assert 'recommendation' in result
        assert isinstance(result['recommendation'], str)
        assert len(result['recommendation']) > 0
    
    # ============================================
    # SOFTWARE SKILL LEVEL TESTS
    # ============================================
    
    def test_detect_software_skill_level_beginner(self, beginner_media_project):
        """Test skill level detection for beginner"""
        result = detect_software_skill_level(beginner_media_project)
        
        assert result['skill_level_available'] is True
        assert result['skill_tier'] == 'beginner'
        assert result['tool_count'] == 1
    
    def test_detect_software_skill_level_expert(self, professional_media_project):
        """Test skill level detection for expert (has Blender)"""
        result = detect_software_skill_level(professional_media_project)
        
        assert result['skill_level_available'] is True
        assert result['skill_tier'] == 'expert'
        assert len(result['expert_tools']) > 0
    
    def test_detect_software_skill_level_intermediate(self):
        """Test skill level detection for intermediate"""
        project_data = {
            'name': 'Intermediate Portfolio',
            'file_path': '/test/intermediate',
            'project_type': 'visual_media',
            'languages': ['Adobe Photoshop', 'Adobe Illustrator']
        }
        project = db_manager.create_project(project_data)
        
        result = detect_software_skill_level(project)
        
        assert result['skill_tier'] in ['intermediate', 'advanced']
    
    def test_detect_software_skill_level_recommended_verb(self, professional_media_project):
        """Test that skill level provides recommended verb"""
        result = detect_software_skill_level(professional_media_project)
        
        assert 'recommended_verb' in result
        assert isinstance(result['recommended_verb'], str)
    
    def test_detect_software_skill_level_wrong_type(self):
        """Test skill level detection with wrong project type"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        result = detect_software_skill_level(project)
        
        assert result['skill_level_available'] is False
    
    # ============================================
    # PORTFOLIO READINESS TESTS
    # ============================================
    
    def test_validate_portfolio_readiness_not_ready(self, beginner_media_project):
        """Test portfolio readiness for beginner"""
        result = validate_portfolio_readiness(beginner_media_project)
        
        assert result['readiness_available'] is True
        assert result['readiness_score'] < 75
        assert result['is_job_ready'] is False
    
    def test_validate_portfolio_readiness_ready(self, professional_media_project):
        """Test portfolio readiness for professional"""
        result = validate_portfolio_readiness(professional_media_project)
        
        assert result['readiness_available'] is True
        assert result['readiness_score'] >= 75
        assert result['is_job_ready'] is True
    
    def test_validate_portfolio_readiness_checklist(self, professional_media_project):
        """Test that portfolio readiness provides checklist"""
        result = validate_portfolio_readiness(professional_media_project)
        
        assert 'checklist' in result
        checklist = result['checklist']
        
        assert 'sufficient_quantity' in checklist
        assert 'professional_software' in checklist
        assert 'high_quality' in checklist
        assert 'diverse_skills' in checklist
    
    def test_validate_portfolio_readiness_recommendations(self, beginner_media_project):
        """Test that portfolio readiness provides recommendations"""
        result = validate_portfolio_readiness(beginner_media_project)
        
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
        # Beginner should have recommendations
        assert len(result['recommendations']) > 0
    
    def test_validate_portfolio_readiness_wrong_type(self):
        """Test portfolio readiness with wrong project type"""
        project_data = {
            'name': 'Text Project',
            'file_path': '/test/text',
            'project_type': 'text'
        }
        project = db_manager.create_project(project_data)
        
        result = validate_portfolio_readiness(project)
        
        assert result['readiness_available'] is False
    
    # ============================================
    # COMPREHENSIVE ANALYSIS TESTS
    # ============================================
    
    def test_analyze_media_project_comprehensive(self, professional_media_project):
        """Test comprehensive media analysis"""
        result = analyze_media_project_comprehensive(professional_media_project)
        
        assert 'media_analysis' in result
        assert 'portfolio_impact' in result
        assert 'skill_level' in result
        assert 'portfolio_readiness' in result
    
    def test_comprehensive_analysis_structure(self, beginner_media_project):
        """Test that comprehensive analysis returns proper structure"""
        result = analyze_media_project_comprehensive(beginner_media_project)
        
        # All four analyses should be present
        assert len(result) == 4
        
        # Each should have a dictionary
        for analysis in result.values():
            assert isinstance(analysis, dict)
    
    # ============================================
    # HELPER FUNCTION TESTS
    # ============================================
    
    def test_get_portfolio_quality_phrase_beginner(self, beginner_media_project):
        """Test quality phrase for beginner portfolio"""
        phrase = get_portfolio_quality_phrase(beginner_media_project)
        
        assert isinstance(phrase, str)
        assert 'portfolio' in phrase.lower() or 'work' in phrase.lower()
    
    def test_get_portfolio_quality_phrase_professional(self, professional_media_project):
        """Test quality phrase for professional portfolio"""
        phrase = get_portfolio_quality_phrase(professional_media_project)
        
        assert isinstance(phrase, str)
        assert 'professional' in phrase.lower() or 'comprehensive' in phrase.lower()
    
    def test_should_emphasize_software_proficiency_beginner(self, beginner_media_project):
        """Test proficiency emphasis for beginner"""
        result = should_emphasize_software_proficiency(beginner_media_project)
        
        assert isinstance(result, bool)
        assert result is False  # Beginner shouldn't emphasize proficiency
    
    def test_should_emphasize_software_proficiency_expert(self, professional_media_project):
        """Test proficiency emphasis for expert"""
        result = should_emphasize_software_proficiency(professional_media_project)
        
        assert isinstance(result, bool)
        assert result is True  # Expert should emphasize proficiency
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    def test_all_analyses_work_together(self, professional_media_project):
        """Test that all media analytics work together"""
        # Run each analysis
        media_analysis = analyze_media_project(professional_media_project)
        impact = calculate_portfolio_impact(professional_media_project)
        skill_level = detect_software_skill_level(professional_media_project)
        readiness = validate_portfolio_readiness(professional_media_project)
        
        # All should return dictionaries
        assert isinstance(media_analysis, dict)
        assert isinstance(impact, dict)
        assert isinstance(skill_level, dict)
        assert isinstance(readiness, dict)
        
        # Get helper values
        quality = get_portfolio_quality_phrase(professional_media_project)
        emphasize = should_emphasize_software_proficiency(professional_media_project)
        
        assert isinstance(quality, str)
        assert isinstance(emphasize, bool)
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully"""
        # Create project with invalid data
        project_data = {
            'name': 'Bad Project',
            'file_path': '/nonexistent',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        
        # All functions should handle errors gracefully
        media_analysis = analyze_media_project(project)
        impact = calculate_portfolio_impact(project)
        skill_level = detect_software_skill_level(project)
        readiness = validate_portfolio_readiness(project)
        
        # Should not raise exceptions
        assert 'analysis_available' in media_analysis or 'impact_available' in impact
        assert 'skill_level_available' in skill_level
        assert 'readiness_available' in readiness


if __name__ == "__main__":
    pytest.main([__file__, '-v'])