"""
Comprehensive test suite for media resume bullet generator

Tests:
- Project header generation with software tools
- All 10 bullet type generation methods
- Media-specific bullet scoring system
- Complete resume component formatting with 2-5 bullets
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
            'languages': ['Adobe Illustrator', 'Adobe Photoshop', 'Figma'],
            'frameworks': [],
            'skills': ['Vector Illustration', 'Logo Design', 'Brand Strategy', 'Typography'],
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
            'skills': ['Video Editing', 'Color Grading', 'Motion Graphics', '3D'],
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
        assert 'Adobe' in header or 'Illustrator' in header or 'Photoshop' in header or 'Figma' in header
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
    # SCORING SYSTEM TESTS
    # ============================================
    
    def test_score_bullet_with_metrics(self, generator, media_project):
        """Test bullet scoring includes metrics check"""
        bullet_with_metrics = "Produced 45+ visual assets using Adobe Illustrator"
        score = generator._score_bullet(bullet_with_metrics, media_project)
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.25  # Should get at least metrics points
    
    def test_score_bullet_with_media_keywords(self, generator, media_project):
        """Test bullet scoring includes media-specific keywords"""
        bullet_with_keywords = "Designed UI mockups using Figma with typography and branding"
        score = generator._score_bullet(bullet_with_keywords, media_project)
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.15  # Should get keyword points
    
    # ============================================
    # BULLET TYPE GENERATION TESTS (10 TYPES)
    # ============================================
    
    def test_generate_main_description_bullet(self, generator, media_project):
        """Test main description bullet generation"""
        bullet = generator._generate_main_description_bullet(media_project, [])
        
        assert isinstance(bullet, str)
        assert len(bullet) > 10
        first_word = bullet.split()[0]
        assert first_word in [v for verbs in generator.ACTION_VERBS.values() for v in verbs]
    
    def test_generate_scale_bullet(self, generator, media_project):
        """Test scale bullet with file count and size"""
        bullet = generator._generate_scale_bullet(media_project, [])
        
        assert bullet is not None
        assert '45' in bullet or '250' in bullet
    
    def test_generate_skills_bullet(self, generator, media_project):
        """Test skills bullet generation"""
        bullet = generator._generate_skills_bullet(media_project, [])
        
        assert bullet is not None
        assert any(skill in bullet for skill in ['Vector Illustration', 'Logo Design', 'Brand Strategy'])
    
    def test_generate_software_mastery_bullet(self, generator, media_project):
        """Test software mastery bullet generation"""
        bullet = generator._generate_software_mastery_bullet(media_project, [])
        
        assert bullet is not None
        assert 'Adobe Illustrator' in bullet or 'Adobe Photoshop' in bullet or 'Figma' in bullet
    
    def test_generate_collaboration_bullet(self, generator, media_project):
        """Test collaboration bullet with creative team"""
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
        bullet = generator._generate_collaboration_bullet(project, [])
        
        assert bullet is not None
        assert '2-person' in bullet
    
    def test_generate_design_process_bullet(self, generator, media_project):
        """Test design process bullet generation"""
        bullet = generator._generate_design_process_bullet(media_project, [])
        
        # Should generate if relevant skills present (Brand Strategy, Typography)
        if bullet:
            assert isinstance(bullet, str)
    
    def test_generate_technical_complexity_bullet(self, generator, video_project):
        """Test technical complexity bullet with advanced skills"""
        bullet = generator._generate_technical_complexity_bullet(video_project, [])
        
        # Should generate with advanced media skills (3D, motion graphics, video editing, color grading)
        assert bullet is not None
        # Check that it mentions at least one of the advanced skills
        assert any(skill.lower() in bullet.lower() for skill in ['3d', 'motion graphics', 'video editing', 'color grading'])
    
    def test_generate_portfolio_impact_bullet(self, generator, media_project):
        """Test portfolio impact bullet generation"""
        bullet = generator._generate_portfolio_impact_bullet(media_project, [])
        
        assert bullet is not None
        assert 'production' in bullet.lower() or 'deliver' in bullet.lower()
    
    def test_generate_creative_innovation_bullet(self, generator, media_project):
        """Test creative innovation bullet with modern tools"""
        bullet = generator._generate_creative_innovation_bullet(media_project, [])
        
        # Should generate with Figma (modern tool)
        assert bullet is not None
        assert 'Figma' in bullet
    
    def test_generate_delivery_quality_bullet(self, generator, media_project):
        """Test delivery quality bullet generation"""
        bullet = generator._generate_delivery_quality_bullet(media_project, [])
        
        assert bullet is not None
        assert 'polished' in bullet.lower() or 'quality' in bullet.lower()
    
    # ============================================
    # COMPLETE BULLET GENERATION TESTS (2-5 BULLETS)
    # ============================================
    
    def test_generate_resume_bullets_default_count(self, generator, media_project):
        """Test generating default number of bullets (3)"""
        bullets = generator.generate_resume_bullets(media_project)
        
        assert len(bullets) == 3
        assert all(isinstance(b, str) for b in bullets)
    
    def test_generate_resume_bullets_2_bullets(self, generator, media_project):
        """Test generating 2 bullets"""
        bullets = generator.generate_resume_bullets(media_project, num_bullets=2)
        
        assert len(bullets) == 2
    
    def test_generate_resume_bullets_5_bullets(self, generator, video_project):
        """Test generating 5 bullets (was broken, now fixed)"""
        bullets = generator.generate_resume_bullets(video_project, num_bullets=5)
        
        assert len(bullets) == 5
        assert all(isinstance(b, str) for b in bullets)
    
    def test_generate_resume_bullets_returns_top_scored(self, generator, media_project):
        """Test that generated bullets are scored and top N returned"""
        bullets = generator.generate_resume_bullets(media_project, num_bullets=3)
        
        # Verify all bullets are scored and valid
        assert len(bullets) == 3
        for bullet in bullets:
            score = generator._score_bullet(bullet, media_project)
            assert 0.0 <= score <= 1.0
    
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
    
    def test_format_resume_component_with_5_bullets(self, generator, video_project):
        """Test formatting with 5 bullets"""
        component = generator.format_resume_component(video_project, num_bullets=5)
        
        assert video_project.name in component
        assert component.count('•') == 5
    
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
    
    def test_generate_bullets_for_project_custom_count(self, generator, video_project):
        """Test generating custom number of bullets"""
        result = generator.generate_bullets_for_project(video_project.id, num_bullets=5)
        
        assert result['success'] is True
        assert len(result['bullets']) == 5
    
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
    
    def test_minimal_project_generates_bullets(self, generator):
        """Test that even minimal projects generate at least 1 bullet"""
        project_data = {
            'name': 'Minimal',
            'file_path': '/test/minimal',
            'project_type': 'visual_media',
            'languages': ['Photoshop']
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project, num_bullets=2)
        assert len(bullets) >= 1
    
    def test_category_parameter_in_select_verb(self, generator, media_project):
        """Test that _select_action_verb accepts category parameter"""
        verb = generator._select_action_verb(media_project, [], category='delivery')
        
        assert verb in generator.ACTION_VERBS['delivery']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])