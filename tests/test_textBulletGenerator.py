"""
Comprehensive test suite for text resume bullet generator

Tests:
- Project header generation with document types
- Main description bullet generation
- Scale/scope bullet generation
- Skills bullet generation
- Complete resume component formatting
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
            'skills': ['Technical Writing', 'Documentation', 'Research Writing'],
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
            'skills': ['Research Writing', 'Critical Thinking', 'Data Analysis'],
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
    # MAIN DESCRIPTION BULLET TESTS
    # ============================================
    
    def test_generate_main_description_with_description(self, generator, text_project):
        """Test main bullet generation with description"""
        bullet = generator._generate_main_description_bullet(text_project)
        
        assert isinstance(bullet, str)
        assert len(bullet) > 10
        first_word = bullet.split()[0]
        assert first_word in generator.ACTION_VERBS['writing'] or first_word in generator.ACTION_VERBS['research']
    
    def test_generate_main_description_with_skills(self, generator, text_project):
        """Test main bullet includes skills"""
        bullet = generator._generate_main_description_bullet(text_project)
        
        assert 'technical writing' in bullet.lower() or 'documentation' in bullet.lower()
    
    def test_generate_main_description_with_tags(self, generator, text_project):
        """Test main bullet uses document types from tags"""
        bullet = generator._generate_main_description_bullet(text_project)
        
        # Should mention documentation or content
        assert 'documentation' in bullet.lower() or 'content' in bullet.lower() or 'markdown' in bullet.lower()
    
    # ============================================
    # SCALE BULLET TESTS
    # ============================================
    
    def test_generate_scale_bullet_with_word_count(self, generator, text_project):
        """Test scale bullet with word count"""
        bullet = generator._generate_scale_bullet(text_project, [])
        
        assert bullet is not None
        assert '25' in bullet or 'word' in bullet.lower()
    
    def test_generate_scale_bullet_with_large_word_count(self, generator, research_project):
        """Test scale bullet with large word count (shows in K)"""
        bullet = generator._generate_scale_bullet(research_project, [])
        
        assert bullet is not None
        assert '50K' in bullet or '50,000' in bullet
    
    def test_generate_scale_bullet_with_document_count(self, generator, text_project):
        """Test scale bullet with document count"""
        bullet = generator._generate_scale_bullet(text_project, [])
        
        assert bullet is not None
        assert '15' in bullet or 'document' in bullet.lower()
    
    def test_generate_scale_bullet_with_team(self, generator, text_project):
        """Test scale bullet with writing team"""
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
        bullet = generator._generate_scale_bullet(project, [])
        
        assert bullet is not None
        # Should mention either team size OR word/document metrics (limited to 2 metrics)
        assert ('2-person writing team' in bullet or 
                ('25K' in bullet or '25,000' in bullet) or 
                ('15' in bullet and 'document' in bullet.lower()))
    
    def test_generate_scale_bullet_returns_none_for_small_project(self, generator):
        """Test scale bullet returns None for small projects"""
        project_data = {
            'name': 'Tiny Doc',
            'file_path': '/test/tiny',
            'project_type': 'text',
            'word_count': 500,
            'file_count': 2
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_scale_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # SKILLS BULLET TESTS
    # ============================================
    
    def test_generate_skills_bullet_with_multiple_skills(self, generator, text_project):
        """Test skills bullet generation"""
        bullet = generator._generate_skills_bullet(text_project, [])
        
        assert bullet is not None
        # Skills should be lowercased in the bullet
        combined_text = ' '.join(text_project.skills).lower()
        assert any(skill.lower() in bullet.lower() for skill in text_project.skills[:4])
    
    def test_generate_skills_bullet_returns_none_with_few_skills(self, generator):
        """Test skills bullet returns None with insufficient skills"""
        project_data = {
            'name': 'No Skills',
            'file_path': '/test/noskills',
            'project_type': 'text',
            'skills': []
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_skills_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # COMPLETE BULLET GENERATION TESTS
    # ============================================
    
    def test_generate_resume_bullets_default_count(self, generator, text_project):
        """Test generating default number of bullets"""
        bullets = generator.generate_resume_bullets(text_project)
        
        assert len(bullets) >= 1
        assert all(isinstance(b, str) for b in bullets)
    
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


if __name__ == "__main__":
    pytest.main([__file__, '-v'])