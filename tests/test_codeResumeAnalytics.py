"""
Comprehensive test suite for code-specific resume analytics.

Tests:
- Code efficiency analysis integration
- Technical density measurement
- Keyword clustering
- Skill extraction
"""

import os
import sys
import pytest
import tempfile
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.codeResumeAnalytics import (
    analyze_code_efficiency,
    analyze_technical_density,
    analyze_keyword_clusters,
    extract_project_skills,
    analyze_code_project_comprehensive,
    get_code_quality_phrase,
    get_technical_depth_phrase,
    should_emphasize_efficiency
)
from src.Databases.database import db_manager, Project


class TestCodeResumeAnalytics:
    """Test suite for code-specific resume analytics"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def temp_code_project(self):
        """Create a temporary project with actual code files"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Create sample Python file
        sample_code = """
import flask
from flask import Flask, request
import pandas as pd
import numpy as np

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    data = pd.DataFrame({'x': [1, 2, 3]})
    return data.to_json()

if __name__ == '__main__':
    app.run()
"""
        code_file = os.path.join(temp_dir, 'app.py')
        with open(code_file, 'w') as f:
            f.write(sample_code)
        
        # Create project
        project_data = {
            'name': 'Flask API',
            'file_path': temp_dir,
            'project_type': 'code',
            'lines_of_code': 150,
            'file_count': 1,
            'languages': ['Python'],
            'frameworks': ['Flask'],
            'skills': ['API Development', 'Data Science']
        }
        project = db_manager.create_project(project_data)
        
        # Add file to database
        db_manager.add_file_to_project({
            'project_id': project.id,
            'file_path': code_file,
            'file_name': 'app.py',
            'file_type': 'code',
            'file_size': len(sample_code),
            'lines_of_code': 15
        })
        
        yield project
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_code_project(self):
        """Create a simple code project for basic tests"""
        project_data = {
            'name': 'Web App',
            'file_path': '/test/webapp',
            'project_type': 'code',
            'lines_of_code': 5000,
            'file_count': 25,
            'languages': ['Python', 'JavaScript'],
            'frameworks': ['Django', 'React'],
            'skills': ['Web Development', 'API Development']
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # CODE EFFICIENCY TESTS
    # ============================================
    
    def test_analyze_code_efficiency_basic(self, temp_code_project):
        """Test basic code efficiency analysis"""
        result = analyze_code_efficiency(temp_code_project)
        
        assert 'efficiency_available' in result
        if result['efficiency_available']:
            assert 'avg_efficiency_score' in result
            assert 'efficiency_level' in result
            assert 'bullet_phrase' in result
    
    def test_analyze_code_efficiency_wrong_type(self):
        """Test efficiency analysis with wrong project type"""
        project_data = {
            'name': 'Media Project',
            'file_path': '/test/media',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        
        result = analyze_code_efficiency(project)
        
        assert result['efficiency_available'] is False
        assert 'error' in result
    
    def test_analyze_code_efficiency_no_files(self, sample_code_project):
        """Test efficiency analysis with no files"""
        result = analyze_code_efficiency(sample_code_project)
        
        assert result['efficiency_available'] is False
        assert 'message' in result
    
    def test_analyze_code_efficiency_with_files(self, temp_code_project):
        """Test efficiency analysis with actual code files"""
        result = analyze_code_efficiency(temp_code_project)
        
        # Should be able to analyze the Python file
        if result.get('efficiency_available'):
            assert result['files_analyzed'] >= 1
            assert 0 <= result['avg_efficiency_score'] <= 100
    
    # ============================================
    # TECHNICAL DENSITY TESTS
    # ============================================
    
    def test_analyze_technical_density_basic(self, temp_code_project):
        """Test technical density analysis"""
        result = analyze_technical_density(temp_code_project)
        
        assert 'density_available' in result
        if result['density_available']:
            assert 'avg_density' in result
            assert 'density_level' in result
            assert 0 <= result['avg_density'] <= 1
    
    def test_analyze_technical_density_wrong_type(self):
        """Test density analysis with wrong project type"""
        project_data = {
            'name': 'Text Project',
            'file_path': '/test/text',
            'project_type': 'text'
        }
        project = db_manager.create_project(project_data)
        
        result = analyze_technical_density(project)
        
        assert result['density_available'] is False
        assert 'error' in result
    
    def test_analyze_technical_density_no_files(self, sample_code_project):
        """Test density analysis with no files"""
        result = analyze_technical_density(sample_code_project)
        
        assert result['density_available'] is False
    
    # ============================================
    # KEYWORD CLUSTERING TESTS
    # ============================================
    
    def test_analyze_keyword_clusters_basic(self, temp_code_project):
        """Test keyword clustering"""
        result = analyze_keyword_clusters(temp_code_project)
        
        assert 'clustering_available' in result
        if result['clustering_available']:
            assert 'top_clusters' in result
            assert 'dominant_cluster' in result
    
    def test_analyze_keyword_clusters_wrong_type(self):
        """Test clustering with wrong project type"""
        project_data = {
            'name': 'Media Project',
            'file_path': '/test/media',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        
        result = analyze_keyword_clusters(project)
        
        assert result['clustering_available'] is False
        assert 'error' in result
    
    def test_analyze_keyword_clusters_no_files(self, sample_code_project):
        """Test clustering with no files"""
        result = analyze_keyword_clusters(sample_code_project)
        
        assert result['clustering_available'] is False
    
    # ============================================
    # SKILL EXTRACTION TESTS
    # ============================================
    
    def test_extract_project_skills_basic(self, temp_code_project):
        """Test skill extraction"""
        result = extract_project_skills(temp_code_project)
        
        assert 'skills_available' in result
        if result['skills_available']:
            assert 'top_skills' in result
            assert 'primary_skill' in result
    
    def test_extract_project_skills_wrong_type(self):
        """Test skill extraction with wrong project type"""
        project_data = {
            'name': 'Text Project',
            'file_path': '/test/text',
            'project_type': 'text'
        }
        project = db_manager.create_project(project_data)
        
        result = extract_project_skills(project)
        
        assert result['skills_available'] is False
        assert 'error' in result
    
    def test_extract_project_skills_invalid_path(self):
        """Test skill extraction with invalid project path"""
        project_data = {
            'name': 'Invalid Project',
            'file_path': '/nonexistent/path',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        result = extract_project_skills(project)
        
        assert result['skills_available'] is False
    
    # ============================================
    # COMPREHENSIVE ANALYSIS TESTS
    # ============================================
    
    def test_analyze_code_project_comprehensive(self, temp_code_project):
        """Test comprehensive code analysis"""
        result = analyze_code_project_comprehensive(temp_code_project)
        
        assert 'efficiency' in result
        assert 'technical_density' in result
        assert 'keyword_clusters' in result
        assert 'skills' in result
    
    def test_comprehensive_analysis_structure(self, sample_code_project):
        """Test that comprehensive analysis returns proper structure"""
        result = analyze_code_project_comprehensive(sample_code_project)
        
        # All four analyses should be present
        assert len(result) == 4
        
        # Each should have availability flag
        for analysis in result.values():
            assert isinstance(analysis, dict)
    
    # ============================================
    # HELPER FUNCTION TESTS
    # ============================================
    
    def test_get_code_quality_phrase_default(self, sample_code_project):
        """Test code quality phrase with no efficiency data"""
        phrase = get_code_quality_phrase(sample_code_project)
        
        assert isinstance(phrase, str)
        assert len(phrase) > 0
    
    def test_get_code_quality_phrase_with_efficiency(self, temp_code_project):
        """Test code quality phrase with efficiency data"""
        phrase = get_code_quality_phrase(temp_code_project)
        
        assert isinstance(phrase, str)
        assert 'code' in phrase.lower()
    
    def test_get_technical_depth_phrase_default(self, sample_code_project):
        """Test technical depth phrase with no density data"""
        phrase = get_technical_depth_phrase(sample_code_project)
        
        assert isinstance(phrase, str)
        assert 'implementation' in phrase.lower() or 'technical' in phrase.lower()
    
    def test_get_technical_depth_phrase_with_density(self, temp_code_project):
        """Test technical depth phrase with density data"""
        phrase = get_technical_depth_phrase(temp_code_project)
        
        assert isinstance(phrase, str)
        assert len(phrase) > 0
    
    def test_should_emphasize_efficiency_default(self, sample_code_project):
        """Test efficiency emphasis check with no data"""
        result = should_emphasize_efficiency(sample_code_project)
        
        assert isinstance(result, bool)
        assert result is False  # No data means don't emphasize
    
    def test_should_emphasize_efficiency_with_data(self, temp_code_project):
        """Test efficiency emphasis check with actual data"""
        result = should_emphasize_efficiency(temp_code_project)
        
        assert isinstance(result, bool)
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    def test_all_analyses_work_together(self, temp_code_project):
        """Test that all code analytics work together"""
        # Run each analysis
        efficiency = analyze_code_efficiency(temp_code_project)
        density = analyze_technical_density(temp_code_project)
        clusters = analyze_keyword_clusters(temp_code_project)
        skills = extract_project_skills(temp_code_project)
        
        # All should return dictionaries
        assert isinstance(efficiency, dict)
        assert isinstance(density, dict)
        assert isinstance(clusters, dict)
        assert isinstance(skills, dict)
        
        # Get helper phrases
        quality = get_code_quality_phrase(temp_code_project)
        depth = get_technical_depth_phrase(temp_code_project)
        emphasize = should_emphasize_efficiency(temp_code_project)
        
        assert isinstance(quality, str)
        assert isinstance(depth, str)
        assert isinstance(emphasize, bool)
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully"""
        # Create project with invalid data
        project_data = {
            'name': 'Bad Project',
            'file_path': '/nonexistent',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        # All functions should handle errors gracefully
        efficiency = analyze_code_efficiency(project)
        density = analyze_technical_density(project)
        clusters = analyze_keyword_clusters(project)
        skills = extract_project_skills(project)
        
        # Should not raise exceptions
        assert 'efficiency_available' in efficiency
        assert 'density_available' in density
        assert 'clustering_available' in clusters
        assert 'skills_available' in skills


if __name__ == "__main__":
    pytest.main([__file__, '-v'])