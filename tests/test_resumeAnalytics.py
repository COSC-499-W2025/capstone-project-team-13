"""
Comprehensive test suite for shared resume analytics functions.

Tests:
- ATS optimization scoring
- Before/After comparison generation
- Bullet improvement functions
- Role-level targeting and enhancement
- Success evidence utilities
- Utility functions
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
    improve_bullet,
    generate_before_after_comparison,
    generate_all_improved_bullets,
    get_role_appropriate_verb,
    generate_role_context,
    improve_bullet_for_role,
    improve_all_bullets_for_role,
    populate_success_evidence,
    get_success_evidence,
    has_success_metrics,
    extract_metrics_from_bullet,
    suggest_improvements,
    ROLE_SPECIFIC_VERBS,
    ROLE_EMPHASIS
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


class TestBulletImprovement:
    """Test suite for bullet improvement functions"""
    
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
            'languages': ['Python', 'JavaScript', 'CSS'],
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
            'languages': ['Adobe Illustrator', 'Adobe Photoshop', 'Figma'],
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
            'languages': ['Markdown', 'LaTeX'],
            'skills': ['Technical Writing', 'Documentation', 'API Documentation']
        }
        return db_manager.create_project(project_data)
    
    def test_improve_bullet_upgrades_weak_verb(self, sample_code_project):
        """Test that improve_bullet upgrades weak action verbs"""
        bullet = "Made a web application with Python"
        improved, _ = improve_bullet(bullet, sample_code_project)
        
        # Should start with a strong verb
        first_word = improved.split()[0]
        assert first_word == 'Developed'
    
    def test_improve_bullet_adds_metrics_code(self, sample_code_project):
        """Test that improve_bullet adds metrics for code projects"""
        bullet = "Developed a web application with Python"
        improved, _ = improve_bullet(bullet, sample_code_project)
        
        # Should have added LOC or file count
        assert any(char.isdigit() for char in improved)
    
    def test_improve_bullet_adds_metrics_media(self, sample_media_project):
        """Test that improve_bullet adds metrics for media projects"""
        bullet = "Created visual content for branding"
        improved, _ = improve_bullet(bullet, sample_media_project)
        
        # Should have added file count or size
        assert any(char.isdigit() for char in improved)
    
    def test_improve_bullet_adds_metrics_text(self, sample_text_project):
        """Test that improve_bullet adds metrics for text projects"""
        bullet = "Wrote technical documentation"
        improved, _ = improve_bullet(bullet, sample_text_project)
        
        # Should have added word count or document count
        assert any(char.isdigit() for char in improved)
    
    def test_improve_bullet_tracks_used_additions(self, sample_code_project):
        """Test that improve_bullet tracks what's been added"""
        bullet = "Made a web application"
        _, used_additions = improve_bullet(bullet, sample_code_project)
        
        # Should have tracked at least one addition
        assert len(used_additions) > 0
    
    def test_improve_bullet_avoids_duplicate_additions(self, sample_code_project):
        """Test that multiple bullets get different additions"""
        bullets = [
            "Made a web application",
            "Created backend services",
            "Built frontend components"
        ]
        
        used_additions = {}
        improved_bullets = []
        
        for bullet in bullets:
            improved, used_additions = improve_bullet(bullet, sample_code_project, used_additions)
            improved_bullets.append(improved)
        
        # Each bullet should be different
        assert len(set(improved_bullets)) == len(improved_bullets)
    
    def test_generate_all_improved_bullets(self, sample_code_project):
        """Test batch improvement of bullets"""
        bullets = [
            "Made a web application",
            "Created backend API",
            "Built database schema"
        ]
        
        improved = generate_all_improved_bullets(sample_code_project, bullets)
        
        assert len(improved) == 3
        # All should be different (unique additions)
        assert len(set(improved)) == 3


class TestBeforeAfterComparison:
    """Test suite for before/after comparison"""
    
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
            'skills': ['API Development', 'Database Design']
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
            'skills': ['Logo Design', 'Brand Strategy']
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
            'skills': ['Technical Writing', 'Documentation']
        }
        return db_manager.create_project(project_data)
    
    def test_generate_before_after_returns_tuple(self, sample_code_project):
        """Test that generate_before_after_comparison returns tuple"""
        bullet = "Made a web application"
        result = generate_before_after_comparison(sample_code_project, bullet)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        comparison, used_additions = result
        assert isinstance(comparison, dict)
        assert isinstance(used_additions, dict)
    
    def test_generate_before_after_structure(self, sample_code_project):
        """Test comparison structure"""
        bullet = "Made a web application"
        comparison, _ = generate_before_after_comparison(sample_code_project, bullet)
        
        assert 'before' in comparison
        assert 'after' in comparison
        assert 'improvements' in comparison
        assert 'improvement_percentage' in comparison
        
        assert 'bullet' in comparison['before']
        assert 'ats_score' in comparison['before']
        assert 'grade' in comparison['before']
        assert 'word_count' in comparison['before']
    
    def test_generate_before_after_improves_score(self, sample_code_project):
        """Test that after bullet has better or equal score"""
        bullet = "Made a web application"
        comparison, _ = generate_before_after_comparison(sample_code_project, bullet)
        
        assert comparison['after']['ats_score'] >= comparison['before']['ats_score']
    
    def test_generate_before_after_lists_improvements(self, sample_code_project):
        """Test that improvements are listed"""
        bullet = "Made a web application"
        comparison, _ = generate_before_after_comparison(sample_code_project, bullet)
        
        assert isinstance(comparison['improvements'], list)
        assert len(comparison['improvements']) >= 1
    
    def test_generate_before_after_tracks_additions(self, sample_code_project):
        """Test that used_additions is tracked across multiple calls"""
        bullets = ["Made app one", "Made app two"]
        
        used_additions = {}
        for bullet in bullets:
            _, used_additions = generate_before_after_comparison(
                sample_code_project, bullet, used_additions
            )
        
        # Should have tracked multiple additions
        assert len(used_additions) >= 1
    
    def test_generate_before_after_media(self, sample_media_project):
        """Test before/after for media project"""
        bullet = "Created graphics"
        comparison, _ = generate_before_after_comparison(sample_media_project, bullet)
        
        assert comparison['before']['bullet'] == bullet
        assert comparison['after']['bullet'] != bullet
    
    def test_generate_before_after_text(self, sample_text_project):
        """Test before/after for text project"""
        bullet = "Wrote articles"
        comparison, _ = generate_before_after_comparison(sample_text_project, bullet)
        
        assert 'improvement_percentage' in comparison


class TestRoleLevelTargeting:
    """Test suite for role-level targeting functions"""
    
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
            'skills': ['API Development', 'Database Design']
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
            'languages': ['Adobe Illustrator', 'Adobe Photoshop'],
            'skills': ['Logo Design', 'Brand Strategy']
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
            'skills': ['Technical Writing', 'Documentation']
        }
        return db_manager.create_project(project_data)
    
    def test_get_role_appropriate_verb_all_levels(self):
        """Test verb selection for all role levels"""
        levels = ['junior', 'mid', 'senior', 'lead']
        
        for level in levels:
            verb = get_role_appropriate_verb(level, 'code')
            assert isinstance(verb, str)
            assert len(verb) > 0
            assert verb in ROLE_SPECIFIC_VERBS[level]
    
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
    
    def test_improve_bullet_for_role_returns_tuple(self, sample_code_project):
        """Test that improve_bullet_for_role returns correct tuple"""
        bullet = "Made a web application"
        result = improve_bullet_for_role(bullet, sample_code_project, 'senior')
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        enhanced, used_verb, emphasis_idx = result
        assert isinstance(enhanced, str)
        assert used_verb in ROLE_SPECIFIC_VERBS['senior']
        assert isinstance(emphasis_idx, int)
    
    def test_improve_bullet_for_role_uses_correct_verb(self, sample_code_project):
        """Test that correct role-level verb is used"""
        bullet = "Made a web application"
        
        junior_result, _, _ = improve_bullet_for_role(bullet, sample_code_project, 'junior')
        senior_result, _, _ = improve_bullet_for_role(bullet, sample_code_project, 'senior')
        lead_result, _, _ = improve_bullet_for_role(bullet, sample_code_project, 'lead')
        
        assert junior_result.split()[0] in ROLE_SPECIFIC_VERBS['junior']
        assert senior_result.split()[0] in ROLE_SPECIFIC_VERBS['senior']
        assert lead_result.split()[0] in ROLE_SPECIFIC_VERBS['lead']
    
    def test_improve_bullet_for_role_adds_emphasis(self, sample_code_project):
        """Test that role-appropriate emphasis is added"""
        bullet = "Made a web application"
        enhanced, _, _ = improve_bullet_for_role(bullet, sample_code_project, 'senior')
        
        # Should have added some emphasis phrase
        assert len(enhanced) > len(bullet)
        assert ',' in enhanced  # Emphasis is added after comma
    
    def test_improve_bullet_for_role_avoids_verb_repetition(self, sample_code_project):
        """Test that verbs aren't repeated when tracking"""
        bullet = "Made a web application"
        used_verbs = ['Led']  # Pre-use the first senior verb
        
        enhanced, used_verb, _ = improve_bullet_for_role(
            bullet, sample_code_project, 'senior', used_verbs
        )
        
        # Should use a different verb
        assert used_verb != 'Led'
        assert used_verb in ROLE_SPECIFIC_VERBS['senior']
    
    def test_improve_bullet_for_role_avoids_emphasis_repetition(self, sample_code_project):
        """Test that emphasis phrases aren't repeated"""
        bullet = "Made a web application"
        used_emphasis_indices = [0]  # Pre-use the first emphasis
        
        _, _, emphasis_idx = improve_bullet_for_role(
            bullet, sample_code_project, 'senior', [], used_emphasis_indices
        )
        
        # Should use a different emphasis index
        assert emphasis_idx != 0
    
    def test_improve_all_bullets_for_role_unique_verbs(self, sample_code_project):
        """Test that batch role improvement uses unique verbs"""
        bullets = [
            "Made app one",
            "Made app two",
            "Made app three"
        ]
        
        improved = improve_all_bullets_for_role(bullets, sample_code_project, 'senior')
        
        # Extract first words (verbs)
        verbs = [b.split()[0] for b in improved]
        
        # All verbs should be different
        assert len(set(verbs)) == len(verbs)
    
    def test_improve_all_bullets_for_role_unique_emphasis(self, sample_code_project):
        """Test that batch role improvement uses unique emphasis phrases"""
        bullets = [
            "Made app one",
            "Made app two",
            "Made app three"
        ]
        
        improved = improve_all_bullets_for_role(bullets, sample_code_project, 'senior')
        
        # All bullets should be different
        assert len(set(improved)) == len(improved)
    
    def test_improve_all_bullets_for_role_handles_five_bullets(self, sample_code_project):
        """Test that 5 bullets get 5 unique extensions (max supported)"""
        bullets = [
            "Made app one",
            "Made app two",
            "Made app three",
            "Made app four",
            "Made app five"
        ]
        
        improved = improve_all_bullets_for_role(bullets, sample_code_project, 'lead')
        
        assert len(improved) == 5
        # All should be unique
        assert len(set(improved)) == 5
    
    def test_improve_all_bullets_for_role_media_project(self, sample_media_project):
        """Test role improvement for media project"""
        bullets = [
            "Created graphics",
            "Made designs",
            "Produced artwork"
        ]
        
        improved = improve_all_bullets_for_role(bullets, sample_media_project, 'mid')
        
        assert len(improved) == 3
        # Should use media-specific emphasis
        for bullet in improved:
            assert any(word in bullet.lower() for word in ['creative', 'design', 'brand', 'deliverables', 'quality'])
    
    def test_improve_all_bullets_for_role_text_project(self, sample_text_project):
        """Test role improvement for text project"""
        bullets = [
            "Wrote articles",
            "Created content",
            "Drafted documents"
        ]
        
        improved = improve_all_bullets_for_role(bullets, sample_text_project, 'mid')
        
        assert len(improved) == 3
        # Should use text-specific emphasis
        for bullet in improved:
            assert any(word in bullet.lower() for word in ['writing', 'content', 'editorial', 'clarity', 'publication'])
    
    def test_role_emphasis_has_five_options_per_level(self):
        """Test that each role level has 5 emphasis options"""
        for role_level in ['junior', 'mid', 'senior', 'lead']:
            for project_type in ['code', 'visual_media', 'text']:
                options = ROLE_EMPHASIS[role_level][project_type]
                assert len(options) == 5, f"{role_level}/{project_type} should have 5 options"


class TestSuccessEvidence:
    """Test suite for success evidence utilities"""
    
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
    
    def test_has_success_metrics_false(self, sample_project):
        """Test has_success_metrics when no metrics exist"""
        assert has_success_metrics(sample_project) is False
    
    def test_has_success_metrics_true(self, sample_project):
        """Test has_success_metrics when metrics exist"""
        populate_success_evidence(sample_project, {'users': 100})
        project = db_manager.get_project(sample_project.id)
        
        assert has_success_metrics(project) is True


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


class TestIntegration:
    """Integration tests for all functions working together"""
    
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
            'skills': ['API Development', 'Database Design']
        }
        return db_manager.create_project(project_data)
    
    def test_full_improvement_workflow(self, sample_code_project):
        """Test complete bullet improvement workflow"""
        # Start with weak bullets
        original_bullets = [
            "Made a web app",
            "Created backend",
            "Built frontend"
        ]
        
        # Score original bullets
        original_scoring = score_all_bullets(original_bullets, 'code')
        
        # Improve with before/after
        improved_bullets = generate_all_improved_bullets(sample_code_project, original_bullets)
        
        # Score improved bullets
        improved_scoring = score_all_bullets(improved_bullets, 'code')
        
        # Improved should have better or equal score
        assert improved_scoring['overall_score'] >= original_scoring['overall_score']
    
    def test_role_level_workflow(self, sample_code_project):
        """Test role-level enhancement workflow"""
        original_bullets = [
            "Made a web app",
            "Created backend",
            "Built frontend"
        ]
        
        # Enhance for different role levels
        junior_bullets = improve_all_bullets_for_role(original_bullets, sample_code_project, 'junior')
        senior_bullets = improve_all_bullets_for_role(original_bullets, sample_code_project, 'senior')
        lead_bullets = improve_all_bullets_for_role(original_bullets, sample_code_project, 'lead')
        
        # All should be different from original
        assert junior_bullets != original_bullets
        assert senior_bullets != original_bullets
        assert lead_bullets != original_bullets
        
        # All role levels should produce different results
        assert junior_bullets != senior_bullets
        assert senior_bullets != lead_bullets
    
    def test_all_functions_work_together(self, sample_code_project):
        """Test that all shared functions work together"""
        # Create bullet
        bullet = "Developed REST API using Python and Django"
        
        # ATS scoring
        ats = calculate_ats_score(bullet, 'code')
        assert ats['score'] >= 0
        
        # Before/after
        comparison, _ = generate_before_after_comparison(sample_code_project, bullet)
        assert comparison['after']['ats_score'] >= 0
        
        # Role context
        context = generate_role_context(sample_code_project, 'mid')
        assert context['focus'] is not None
        
        # Role improvement
        enhanced, _, _ = improve_bullet_for_role(bullet, sample_code_project, 'senior')
        assert len(enhanced) > 0
        
        # Success evidence
        populate_success_evidence(sample_code_project, {'users': 100})
        project = db_manager.get_project(sample_code_project.id)
        assert has_success_metrics(project) is True
        
        # Utility functions
        metrics = extract_metrics_from_bullet("Improved by 40%")
        assert len(metrics) > 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])