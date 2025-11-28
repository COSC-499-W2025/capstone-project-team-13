"""
Comprehensive test suite for shared resume analytics functions.

Tests:
- ATS optimization scoring
- Before/After comparison generation
- Role-level context generation
- Success evidence utilities
"""

import os
import sys
import pytest
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Analysis.resumeAnalytics import (
    calculate_ats_score,
    score_all_bullets,
    generate_before_after_comparison,
    get_role_appropriate_verb,
    generate_role_context,
    populate_success_evidence,
    get_success_evidence,
    has_success_metrics,
    extract_metrics_from_bullet,
    suggest_improvements
)
from src.Databases.database import db_manager, Project


class TestResumeAnalytics:
    """Test suite for shared resume analytics"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_code_project(self):
        """Create a sample code project"""
        project_data = {
            'name': 'E-Commerce Platform',
            'file_path': '/test/ecommerce',
            'project_type': 'code',
            'lines_of_code': 8500,
            'file_count': 45,
            'languages': ['Python', 'JavaScript'],
            'frameworks': ['Django', 'React'],
            'skills': ['API Development', 'Database Design', 'Frontend Development']
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def sample_media_project(self):
        """Create a sample media project"""
        project_data = {
            'name': 'Brand Identity',
            'file_path': '/test/branding',
            'project_type': 'visual_media',
            'file_count': 35,
            'total_size_bytes': 200 * 1024 * 1024,
            'languages': ['Adobe Illustrator', 'Adobe Photoshop'],
            'skills': ['Logo Design', 'Brand Strategy', 'Typography']
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def sample_text_project(self):
        """Create a sample text project"""
        project_data = {
            'name': 'Technical Documentation',
            'file_path': '/test/docs',
            'project_type': 'text',
            'word_count': 15000,
            'file_count': 12,
            'skills': ['Technical Writing', 'Documentation', 'API Documentation']
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # ATS SCORING TESTS
    # ============================================
    
    def test_calculate_ats_score_excellent_bullet(self):
        """Test ATS scoring for high-quality bullet"""
        bullet = "Developed scalable REST API using Python and Django, improving performance by 40%"
        score_data = calculate_ats_score(bullet, 'code')
        
        assert score_data['score'] >= 70
        assert score_data['has_metrics'] is True
        assert len(score_data['keywords']) >= 2
        assert 'grade' in score_data
    
    def test_calculate_ats_score_poor_bullet(self):
        """Test ATS scoring for low-quality bullet"""
        bullet = "Made a project"
        score_data = calculate_ats_score(bullet, 'code')
        
        assert score_data['score'] < 60
        assert score_data['has_metrics'] is False
        assert len(score_data['feedback']) > 0
    
    def test_calculate_ats_score_detects_keywords(self):
        """Test keyword detection in ATS scoring"""
        bullet = "Built application using React, Node.js, and PostgreSQL database"
        score_data = calculate_ats_score(bullet, 'code')
        
        assert len(score_data['keywords']) >= 2
        keywords_lower = [k.lower() for k in score_data['keywords']]
        assert any(k in keywords_lower for k in ['react', 'node', 'postgresql'])
    
    def test_calculate_ats_score_length_validation(self):
        """Test length scoring in ATS"""
        short = "Made app"
        optimal = "Developed web application using React and Node.js with REST API"
        long = "Developed comprehensive web application using React framework and Node.js backend with REST API integration and PostgreSQL database including user authentication system"
        
        short_score = calculate_ats_score(short, 'code')
        optimal_score = calculate_ats_score(optimal, 'code')
        long_score = calculate_ats_score(long, 'code')
        
        assert optimal_score['score'] >= short_score['score']
        assert optimal_score['score'] >= long_score['score']
    
    def test_calculate_ats_score_project_type_keywords(self):
        """Test that ATS uses project-type-specific keywords"""
        media_bullet = "Created visual content using Photoshop and Illustrator for branding"
        text_bullet = "Authored technical documentation with SEO optimization"
        
        media_score = calculate_ats_score(media_bullet, 'visual_media')
        text_score = calculate_ats_score(text_bullet, 'text')
        
        assert len(media_score['keywords']) > 0
        assert len(text_score['keywords']) > 0
    
    def test_score_all_bullets(self):
        """Test batch scoring of multiple bullets"""
        bullets = [
            "Developed REST API using Python and Django",
            "Built responsive frontend with React and TypeScript",
            "Implemented automated testing with pytest"
        ]
        
        scoring = score_all_bullets(bullets, 'code')
        
        assert 'overall_score' in scoring
        assert 'individual_scores' in scoring
        assert len(scoring['individual_scores']) == 3
        assert 'unique_keywords' in scoring
        assert scoring['overall_score'] >= 0
        assert scoring['overall_score'] <= 100
    
    # ============================================
    # BEFORE/AFTER COMPARISON TESTS
    # ============================================
    
    def test_generate_before_after_code(self, sample_code_project):
        """Test before/after comparison for code project"""
        optimized = "Engineered full-stack e-commerce platform using Django and React with PostgreSQL"
        comparison = generate_before_after_comparison(sample_code_project, optimized)
        
        assert 'before' in comparison
        assert 'after' in comparison
        assert 'improvements' in comparison
        assert comparison['after']['ats_score'] >= comparison['before']['ats_score']
    
    def test_generate_before_after_media(self, sample_media_project):
        """Test before/after comparison for media project"""
        optimized = "Crafted comprehensive brand identity using Adobe Illustrator with 35+ assets"
        comparison = generate_before_after_comparison(sample_media_project, optimized)
        
        assert comparison['before']['bullet'] != comparison['after']['bullet']
        assert len(comparison['improvements']) > 0
    
    def test_generate_before_after_text(self, sample_text_project):
        """Test before/after comparison for text project"""
        optimized = "Authored 15K+ words of technical documentation across 12 documents"
        comparison = generate_before_after_comparison(sample_text_project, optimized)
        
        assert 'improvement_percentage' in comparison
        assert comparison['improvement_percentage'] > 0
    
    def test_before_after_shows_improvements(self, sample_code_project):
        """Test that improvements are listed"""
        optimized = "Developed scalable API using Python Django with 40% performance improvement"
        comparison = generate_before_after_comparison(sample_code_project, optimized)
        
        assert isinstance(comparison['improvements'], list)
        assert len(comparison['improvements']) >= 1
    
    # ============================================
    # ROLE-LEVEL CONTEXT TESTS
    # ============================================
    
    def test_get_role_appropriate_verb_all_levels(self):
        """Test verb selection for all role levels"""
        levels = ['junior', 'mid', 'senior', 'lead']
        
        for level in levels:
            verb = get_role_appropriate_verb(level, 'code')
            assert isinstance(verb, str)
            assert len(verb) > 0
    
    def test_get_role_appropriate_verb_invalid_defaults(self):
        """Test that invalid role level defaults to mid"""
        verb = get_role_appropriate_verb('invalid', 'code')
        mid_verb = get_role_appropriate_verb('mid', 'code')
        assert verb == mid_verb
    
    def test_generate_role_context_junior(self, sample_code_project):
        """Test role context for junior level"""
        context = generate_role_context(sample_code_project, 'junior')
        
        assert 'focus' in context
        assert 'team_phrase' in context
        assert 'emphasis' in context
        assert 'learning' in context['focus'].lower() or 'implementation' in context['focus'].lower()
    
    def test_generate_role_context_senior(self, sample_code_project):
        """Test role context for senior level"""
        context = generate_role_context(sample_code_project, 'senior')
        
        assert 'architecture' in context['focus'].lower() or 'leadership' in context['focus'].lower()
    
    def test_generate_role_context_with_team(self, sample_code_project):
        """Test role context with team members"""
        # Add contributors
        db_manager.add_contributor_to_project({
            'project_id': sample_code_project.id,
            'name': 'Dev 1',
            'commit_count': 50
        })
        db_manager.add_contributor_to_project({
            'project_id': sample_code_project.id,
            'name': 'Dev 2',
            'commit_count': 30
        })
        
        project = db_manager.get_project(sample_code_project.id)
        context = generate_role_context(project, 'lead')
        
        assert 'team' in context['team_phrase'].lower()
    
    # ============================================
    # SUCCESS EVIDENCE TESTS
    # ============================================
    
    def test_populate_success_evidence(self, sample_code_project):
        """Test populating success evidence"""
        metrics = {
            'users': 1000,
            'performance_improvement': 40,
            'success_rate': 95
        }
        
        populate_success_evidence(sample_code_project, metrics)
        
        # Reload project
        project = db_manager.get_project(sample_code_project.id)
        assert project.success_evidence is not None
    
    def test_get_success_evidence(self, sample_code_project):
        """Test retrieving success evidence"""
        metrics = {'users': 500, 'uptime': 99.9}
        populate_success_evidence(sample_code_project, metrics)
        
        project = db_manager.get_project(sample_code_project.id)
        retrieved = get_success_evidence(project)
        
        assert retrieved is not None
        assert retrieved['users'] == 500
        assert retrieved['uptime'] == 99.9
    
    def test_get_success_evidence_none(self, sample_code_project):
        """Test getting success evidence when none exists"""
        evidence = get_success_evidence(sample_code_project)
        assert evidence is None
    
    def test_has_success_metrics(self, sample_code_project):
        """Test checking for success metrics"""
        assert has_success_metrics(sample_code_project) is False
        
        populate_success_evidence(sample_code_project, {'users': 100})
        project = db_manager.get_project(sample_code_project.id)
        
        assert has_success_metrics(project) is True
    
    # ============================================
    # UTILITY FUNCTION TESTS
    # ============================================
    
    def test_extract_metrics_from_bullet(self):
        """Test metric extraction from bullets"""
        bullet = "Improved performance by 40% and processed 10K+ requests with 5 GB data"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert len(metrics) > 0
        assert any('40%' in m for m in metrics)
        assert any('10K' in m.upper() for m in metrics)
    
    def test_extract_metrics_no_metrics(self):
        """Test metric extraction with no metrics"""
        bullet = "Developed a web application"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert len(metrics) == 0
    
    def test_suggest_improvements_low_score(self):
        """Test improvement suggestions for low-scoring bullet"""
        bullet = "Made a project"
        suggestions = suggest_improvements(bullet, 'code')
        
        assert len(suggestions) > 0
        assert any('metric' in s.lower() for s in suggestions)
    
    def test_suggest_improvements_high_score(self):
        """Test improvement suggestions for high-scoring bullet"""
        bullet = "Developed scalable REST API using Python Django with 40% performance boost"
        suggestions = suggest_improvements(bullet, 'code')
        
        # High-scoring bullets should have few or no suggestions
        assert len(suggestions) <= 2
    
    # ============================================
    # INTEGRATION TESTS
    # ============================================
    
    def test_all_functions_work_together(self, sample_code_project):
        """Test that all shared functions work together"""
        # Create bullet
        bullet = "Developed REST API using Python and Django"
        
        # ATS scoring
        ats = calculate_ats_score(bullet, 'code')
        assert ats['score'] >= 0
        
        # Before/after
        comparison = generate_before_after_comparison(sample_code_project, bullet)
        assert comparison['after']['ats_score'] >= 0
        
        # Role context
        context = generate_role_context(sample_code_project, 'mid')
        assert context['focus'] is not None
        
        # Success evidence
        populate_success_evidence(sample_code_project, {'users': 100})
        project = db_manager.get_project(sample_code_project.id)
        assert has_success_metrics(project) is True


if __name__ == "__main__":
    pytest.main([__file__, '-v'])