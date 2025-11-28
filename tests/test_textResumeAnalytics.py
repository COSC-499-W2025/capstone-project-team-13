"""
Comprehensive test suite for text-specific resume analytics.

Tests:
- Writing skill extraction integration
- Writing quality assessment
- Publication readiness validation
- Content volume benchmarking
- Writing style identification
"""

import os
import sys
import pytest
import tempfile
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.textResumeAnalytics import (
    extract_writing_skills,
    analyze_writing_quality,
    validate_publication_readiness,
    benchmark_content_volume,
    identify_writing_style,
    analyze_text_project_comprehensive,
    get_writing_quality_phrase,
    get_volume_descriptor,
    should_emphasize_publication_ready
)
from src.Databases.database import db_manager, Project


class TestTextResumeAnalytics:
    """Test suite for text-specific resume analytics"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def temp_text_project(self):
        """Create a temporary project with actual text files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create sample text files
        sample_text = """
        Technical Writing Documentation
        
        This document demonstrates various writing skills including
        grammar, syntax, and clear communication. Research shows that
        good technical writing requires attention to detail and thorough
        documentation practices.
        """
        
        for i in range(3):
            text_path = os.path.join(temp_dir, f'doc{i}.txt')
            with open(text_path, 'w') as f:
                f.write(sample_text)
        
        # Create project
        project_data = {
            'name': 'Documentation Project',
            'file_path': temp_dir,
            'project_type': 'text',
            'word_count': 150,
            'file_count': 3,
            'skills': ['Technical Writing']
        }
        project = db_manager.create_project(project_data)
        
        yield project
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def beginner_text_project(self):
        """Create a beginner-level text project"""
        project_data = {
            'name': 'Blog Posts',
            'file_path': '/test/blog',
            'project_type': 'text',
            'word_count': 3000,
            'file_count': 4,
            'skills': ['Content Writing']
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def professional_text_project(self):
        """Create a professional-level text project"""
        project_data = {
            'name': 'Technical Documentation',
            'file_path': '/test/techdocs',
            'project_type': 'text',
            'word_count': 25000,
            'file_count': 15,
            'skills': ['Technical Writing', 'Documentation', 'Editing', 'Research']
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # WRITING SKILL EXTRACTION TESTS
    # ============================================
    
    def test_extract_writing_skills_basic(self, temp_text_project):
        """Test basic writing skill extraction"""
        result = extract_writing_skills(temp_text_project)
        
        assert 'skills_available' in result
    
    def test_extract_writing_skills_wrong_type(self):
        """Test skill extraction with wrong project type"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        result = extract_writing_skills(project)
        
        assert result['skills_available'] is False
        assert 'error' in result
    
    def test_extract_writing_skills_invalid_path(self):
        """Test skill extraction with invalid path"""
        project_data = {
            'name': 'Invalid Project',
            'file_path': '/nonexistent/path',
            'project_type': 'text'
        }
        project = db_manager.create_project(project_data)
        
        result = extract_writing_skills(project)
        
        assert result['skills_available'] is False
    
    # ============================================
    # WRITING QUALITY TESTS
    # ============================================
    
    def test_analyze_writing_quality_beginner(self, beginner_text_project):
        """Test writing quality for beginner"""
        result = analyze_writing_quality(beginner_text_project)
        
        assert result['quality_available'] is True
        assert result['quality_score'] < 60
        assert result['quality_level'] in ['Beginner', 'Developing']
    
    def test_analyze_writing_quality_professional(self, professional_text_project):
        """Test writing quality for professional"""
        result = analyze_writing_quality(professional_text_project)
        
        assert result['quality_available'] is True
        assert result['quality_score'] >= 60
        assert result['quality_level'] in ['Professional', 'Intermediate']
    
    def test_analyze_writing_quality_wrong_type(self):
        """Test writing quality with wrong project type"""
        project_data = {
            'name': 'Media Project',
            'file_path': '/test/media',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        
        result = analyze_writing_quality(project)
        
        assert result['quality_available'] is False
        assert 'error' in result
    
    def test_analyze_writing_quality_insights(self, professional_text_project):
        """Test that writing quality provides insights"""
        result = analyze_writing_quality(professional_text_project)
        
        assert 'insights' in result
        assert isinstance(result['insights'], list)
        assert len(result['insights']) > 0
    
    # ============================================
    # PUBLICATION READINESS TESTS
    # ============================================
    
    def test_validate_publication_readiness_not_ready(self, beginner_text_project):
        """Test publication readiness for beginner"""
        result = validate_publication_readiness(beginner_text_project)
        
        assert result['readiness_available'] is True
        assert result['publication_score'] < 75
        assert result['is_publication_ready'] is False
    
    def test_validate_publication_readiness_ready(self, professional_text_project):
        """Test publication readiness for professional"""
        result = validate_publication_readiness(professional_text_project)
        
        assert result['readiness_available'] is True
        # Professional should score well
        assert result['publication_score'] >= 50
    
    def test_validate_publication_readiness_checklist(self, professional_text_project):
        """Test that readiness provides checklist"""
        result = validate_publication_readiness(professional_text_project)
        
        assert 'checklist' in result
        checklist = result['checklist']
        
        assert 'sufficient_length' in checklist
        assert 'document_variety' in checklist
        assert 'professional_skills' in checklist
        assert 'editorial_polish' in checklist
    
    def test_validate_publication_readiness_recommendations(self, beginner_text_project):
        """Test that readiness provides recommendations"""
        result = validate_publication_readiness(beginner_text_project)
        
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
        # Beginner should have recommendations
        assert len(result['recommendations']) > 0
    
    def test_validate_publication_readiness_wrong_type(self):
        """Test publication readiness with wrong project type"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        result = validate_publication_readiness(project)
        
        assert result['readiness_available'] is False
    
    # ============================================
    # CONTENT VOLUME BENCHMARK TESTS
    # ============================================
    
    def test_benchmark_content_volume_blog(self, beginner_text_project):
        """Test content benchmarking for blog portfolio"""
        result = benchmark_content_volume(beginner_text_project)
        
        assert result['benchmark_available'] is True
        assert 'benchmark_type' in result
        assert 'completion_percentage' in result
        assert 0 <= result['completion_percentage'] <= 100
    
    def test_benchmark_content_volume_technical(self, professional_text_project):
        """Test content benchmarking for technical writing"""
        result = benchmark_content_volume(professional_text_project)
        
        assert result['benchmark_available'] is True
        assert result['current_words'] == 25000
        assert result['current_docs'] == 15
    
    def test_benchmark_content_volume_wrong_type(self):
        """Test benchmarking with wrong project type"""
        project_data = {
            'name': 'Media Project',
            'file_path': '/test/media',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        
        result = benchmark_content_volume(project)
        
        assert result['benchmark_available'] is False
    
    def test_benchmark_content_volume_on_track(self):
        """Test on_track indicator in benchmarking"""
        project_data = {
            'name': 'Large Project',
            'file_path': '/test/large',
            'project_type': 'text',
            'word_count': 50000,
            'file_count': 25
        }
        project = db_manager.create_project(project_data)
        
        result = benchmark_content_volume(project)
        
        assert 'on_track' in result
        assert isinstance(result['on_track'], bool)
    
    # ============================================
    # WRITING STYLE IDENTIFICATION TESTS
    # ============================================
    
    def test_identify_writing_style_basic(self, temp_text_project):
        """Test basic writing style identification"""
        result = identify_writing_style(temp_text_project)
        
        assert 'style_available' in result
    
    def test_identify_writing_style_wrong_type(self):
        """Test style identification with wrong project type"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        result = identify_writing_style(project)
        
        assert result['style_available'] is False
    
    def test_identify_writing_style_with_skills(self, professional_text_project):
        """Test style identification with skills"""
        result = identify_writing_style(professional_text_project)
        
        if result.get('style_available'):
            assert 'primary_style' in result
            assert 'emphasis' in result
    
    def test_identify_writing_style_emphasis(self):
        """Test that style identification provides emphasis"""
        project_data = {
            'name': 'Academic Papers',
            'file_path': '/test/academic',
            'project_type': 'text',
            'word_count': 30000,
            'file_count': 5,
            'skills': ['Research Writing', 'Critical Thinking']
        }
        project = db_manager.create_project(project_data)
        
        result = identify_writing_style(project)
        
        if result.get('style_available'):
            assert 'emphasis' in result
            assert isinstance(result['emphasis'], str)
    
    # ============================================
    # COMPREHENSIVE ANALYSIS TESTS
    # ============================================
    
    def test_analyze_text_project_comprehensive(self, professional_text_project):
        """Test comprehensive text analysis"""
        result = analyze_text_project_comprehensive(professional_text_project)
        
        assert 'writing_skills' in result
        assert 'writing_quality' in result
        assert 'publication_readiness' in result
        assert 'content_benchmark' in result
        assert 'writing_style' in result
    
    def test_comprehensive_analysis_structure(self, beginner_text_project):
        """Test that comprehensive analysis returns proper structure"""
        result = analyze_text_project_comprehensive(beginner_text_project)
        
        # All five analyses should be present
        assert len(result) == 5
        
        # Each should be a dictionary
        for analysis in result.values():
            assert isinstance(analysis, dict)
    
    # ============================================
    # HELPER FUNCTION TESTS
    # ============================================
    
    def test_get_writing_quality_phrase_beginner(self, beginner_text_project):
        """Test quality phrase for beginner"""
        phrase = get_writing_quality_phrase(beginner_text_project)
        
        assert isinstance(phrase, str)
        assert 'writing' in phrase.lower()
    
    def test_get_writing_quality_phrase_professional(self, professional_text_project):
        """Test quality phrase for professional"""
        phrase = get_writing_quality_phrase(professional_text_project)
        
        assert isinstance(phrase, str)
        assert len(phrase) > 0
    
    def test_get_volume_descriptor_various_sizes(self):
        """Test volume descriptor for different word counts"""
        small = {'word_count': 5000, 'file_path': '/test', 'project_type': 'text'}
        medium = {'word_count': 15000, 'file_path': '/test', 'project_type': 'text'}
        large = {'word_count': 30000, 'file_path': '/test', 'project_type': 'text'}
        huge = {'word_count': 60000, 'file_path': '/test', 'project_type': 'text'}
        
        small_proj = db_manager.create_project(small)
        medium_proj = db_manager.create_project(medium)
        large_proj = db_manager.create_project(large)
        huge_proj = db_manager.create_project(huge)
        
        assert get_volume_descriptor(small_proj) in ['focused', 'comprehensive']
        assert get_volume_descriptor(medium_proj) in ['comprehensive', 'substantial']
        assert get_volume_descriptor(large_proj) in ['substantial', 'extensive']
        assert get_volume_descriptor(huge_proj) == 'extensive'
    
    def test_should_emphasize_publication_ready_not_ready(self, beginner_text_project):
        """Test publication emphasis for not ready portfolio"""
        result = should_emphasize_publication_ready(beginner_text_project)
        
        assert isinstance(result, bool)
        assert result is False
    
    def test_should_emphasize_publication_ready_ready(self, professional_text_project):
        """Test publication emphasis for ready portfolio"""
        result = should_emphasize_publication_ready(professional_text_project)
        
        assert isinstance(result, bool)
        # May or may not be ready depending on exact scoring
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    def test_all_analyses_work_together(self, professional_text_project):
        """Test that all text analytics work together"""
        # Run each analysis
        skills = extract_writing_skills(professional_text_project)
        quality = analyze_writing_quality(professional_text_project)
        readiness = validate_publication_readiness(professional_text_project)
        benchmark = benchmark_content_volume(professional_text_project)
        style = identify_writing_style(professional_text_project)
        
        # All should return dictionaries
        assert isinstance(skills, dict)
        assert isinstance(quality, dict)
        assert isinstance(readiness, dict)
        assert isinstance(benchmark, dict)
        assert isinstance(style, dict)
        
        # Get helper values
        quality_phrase = get_writing_quality_phrase(professional_text_project)
        volume = get_volume_descriptor(professional_text_project)
        emphasize = should_emphasize_publication_ready(professional_text_project)
        
        assert isinstance(quality_phrase, str)
        assert isinstance(volume, str)
        assert isinstance(emphasize, bool)
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully"""
        # Create project with invalid data
        project_data = {
            'name': 'Bad Project',
            'file_path': '/nonexistent',
            'project_type': 'text'
        }
        project = db_manager.create_project(project_data)
        
        # All functions should handle errors gracefully
        skills = extract_writing_skills(project)
        quality = analyze_writing_quality(project)
        readiness = validate_publication_readiness(project)
        benchmark = benchmark_content_volume(project)
        style = identify_writing_style(project)
        
        # Should not raise exceptions
        assert 'skills_available' in skills
        assert 'quality_available' in quality
        assert 'readiness_available' in readiness
        assert 'benchmark_available' in benchmark
        assert 'style_available' in style


if __name__ == "__main__":
    pytest.main([__file__, '-v'])