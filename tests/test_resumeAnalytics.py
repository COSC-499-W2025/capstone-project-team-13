"""
Comprehensive test suite for shared resume analytics functions.

Tests:
- ATS optimization scoring
- Success evidence utilities
- Utility functions
- Batch scoring and grade distribution

Note: Improvement functions have been removed from resumeAnalytics.
Bullets are now optimized during generation in the bullet generators.
"""

import os
import sys
import pytest
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.resumeAnalytics import (
    calculate_ats_score,
    score_all_bullets,
    populate_success_evidence,
    get_success_evidence,
    has_success_metrics,
    extract_metrics_from_bullet,
    suggest_improvements,
    TECHNICAL_KEYWORDS,
    STRONG_ACTION_VERBS
)
from src.Databases.database import db_manager, Project


class TestATSScoring:
    """Test suite for ATS optimization scoring"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
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
    
    def test_calculate_ats_score_strong_action_verb(self):
        """Test that strong action verbs get full points"""
        strong_verb_bullet = "Developed REST API using Python"
        weak_verb_bullet = "Made REST API using Python"
        
        strong_score = calculate_ats_score(strong_verb_bullet, 'code')
        weak_score = calculate_ats_score(weak_verb_bullet, 'code')
        
        assert strong_score['score'] > weak_score['score']
    
    def test_calculate_ats_score_returns_all_fields(self):
        """Test that ATS scoring returns all expected fields"""
        bullet = "Developed web app using React and Node.js"
        score_data = calculate_ats_score(bullet, 'code')
        
        assert 'score' in score_data
        assert 'grade' in score_data
        assert 'feedback' in score_data
        assert 'keywords' in score_data
        assert 'word_count' in score_data
        assert 'has_metrics' in score_data
    
    def test_calculate_ats_score_grade_classification(self):
        """Test grade classification boundaries"""
        excellent = "Developed scalable REST API using Python Django PostgreSQL, improving performance by 40%"
        poor = "Did stuff"
        
        excellent_score = calculate_ats_score(excellent, 'code')
        poor_score = calculate_ats_score(poor, 'code')
        
        assert 'A' in excellent_score['grade'] or 'B' in excellent_score['grade']
        assert 'D' in poor_score['grade'] or 'C' in poor_score['grade']
    
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
        assert 'grade_distribution' in scoring
        assert scoring['overall_score'] >= 0
        assert scoring['overall_score'] <= 100
    
    def test_score_all_bullets_grade_distribution(self):
        """Test grade distribution in batch scoring"""
        bullets = [
            "Developed scalable REST API using Python Django with 40% performance boost",
            "Made a thing",
            "Built frontend with React"
        ]
        
        scoring = score_all_bullets(bullets, 'code')
        
        assert 'grade_distribution' in scoring
        assert 'A+' in scoring['grade_distribution']
        assert 'D' in scoring['grade_distribution']
        total_grades = sum(scoring['grade_distribution'].values())
        assert total_grades == 3
    
    def test_score_all_bullets_aggregate_keywords(self):
        """Test that batch scoring aggregates keywords correctly"""
        bullets = [
            "Developed REST API using Python",
            "Built frontend with React and TypeScript",
            "Managed PostgreSQL database"
        ]
        
        scoring = score_all_bullets(bullets, 'code')
        
        assert scoring['total_keywords'] > 0
        assert 'unique_keywords' in scoring
        assert isinstance(scoring['unique_keywords'], list)
    
    def test_score_all_bullets_bullets_with_metrics(self):
        """Test that batch scoring counts bullets with metrics"""
        bullets = [
            "Developed API with 5000+ lines of code",
            "Built frontend",
            "Managed 100+ files"
        ]
        
        scoring = score_all_bullets(bullets, 'code')
        
        assert 'bullets_with_metrics' in scoring
        assert scoring['bullets_with_metrics'] == 2


class TestSuccessEvidence:
    """Test suite for success evidence utility functions"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project"""
        project_data = {
            'name': 'Test Project',
            'file_path': '/test/project',
            'project_type': 'code'
        }
        return db_manager.create_project(project_data)
    
    def test_populate_success_evidence(self, sample_project):
        """Test populating success evidence"""
        metrics = {
            'users': 1000,
            'performance_improvement': 40,
            'success_rate': 95
        }
        
        populate_success_evidence(sample_project, metrics)
        
        # Reload project
        project = db_manager.get_project(sample_project.id)
        assert project.success_evidence is not None
    
    def test_get_success_evidence(self, sample_project):
        """Test retrieving success evidence"""
        metrics = {'users': 500, 'uptime': 99.9}
        populate_success_evidence(sample_project, metrics)
        
        project = db_manager.get_project(sample_project.id)
        retrieved = get_success_evidence(project)
        
        assert retrieved is not None
        assert retrieved['users'] == 500
        assert retrieved['uptime'] == 99.9
    
    def test_get_success_evidence_none(self, sample_project):
        """Test getting success evidence when none exists"""
        evidence = get_success_evidence(sample_project)
        assert evidence is None
    
    def test_get_success_evidence_invalid_json(self, sample_project):
        """Test handling of invalid JSON in success evidence"""
        # Manually set invalid JSON
        db_manager.update_project(sample_project.id, {'success_evidence': 'invalid json'})
        project = db_manager.get_project(sample_project.id)
        
        evidence = get_success_evidence(project)
        assert evidence is None
    
    def test_has_success_metrics_false(self, sample_project):
        """Test has_success_metrics when no metrics exist"""
        assert has_success_metrics(sample_project) is False
    
    def test_has_success_metrics_true(self, sample_project):
        """Test has_success_metrics when metrics exist"""
        populate_success_evidence(sample_project, {'users': 100})
        project = db_manager.get_project(sample_project.id)
        
        assert has_success_metrics(project) is True
    
    def test_populate_success_evidence_overwrites(self, sample_project):
        """Test that populating success evidence overwrites existing data"""
        populate_success_evidence(sample_project, {'users': 100})
        populate_success_evidence(sample_project, {'users': 200})
        
        project = db_manager.get_project(sample_project.id)
        evidence = get_success_evidence(project)
        
        assert evidence['users'] == 200


class TestUtilityFunctions:
    """Test suite for utility functions"""
    
    def test_extract_metrics_percentage(self):
        """Test extracting percentage metrics"""
        bullet = "Improved performance by 40%"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert '40%' in metrics
    
    def test_extract_metrics_large_numbers(self):
        """Test extracting K/M/B numbers"""
        bullet = "Processed 10K+ requests and served 2M users"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert any('10K' in m.upper() for m in metrics)
        assert any('2M' in m.upper() for m in metrics)
    
    def test_extract_metrics_with_units(self):
        """Test extracting numbers with units"""
        bullet = "Managed 5 GB of data across 100 files"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert len(metrics) > 0
        assert any('GB' in m.upper() or 'files' in m.lower() for m in metrics)
    
    def test_extract_metrics_no_metrics(self):
        """Test extraction with no metrics"""
        bullet = "Developed a web application"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert len(metrics) == 0
    
    def test_extract_metrics_multiple_types(self):
        """Test extracting multiple metric types"""
        bullet = "Processed 50K users with 99.9% uptime and 10 GB storage"
        metrics = extract_metrics_from_bullet(bullet)
        
        assert len(metrics) >= 2
    
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
    
    def test_suggest_improvements_missing_keywords(self):
        """Test suggestions mention keywords when missing"""
        bullet = "Made something with 50% improvement"
        suggestions = suggest_improvements(bullet, 'code')
        
        assert any('keyword' in s.lower() for s in suggestions)
    
    def test_suggest_improvements_short_bullet(self):
        """Test suggestions for short bullets"""
        bullet = "Made app"
        suggestions = suggest_improvements(bullet, 'code')
        
        assert any('expand' in s.lower() or 'detail' in s.lower() for s in suggestions)
    
    def test_suggest_improvements_long_bullet(self):
        """Test suggestions for overly long bullets"""
        bullet = "Developed comprehensive web application system using React framework with TypeScript and Node.js backend server with PostgreSQL relational database management system and Redis caching layer"
        suggestions = suggest_improvements(bullet, 'code')
        
        assert any('condense' in s.lower() for s in suggestions)


class TestConstants:
    """Test suite for module constants"""
    
    def test_technical_keywords_exists(self):
        """Test that TECHNICAL_KEYWORDS is defined"""
        assert TECHNICAL_KEYWORDS is not None
        assert isinstance(TECHNICAL_KEYWORDS, dict)
        assert 'code' in TECHNICAL_KEYWORDS
        assert 'visual_media' in TECHNICAL_KEYWORDS
        assert 'text' in TECHNICAL_KEYWORDS
    
    def test_strong_action_verbs_exists(self):
        """Test that STRONG_ACTION_VERBS is defined"""
        assert STRONG_ACTION_VERBS is not None
        assert isinstance(STRONG_ACTION_VERBS, list)
        assert len(STRONG_ACTION_VERBS) > 0
        assert 'Developed' in STRONG_ACTION_VERBS
        assert 'Built' in STRONG_ACTION_VERBS
    
    def test_technical_keywords_code_category(self):
        """Test code category has expected subcategories"""
        code_keywords = TECHNICAL_KEYWORDS['code']
        
        assert 'languages' in code_keywords
        assert 'frameworks' in code_keywords
        assert isinstance(code_keywords['languages'], list)
    
    def test_technical_keywords_media_category(self):
        """Test media category has expected subcategories"""
        media_keywords = TECHNICAL_KEYWORDS['visual_media']
        
        assert 'software' in media_keywords
        assert 'skills' in media_keywords
        assert isinstance(media_keywords['software'], list)
    
    def test_technical_keywords_text_category(self):
        """Test text category has expected subcategories"""
        text_keywords = TECHNICAL_KEYWORDS['text']
        
        assert 'types' in text_keywords
        assert 'skills' in text_keywords
        assert isinstance(text_keywords['types'], list)


class TestIntegration:
    """Integration tests for scoring functions working together"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project"""
        project_data = {
            'name': 'E-Commerce Platform',
            'file_path': '/test/ecommerce',
            'project_type': 'code',
            'lines_of_code': 8500,
            'file_count': 45,
            'languages': ['Python', 'JavaScript'],
            'frameworks': ['Django', 'React'],
            'skills': ['API Development', 'Database Design']
        }
        return db_manager.create_project(project_data)
    
    def test_full_scoring_workflow(self, sample_project):
        """Test complete scoring workflow"""
        bullets = [
            "Developed REST API using Python and Django",
            "Built responsive frontend with React and TypeScript",
            "Implemented automated testing with pytest"
        ]
        
        # Score individual bullets
        individual_scores = [calculate_ats_score(b, 'code') for b in bullets]
        assert all(s['score'] >= 0 for s in individual_scores)
        
        # Batch score
        batch_scoring = score_all_bullets(bullets, 'code')
        assert batch_scoring['overall_score'] >= 0
        
        # Extract metrics
        all_metrics = []
        for bullet in bullets:
            metrics = extract_metrics_from_bullet(bullet)
            all_metrics.extend(metrics)
        
        # Get suggestions
        suggestions = []
        for bullet in bullets:
            bullet_suggestions = suggest_improvements(bullet, 'code')
            suggestions.extend(bullet_suggestions)
        
        # All functions work together
        assert len(individual_scores) == 3
        assert batch_scoring['overall_score'] <= 100
    
    def test_scoring_with_success_evidence(self, sample_project):
        """Test that scoring works alongside success evidence"""
        # Add success evidence
        populate_success_evidence(sample_project, {
            'users': 1000,
            'performance_improvement': 40
        })
        
        # Score bullets
        bullets = ["Developed API improving performance by 40%"]
        scoring = score_all_bullets(bullets, 'code')
        
        # Both should work
        project = db_manager.get_project(sample_project.id)
        assert has_success_metrics(project) is True
        assert scoring['overall_score'] > 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])