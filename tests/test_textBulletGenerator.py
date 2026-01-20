"""
Comprehensive test suite for text resume bullet generator

Tests:
- Project header generation with document types
- All 10 bullet type generation methods
- Writing-specific bullet scoring system
- Complete resume component formatting with 2-5 bullets
- Edge cases and error handling
"""

import os
import sys
import pytest
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.textBulletGenerator import TextBulletGenerator
from src.Databases.database import db_manager, Project


class TestTextBulletGenerator:
    """Test suite for TextBulletGenerator class"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def generator(self):
        """Create a TextBulletGenerator instance"""
        return TextBulletGenerator()
    
    @pytest.fixture
    def text_project(self):
        """Create a text/document project for testing"""
        project_data = {
            'name': 'Technical Documentation Suite',
            'file_path': '/test/documentation',
            'description': 'Comprehensive technical documentation for software platform',
            'project_type': 'text',
            'word_count': 25000,
            'file_count': 15,
            'total_size_bytes': 5 * 1024 * 1024,  # 5 MB
            'date_created': datetime.now(timezone.utc),
            'date_modified': datetime.now(timezone.utc),
            'languages': [],
            'frameworks': [],
            'skills': ['Technical Writing', 'Documentation', 'Research Writing', 'SEO'],
            'tags': ['Markdown', 'PDF']
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def research_project(self):
        """Create a research writing project for testing"""
        project_data = {
            'name': 'Academic Research Papers',
            'file_path': '/test/research',
            'description': 'Collection of peer-reviewed research papers',
            'project_type': 'text',
            'word_count': 50000,
            'file_count': 8,
            'total_size_bytes': 3 * 1024 * 1024,
            'date_created': datetime.now(timezone.utc),
            'date_modified': datetime.now(timezone.utc),
            'languages': [],
            'frameworks': [],
            'skills': ['Research Writing', 'Critical Thinking', 'Data Analysis', 'Academic Writing'],
            'tags': ['LaTeX', 'PDF']
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # PROJECT HEADER TESTS
    # ============================================
    
    def test_generate_project_header_with_tags(self, generator, text_project):
        """Test header generation with document types"""
        header = generator.generate_project_header(text_project)
        
        assert text_project.name in header
        assert 'Markdown' in header or 'PDF' in header
        assert '|' in header
    
    def test_generate_project_header_without_tags(self, generator):
        """Test header generation without tags"""
        project_data = {
            'name': 'Generic Writing',
            'file_path': '/test/generic',
            'project_type': 'text',
            'tags': []
        }
        project = db_manager.create_project(project_data)
        header = generator.generate_project_header(project)
        
        assert project.name in header
        assert 'Writing' in header
        assert '|' in header
    
    # ============================================
    # SCORING SYSTEM TESTS
    # ============================================
    
    def test_score_bullet_with_metrics(self, generator, text_project):
        """Test bullet scoring includes metrics check"""
        bullet_with_metrics = "Authored 25,000+ words of technical documentation"
        score = generator._score_bullet(bullet_with_metrics, text_project)
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.25  # Should get at least metrics points
    
    def test_score_bullet_with_writing_keywords(self, generator, text_project):
        """Test bullet scoring includes writing-specific keywords"""
        bullet_with_keywords = "Composed technical writing with SEO and copywriting expertise"
        score = generator._score_bullet(bullet_with_keywords, text_project)
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.15  # Should get keyword points
    
    # ============================================
    # BULLET TYPE GENERATION TESTS (10 TYPES)
    # ============================================
    
    def test_generate_main_description_bullet(self, generator, text_project):
        """Test main description bullet generation"""
        bullet = generator._generate_main_description_bullet(text_project, [])
        
        assert isinstance(bullet, str)
        assert len(bullet) > 10
        first_word = bullet.split()[0]
        assert first_word in [v for verbs in generator.ACTION_VERBS.values() for v in verbs]
    
    def test_generate_scale_bullet(self, generator, text_project):
        """Test scale bullet with word count"""
        bullet = generator._generate_scale_bullet(text_project, [])
        
        assert bullet is not None
        assert '25' in bullet or '15' in bullet
    
    def test_generate_skills_bullet(self, generator, text_project):
        """Test skills bullet generation"""
        bullet = generator._generate_skills_bullet(text_project, [])
        
        assert bullet is not None
        assert any(skill.lower() in bullet.lower() for skill in text_project.skills[:4])
    
    def test_generate_research_depth_bullet(self, generator, research_project):
        """Test research depth bullet generation"""
        bullet = generator._generate_research_depth_bullet(research_project, [])
        
        # Should generate with research skills
        assert bullet is not None
        assert 'research' in bullet.lower() or 'analysis' in bullet.lower()
    
    def test_generate_collaboration_bullet(self, generator, text_project):
        """Test collaboration bullet with writing team"""
        db_manager.add_contributor_to_project({
            'project_id': text_project.id,
            'name': 'Writer 1',
            'commit_count': 20
        })
        db_manager.add_contributor_to_project({
            'project_id': text_project.id,
            'name': 'Writer 2',
            'commit_count': 15
        })
        
        project = db_manager.get_project(text_project.id)
        bullet = generator._generate_collaboration_bullet(project, [])
        
        assert bullet is not None
        assert '2-person' in bullet
    
    def test_generate_audience_focus_bullet(self, generator, text_project):
        """Test audience focus bullet generation"""
        bullet = generator._generate_audience_focus_bullet(text_project, [])
        
        # Should generate with SEO skill or audience-related content
        assert bullet is not None
        # Check for audience-related terms (stakeholders, audiences, readers, etc.)
        assert any(term in bullet.lower() for term in ['audience', 'seo', 'stakeholder', 'reader', 'web'])
    
    def test_generate_editing_quality_bullet(self, generator):
        """Test editing quality bullet generation"""
        project_data = {
            'name': 'Editing Project',
            'file_path': '/test/editing',
            'project_type': 'text',
            'skills': ['Editing', 'Proofreading', 'Grammar', 'AP Style']
        }
        project = db_manager.create_project(project_data)
        
        bullet = generator._generate_editing_quality_bullet(project, [])
        
        assert bullet is not None
        assert 'edit' in bullet.lower() or 'style' in bullet.lower()
    
    def test_generate_content_strategy_bullet(self, generator, text_project):
        """Test content strategy bullet generation"""
        bullet = generator._generate_content_strategy_bullet(text_project, [])
        
        # Should generate with SEO skill
        assert bullet is not None
        assert 'seo' in bullet.lower() or 'strategy' in bullet.lower()
    
    def test_generate_technical_documentation_bullet(self, generator, text_project):
        """Test technical documentation bullet generation"""
        bullet = generator._generate_technical_documentation_bullet(text_project, [])
        
        # Should generate with Technical Writing skill
        assert bullet is not None
        assert 'technical' in bullet.lower() or 'documentation' in bullet.lower()
    
    def test_generate_publication_impact_bullet(self, generator, text_project):
        """Test publication impact bullet generation"""
        bullet = generator._generate_publication_impact_bullet(text_project, [])
        
        assert bullet is not None
        assert 'deliver' in bullet.lower() or 'materials' in bullet.lower()
    
    # ============================================
    # COMPLETE BULLET GENERATION TESTS (2-5 BULLETS)
    # ============================================
    
    def test_generate_resume_bullets_default_count(self, generator, text_project):
        """Test generating default number of bullets (3)"""
        bullets = generator.generate_resume_bullets(text_project)
        
        assert len(bullets) == 3
        assert all(isinstance(b, str) for b in bullets)
    
    def test_generate_resume_bullets_2_bullets(self, generator, text_project):
        """Test generating 2 bullets"""
        bullets = generator.generate_resume_bullets(text_project, num_bullets=2)
        
        assert len(bullets) == 2
    
    def test_generate_resume_bullets_5_bullets(self, generator, research_project):
        """Test generating 5 bullets (was broken, now fixed)"""
        bullets = generator.generate_resume_bullets(research_project, num_bullets=5)
        
        assert len(bullets) == 5
        assert all(isinstance(b, str) for b in bullets)
    
    def test_generate_resume_bullets_returns_top_scored(self, generator, text_project):
        """Test that generated bullets are scored and top N returned"""
        bullets = generator.generate_resume_bullets(text_project, num_bullets=3)
        
        # Verify all bullets are scored and valid
        assert len(bullets) == 3
        for bullet in bullets:
            score = generator._score_bullet(bullet, text_project)
            assert 0.0 <= score <= 1.0
    
    def test_generate_resume_bullets_avoids_duplicate_verbs(self, generator, research_project):
        """Test that bullets avoid repeating verbs"""
        bullets = generator.generate_resume_bullets(research_project, num_bullets=3)
        
        verbs = [bullet.split()[0] for bullet in bullets]
        assert len(set(verbs)) >= 2
    
    # ============================================
    # FORMAT RESUME COMPONENT TESTS
    # ============================================
    
    def test_format_resume_component_structure(self, generator, text_project):
        """Test complete resume component formatting"""
        component = generator.format_resume_component(text_project)
        
        assert text_project.name in component
        assert '|' in component
        assert '•' in component
        assert '\n' in component
    
    def test_format_resume_component_with_5_bullets(self, generator, research_project):
        """Test formatting with 5 bullets"""
        component = generator.format_resume_component(research_project, num_bullets=5)
        
        assert research_project.name in component
        assert component.count('•') == 5
    
    # ============================================
    # GENERATE_BULLETS_FOR_PROJECT TESTS
    # ============================================
    
    def test_generate_bullets_for_project_success(self, generator, text_project):
        """Test generating bullets for valid text project"""
        result = generator.generate_bullets_for_project(text_project.id)
        
        assert result['success'] is True
        assert result['project_id'] == text_project.id
        assert result['project_type'] == 'text'
        assert 'header' in result
        assert 'bullets' in result
    
    def test_generate_bullets_for_project_custom_count(self, generator, research_project):
        """Test generating custom number of bullets"""
        result = generator.generate_bullets_for_project(research_project.id, num_bullets=5)
        
        assert result['success'] is True
        assert len(result['bullets']) == 5
    
    def test_generate_bullets_for_project_invalid_id(self, generator):
        """Test handling of invalid project ID"""
        result = generator.generate_bullets_for_project(99999)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_generate_bullets_for_project_wrong_type(self, generator):
        """Test handling of non-text project"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        result = generator.generate_bullets_for_project(project.id)
        
        assert result['success'] is False
        assert 'not a text project' in result['error']
    
    # ============================================
    # EDGE CASE TESTS
    # ============================================
    
    def test_handles_empty_skills(self, generator):
        """Test handling of empty skills list"""
        project_data = {
            'name': 'Empty Skills',
            'file_path': '/test/empty',
            'project_type': 'text',
            'tags': ['Markdown'],
            'skills': []
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project)
        assert len(bullets) >= 1
    
    def test_generates_generic_bullet_when_needed(self, generator):
        """Test that generic bullet is generated when data is sparse"""
        project_data = {
            'name': 'Minimal Text',
            'file_path': '/test/minimal',
            'project_type': 'text',
            'word_count': 500,
            'tags': []
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project, num_bullets=3)
        # Should have at least the main bullet
        assert len(bullets) >= 1
    
    def test_minimal_project_generates_bullets(self, generator):
        """Test that even minimal projects generate at least 1 bullet"""
        project_data = {
            'name': 'Minimal',
            'file_path': '/test/minimal',
            'project_type': 'text',
            'tags': ['Writing']
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project, num_bullets=2)
        assert len(bullets) >= 1
    
    def test_category_parameter_in_select_verb(self, generator, text_project):
        """Test that _select_action_verb accepts category parameter"""
        verb = generator._select_action_verb(text_project, [], category='research')
        
        assert verb in generator.ACTION_VERBS['research']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])