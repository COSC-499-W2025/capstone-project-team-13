"""
Comprehensive test suite for media resume bullet generator

Tests:
- Project header generation with software tools
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

from src.Resume.mediaBulletGenerator import MediaBulletGenerator
from src.Databases.database import db_manager, Project


class TestMediaBulletGenerator:
    """Test suite for MediaBulletGenerator class"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def generator(self):
        """Create a MediaBulletGenerator instance"""
        return MediaBulletGenerator()
    
    @pytest.fixture
    def media_project(self):
        """Create a visual media project for testing"""
        project_data = {
            'name': 'Brand Identity Design',
            'file_path': '/test/brand_identity',
            'description': 'Complete brand identity package with logos and marketing materials',
            'project_type': 'visual_media',
            'file_count': 45,
            'total_size_bytes': 250 * 1024 * 1024,  # 250 MB
            'date_created': datetime.now(timezone.utc),
            'date_modified': datetime.now(timezone.utc),
            'languages': ['Adobe Illustrator', 'Adobe Photoshop'],  # Software in languages field
            'frameworks': [],
            'skills': ['Vector Illustration', 'Logo Design', 'Brand Strategy'],
            'tags': ['Design', 'Branding']
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def video_project(self):
        """Create a video editing project for testing"""
        project_data = {
            'name': 'Documentary Film Editing',
            'file_path': '/test/documentary',
            'description': 'Feature-length documentary post-production',
            'project_type': 'visual_media',
            'file_count': 150,
            'total_size_bytes': 5 * 1024 * 1024 * 1024,  # 5 GB
            'date_created': datetime.now(timezone.utc),
            'date_modified': datetime.now(timezone.utc),
            'languages': ['Adobe Premiere Pro', 'DaVinci Resolve'],
            'frameworks': [],
            'skills': ['Video Editing', 'Color Grading', 'Motion Graphics'],
            'tags': ['Video', 'Post-Production']
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # PROJECT HEADER TESTS
    # ============================================
    
    def test_generate_project_header_with_software(self, generator, media_project):
        """Test header generation with software tools"""
        header = generator.generate_project_header(media_project)
        
        assert media_project.name in header
        assert 'Adobe' in header or 'Illustrator' in header or 'Photoshop' in header
        assert '|' in header
    
    def test_generate_project_header_without_software(self, generator):
        """Test header generation without software"""
        project_data = {
            'name': 'Generic Media',
            'file_path': '/test/generic',
            'project_type': 'visual_media',
            'languages': []
        }
        project = db_manager.create_project(project_data)
        header = generator.generate_project_header(project)
        
        assert project.name in header
        assert 'Digital Media' in header
        assert '|' in header
    
    # ============================================
    # MAIN DESCRIPTION BULLET TESTS
    # ============================================
    
    def test_generate_main_description_with_software(self, generator, media_project):
        """Test main bullet generation with software"""
        bullet = generator._generate_main_description_bullet(media_project)
        
        assert isinstance(bullet, str)
        assert len(bullet) > 10
        first_word = bullet.split()[0]
        assert first_word in generator.ACTION_VERBS['creative'] or first_word in generator.ACTION_VERBS['design']
    
    def test_generate_main_description_with_skills(self, generator, media_project):
        """Test main bullet includes skills"""
        bullet = generator._generate_main_description_bullet(media_project)
        
        assert 'Vector Illustration' in bullet or 'Logo Design' in bullet or 'expertise' in bullet.lower()
    
    # ============================================
    # SCALE BULLET TESTS
    # ============================================
    
    def test_generate_scale_bullet_with_file_count(self, generator, media_project):
        """Test scale bullet with file count"""
        bullet = generator._generate_scale_bullet(media_project, [])
        
        assert bullet is not None
        assert '45' in bullet or 'assets' in bullet.lower()
    
    def test_generate_scale_bullet_with_size_mb(self, generator, media_project):
        """Test scale bullet with MB size"""
        bullet = generator._generate_scale_bullet(media_project, [])
        
        assert bullet is not None
        assert '250' in bullet or 'MB' in bullet
    
    def test_generate_scale_bullet_with_size_gb(self, generator, video_project):
        """Test scale bullet with GB size"""
        bullet = generator._generate_scale_bullet(video_project, [])
        
        assert bullet is not None
        assert '5' in bullet and 'GB' in bullet
    
    def test_generate_scale_bullet_with_team(self, generator, media_project):
        """Test scale bullet with creative team"""
        db_manager.add_contributor_to_project({
            'project_id': media_project.id,
            'name': 'Designer 1',
            'commit_count': 30
        })
        db_manager.add_contributor_to_project({
            'project_id': media_project.id,
            'name': 'Designer 2',
            'commit_count': 20
        })
        
        project = db_manager.get_project(media_project.id)
        bullet = generator._generate_scale_bullet(project, [])
        
        assert bullet is not None
        assert '2-person creative team' in bullet
    
    def test_generate_scale_bullet_returns_none_for_small_project(self, generator):
        """Test scale bullet returns None for small projects"""
        project_data = {
            'name': 'Tiny Media',
            'file_path': '/test/tiny',
            'project_type': 'visual_media',
            'file_count': 3,
            'total_size_bytes': 10 * 1024 * 1024  # 10 MB
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_scale_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # SKILLS BULLET TESTS
    # ============================================
    
    def test_generate_skills_bullet_with_multiple_skills(self, generator, media_project):
        """Test skills bullet generation"""
        bullet = generator._generate_skills_bullet(media_project, [])
        
        assert bullet is not None
        assert any(skill in bullet for skill in ['Vector Illustration', 'Logo Design', 'Brand Strategy'])
    
    def test_generate_skills_bullet_returns_none_with_few_skills(self, generator):
        """Test skills bullet returns None with insufficient skills"""
        project_data = {
            'name': 'No Skills',
            'file_path': '/test/noskills',
            'project_type': 'visual_media',
            'skills': []
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_skills_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # COMPLETE BULLET GENERATION TESTS
    # ============================================
    
    def test_generate_resume_bullets_default_count(self, generator, media_project):
        """Test generating default number of bullets"""
        bullets = generator.generate_resume_bullets(media_project)
        
        assert len(bullets) >= 1
        assert all(isinstance(b, str) for b in bullets)
    
    def test_generate_resume_bullets_avoids_duplicate_verbs(self, generator, video_project):
        """Test that bullets avoid repeating verbs"""
        bullets = generator.generate_resume_bullets(video_project, num_bullets=3)
        
        verbs = [bullet.split()[0] for bullet in bullets]
        assert len(set(verbs)) >= 2
    
    # ============================================
    # FORMAT RESUME COMPONENT TESTS
    # ============================================
    
    def test_format_resume_component_structure(self, generator, media_project):
        """Test complete resume component formatting"""
        component = generator.format_resume_component(media_project)
        
        assert media_project.name in component
        assert '|' in component
        assert '•' in component
        assert '\n' in component
    
    # ============================================
    # GENERATE_BULLETS_FOR_PROJECT TESTS
    # ============================================
    
    def test_generate_bullets_for_project_success(self, generator, media_project):
        """Test generating bullets for valid media project"""
        result = generator.generate_bullets_for_project(media_project.id)
        
        assert result['success'] is True
        assert result['project_id'] == media_project.id
        assert result['project_type'] == 'visual_media'
        assert 'header' in result
        assert 'bullets' in result
    
    def test_generate_bullets_for_project_invalid_id(self, generator):
        """Test handling of invalid project ID"""
        result = generator.generate_bullets_for_project(99999)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_generate_bullets_for_project_wrong_type(self, generator):
        """Test handling of non-media project"""
        project_data = {
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        result = generator.generate_bullets_for_project(project.id)
        
        assert result['success'] is False
        assert 'not a media project' in result['error']
    
    # ============================================
    # EDGE CASE TESTS
    # ============================================
    
    def test_handles_empty_skills(self, generator):
        """Test handling of empty skills list"""
        project_data = {
            'name': 'Empty Skills',
            'file_path': '/test/empty',
            'project_type': 'visual_media',
            'languages': ['Adobe Photoshop'],
            'skills': []
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project)
        assert len(bullets) >= 1


if __name__ == "__main__":
    pytest.main([__file__, '-v'])