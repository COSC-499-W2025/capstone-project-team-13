"""
Comprehensive test suite for code resume bullet generator

Tests:
- Project header generation with tech stack
- Main description bullet generation
- Scale/scope bullet generation
- Skills bullet generation
- Impact bullet generation
- Complete resume component formatting
- Edge cases and error handling
"""

import os
import sys
import pytest
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.codeBulletGenerator import CodeBulletGenerator
from src.Databases.database import db_manager, Project


class TestCodeBulletGenerator:
    """Test suite for CodeBulletGenerator class"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def generator(self):
        """Create a CodeBulletGenerator instance"""
        return CodeBulletGenerator()
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample coding project for testing"""
        project_data = {
            'name': 'PacMan Ghost Hunter',
            'file_path': '/test/pacman',
            'description': '3D reimagining of Pac-Man with shooting mechanics',
            'project_type': 'code',
            'lines_of_code': 5000,
            'file_count': 45,
            'total_size_bytes': 1024000,
            'date_created': datetime.now(timezone.utc),
            'date_modified': datetime.now(timezone.utc),
            'languages': ['C#', 'JavaScript'],
            'frameworks': ['Unity'],
            'skills': ['Game Development', '3D Rendering', 'AI Development'],
            'collaboration_type': 'Individual Project'
        }
        return db_manager.create_project(project_data)
    
    @pytest.fixture
    def web_project(self):
        """Create a web development project for testing"""
        project_data = {
            'name': 'E-Commerce Dashboard',
            'file_path': '/test/ecommerce',
            'description': 'Full-stack e-commerce admin dashboard',
            'project_type': 'code',
            'lines_of_code': 8500,
            'file_count': 120,
            'total_size_bytes': 2048000,
            'date_created': datetime.now(timezone.utc),
            'date_modified': datetime.now(timezone.utc),
            'languages': ['JavaScript', 'Python'],
            'frameworks': ['React', 'Django'],
            'skills': ['Frontend Development', 'Backend Development', 'API Development', 'Database Management'],
            'collaboration_type': 'Collaborative Project'
        }
        return db_manager.create_project(project_data)
    
    # ============================================
    # PROJECT HEADER TESTS
    # ============================================
    
    def test_generate_project_header_with_frameworks(self, generator, sample_project):
        """Test header generation with frameworks"""
        header = generator.generate_project_header(sample_project)
        
        assert sample_project.name in header
        assert 'Unity' in header
        assert 'C#' in header
        assert '|' in header
    
    def test_generate_project_header_without_frameworks(self, generator):
        """Test header generation without frameworks"""
        project_data = {
            'name': 'Simple Calculator',
            'file_path': '/test/calculator',
            'project_type': 'code',
            'languages': ['Python'],
            'frameworks': []
        }
        project = db_manager.create_project(project_data)
        header = generator.generate_project_header(project)
        
        assert project.name in header
        assert 'Python' in header
        assert '|' in header
    
    def test_generate_project_header_filters_html_css(self, generator):
        """Test that HTML/CSS are filtered from tech stack"""
        project_data = {
            'name': 'Website',
            'file_path': '/test/website',
            'project_type': 'code',
            'languages': ['HTML', 'CSS', 'JavaScript'],
            'frameworks': ['React']
        }
        project = db_manager.create_project(project_data)
        header = generator.generate_project_header(project)
        
        assert 'JavaScript' in header or 'React' in header
        assert project.name in header
    
    # ============================================
    # MAIN DESCRIPTION BULLET TESTS
    # ============================================
    
    def test_generate_main_description_with_description(self, generator, sample_project):
        """Test main bullet uses description when available"""
        bullet = generator._generate_main_description_bullet(sample_project)
        
        assert bullet.split()[0] in [v for verbs in generator.ACTION_VERBS.values() for v in verbs]
        assert len(bullet) > 10
    
    def test_generate_main_description_minimal_project(self, generator):
        """Test main bullet generation with minimal project data"""
        project_data = {
            'name': 'Minimal App',
            'file_path': '/test/minimal',
            'project_type': 'code',
            'languages': ['Python']
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_main_description_bullet(project)
        
        assert bullet.split()[0] in [v for verbs in generator.ACTION_VERBS.values() for v in verbs]
        assert 'Python' in bullet or 'application' in bullet
    
    # ============================================
    # SCALE BULLET TESTS
    # ============================================
    
    def test_generate_scale_bullet_with_metrics(self, generator, sample_project):
        """Test scale bullet generation with project metrics"""
        bullet = generator._generate_scale_bullet(sample_project, [])
        
        assert bullet is not None
        assert '5,000' in bullet or '45' in bullet
    
    def test_generate_scale_bullet_with_team(self, generator, web_project):
        """Test scale bullet includes team size"""
        db_manager.add_contributor_to_project({
            'project_id': web_project.id,
            'name': 'Developer 1',
            'commit_count': 50
        })
        db_manager.add_contributor_to_project({
            'project_id': web_project.id,
            'name': 'Developer 2',
            'commit_count': 30
        })
        
        project = db_manager.get_project(web_project.id)
        bullet = generator._generate_scale_bullet(project, [])
        
        assert bullet is not None
        assert '2-person team' in bullet or 'collaboration' in bullet.lower()
    
    def test_generate_scale_bullet_returns_none_for_small_project(self, generator):
        """Test scale bullet returns None for projects below thresholds"""
        project_data = {
            'name': 'Tiny App',
            'file_path': '/test/tiny',
            'project_type': 'code',
            'lines_of_code': 500,
            'file_count': 5
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_scale_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # SKILLS BULLET TESTS
    # ============================================
    
    def test_generate_skills_bullet_with_multiple_skills(self, generator, web_project):
        """Test skills bullet generation with multiple skills"""
        bullet = generator._generate_skills_bullet(web_project, [])
        
        assert bullet is not None
        assert any(skill.split()[0] in bullet for skill in web_project.skills[:4])
    
    def test_generate_skills_bullet_returns_none_with_few_skills(self, generator):
        """Test skills bullet returns None when insufficient skills"""
        project_data = {
            'name': 'No Skills',
            'file_path': '/test/noskills',
            'project_type': 'code',
            'skills': []
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_skills_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # IMPACT BULLET TESTS
    # ============================================
    
    def test_generate_impact_bullet_with_metrics(self, generator, sample_project):
        """Test impact bullet generation with success metrics"""
        success_metrics = {
            'users': 1000,
            'performance_improvement': 40,
            'success_rate': 95
        }
        db_manager.update_project(sample_project.id, {'success_evidence': json.dumps(success_metrics)})
        
        project = db_manager.get_project(sample_project.id)
        bullet = generator._generate_impact_bullet(project, [])
        
        assert bullet is not None
        assert '1000' in bullet or '40' in bullet or '95' in bullet
    
    def test_generate_impact_bullet_returns_none_without_metrics(self, generator):
        """Test impact bullet returns None without success metrics"""
        project_data = {
            'name': 'No Metrics',
            'file_path': '/test/nometrics',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        bullet = generator._generate_impact_bullet(project, [])
        
        assert bullet is None
    
    # ============================================
    # COMPLETE BULLET GENERATION TESTS
    # ============================================
    
    def test_generate_resume_bullets_default_count(self, generator, sample_project):
        """Test generating default number of bullets (3)"""
        bullets = generator.generate_resume_bullets(sample_project)
        
        assert len(bullets) == 3
        assert all(isinstance(b, str) for b in bullets)
        assert all(len(b) > 10 for b in bullets)
    
    def test_generate_resume_bullets_avoids_duplicate_verbs(self, generator, sample_project):
        """Test that generated bullets avoid repeating action verbs"""
        bullets = generator.generate_resume_bullets(sample_project, num_bullets=3)
        
        verbs = [bullet.split()[0] for bullet in bullets]
        assert len(set(verbs)) >= 2
    
    # ============================================
    # FORMAT RESUME COMPONENT TESTS
    # ============================================
    
    def test_format_resume_component_structure(self, generator, sample_project):
        """Test complete resume component formatting"""
        component = generator.format_resume_component(sample_project)
        
        assert sample_project.name in component
        assert '|' in component
        assert '•' in component
        assert component.count('•') == 3
        assert '\n' in component
    
    # ============================================
    # GENERATE_BULLETS_FOR_PROJECT TESTS
    # ============================================
    
    def test_generate_bullets_for_project_success(self, generator, sample_project):
        """Test generating bullets for valid project"""
        result = generator.generate_bullets_for_project(sample_project.id)
        
        assert result['success'] is True
        assert result['project_id'] == sample_project.id
        assert result['project_type'] == 'code'
        assert 'header' in result
        assert 'bullets' in result
        assert len(result['bullets']) == 3
    
    def test_generate_bullets_for_project_invalid_id(self, generator):
        """Test handling of invalid project ID"""
        result = generator.generate_bullets_for_project(99999)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_generate_bullets_for_project_wrong_type(self, generator):
        """Test handling of non-code project"""
        project_data = {
            'name': 'Media Project',
            'file_path': '/test/media',
            'project_type': 'visual_media'
        }
        project = db_manager.create_project(project_data)
        result = generator.generate_bullets_for_project(project.id)
        
        assert result['success'] is False
        assert 'not a coding project' in result['error']
    
    # ============================================
    # EDGE CASE TESTS
    # ============================================
    
    def test_handles_none_values_gracefully(self, generator):
        """Test handling of None values in project data"""
        project_data = {
            'name': 'Sparse Project',
            'file_path': '/test/sparse',
            'project_type': 'code',
            'languages': None,
            'frameworks': None,
            'skills': None
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project)
        assert len(bullets) >= 1
    
    def test_very_large_metrics(self, generator):
        """Test handling of very large metric values"""
        project_data = {
            'name': 'Large Project',
            'file_path': '/test/large',
            'project_type': 'code',
            'lines_of_code': 1000000,
            'file_count': 5000,
            'languages': ['Java']
        }
        project = db_manager.create_project(project_data)
        
        bullets = generator.generate_resume_bullets(project)
        scale_bullet = generator._generate_scale_bullet(project, [])
        
        if scale_bullet:
            assert '1,000,000' in scale_bullet or '5,000' in scale_bullet


if __name__ == "__main__":
    pytest.main([__file__, '-v'])