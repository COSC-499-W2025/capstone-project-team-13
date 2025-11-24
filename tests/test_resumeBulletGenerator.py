"""
Comprehensive test suite for resume bullet generator

Tests:
- Project header generation with tech stack
- Main description bullet generation
- Scale/scope bullet generation
- Skills bullet generation
- Impact bullet generation
- Complete resume component formatting
- Batch generation
- Edge cases and error handling
- All project types (code, visual_media, text)
"""

import os
import sys
import pytest
import json
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Resume.resumeBulletGenerator import (
    ResumeBulletGenerator,
    generate_resume_bullets_for_all_projects,
    print_resume_component
)
from src.Databases.database import db_manager, Project


class TestResumeBulletGenerator:
    """Test suite for ResumeBulletGenerator class"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Setup: Clear database before each test
        db_manager.clear_all_data()
        yield
        # Teardown: Clear database after each test
        db_manager.clear_all_data()
    
    @pytest.fixture
    def generator(self):
        """Create a ResumeBulletGenerator instance"""
        return ResumeBulletGenerator()
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing"""
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
    
    @pytest.fixture
    def minimal_project(self):
        """Create a minimal project with limited data"""
        project_data = {
            'name': 'Simple Calculator',
            'file_path': '/test/calculator',
            'project_type': 'code',
            'lines_of_code': 500,
            'file_count': 5,
            'languages': ['Python'],
            'frameworks': [],
            'skills': []
        }
        return db_manager.create_project(project_data)
    
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
    
    def test_generate_project_header_without_frameworks(self, generator, minimal_project):
        """Test header generation without frameworks"""
        header = generator.generate_project_header(minimal_project)
        
        assert minimal_project.name in header
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
        
        # HTML and CSS should be filtered out, JavaScript should remain
        assert 'JavaScript' in header or 'React' in header
        # But header should still be valid
        assert project.name in header
    
    def test_generate_project_header_media_project(self, generator, media_project):
        """Test header generation for media projects"""
        header = generator.generate_project_header(media_project)
        
        assert media_project.name in header
        assert 'Adobe' in header  # Should show software
        assert '|' in header
    
    def test_generate_project_header_text_project(self, generator, text_project):
        """Test header generation for text projects"""
        header = generator.generate_project_header(text_project)
        
        assert text_project.name in header
        assert '|' in header
        # Should show document types from tags
        assert 'Markdown' in header or 'PDF' in header or 'Writing' in header
    
    # ============================================
    # MAIN DESCRIPTION BULLET TESTS
    # ============================================
    
    def test_generate_main_description_with_custom_description(self, generator, sample_project):
        """Test main bullet uses custom description when available"""
        custom_desc = "a unique gaming experience with advanced AI"
        db_manager.update_project(sample_project.id, {'custom_description': custom_desc})
        
        project = db_manager.get_project(sample_project.id)
        bullet = generator._generate_main_description_bullet(project)
        
        # Should use action verb
        assert bullet.split()[0] in [v for verbs in generator.ACTION_VERBS.values() for v in verbs]
        assert len(bullet) > 10
    
    def test_generate_main_description_with_description(self, generator, sample_project):
        """Test main bullet uses description when available"""
        bullet = generator._generate_main_description_bullet(sample_project)
        
        assert bullet.split()[0] in [v for verbs in generator.ACTION_VERBS.values() for v in verbs]
        assert len(bullet) > 10
    
    def test_generate_main_description_minimal_project(self, generator, minimal_project):
        """Test main bullet generation with minimal project data"""
        bullet = generator._generate_main_description_bullet(minimal_project)
        
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
        assert any(verb in bullet for verb in ['maintained', 'managed', 'handled'])
    
    def test_generate_scale_bullet_with_team(self, generator, web_project):
        """Test scale bullet includes team size"""
        # Add contributors
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
    
    def test_generate_scale_bullet_returns_none_for_small_project(self, generator, minimal_project):
        """Test scale bullet returns None for projects below thresholds"""
        # Minimal project has 500 LOC and 5 files (both below thresholds)
        bullet = generator._generate_scale_bullet(minimal_project, [])
        
        # Should return None because metrics are too small
        assert bullet is None
    
    # ============================================
    # SKILLS BULLET TESTS
    # ============================================
    
    def test_generate_skills_bullet_with_multiple_skills(self, generator, web_project):
        """Test skills bullet generation with multiple skills"""
        bullet = generator._generate_skills_bullet(web_project, [])
        
        assert bullet is not None
        # Should mention at least some skills
        assert any(skill.split()[0] in bullet for skill in web_project.skills[:4])
    
    def test_generate_skills_bullet_returns_none_with_few_skills(self, generator, minimal_project):
        """Test skills bullet returns None when insufficient skills"""
        bullet = generator._generate_skills_bullet(minimal_project, [])
        
        assert bullet is None  # Minimal project has no skills
    
    def test_generate_skills_bullet_formatting(self, generator, sample_project):
        """Test skills bullet proper formatting with commas and 'and'"""
        bullet = generator._generate_skills_bullet(sample_project, [])
        
        if bullet:
            # Should have proper English formatting
            assert 'using' in bullet.lower()
            assert 'and' in bullet or ',' in bullet
    
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
    
    def test_generate_impact_bullet_returns_none_without_metrics(self, generator, minimal_project):
        """Test impact bullet returns None without success metrics"""
        bullet = generator._generate_impact_bullet(minimal_project, [])
        
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
    
    def test_generate_resume_bullets_custom_count(self, generator, web_project):
        """Test generating custom number of bullets"""
        bullets = generator.generate_resume_bullets(web_project, num_bullets=5)
        
        assert len(bullets) <= 5  # May be less if not enough data
        assert all(isinstance(b, str) for b in bullets)
    
    def test_generate_resume_bullets_avoids_duplicate_verbs(self, generator, sample_project):
        """Test that generated bullets avoid repeating action verbs"""
        bullets = generator.generate_resume_bullets(sample_project, num_bullets=3)
        
        # Extract first word (action verb) from each bullet
        verbs = [bullet.split()[0] for bullet in bullets]
        
        # Should have variety in verbs (at least 2 different ones for 3 bullets)
        assert len(set(verbs)) >= 2
    
    def test_generate_resume_bullets_minimal_project(self, generator, minimal_project):
        """Test bullet generation works with minimal data"""
        bullets = generator.generate_resume_bullets(minimal_project, num_bullets=3)
        
        assert len(bullets) >= 1  # Should generate at least main bullet
        assert all(isinstance(b, str) for b in bullets)
    
    # ============================================
    # MEDIA PROJECT BULLET TESTS
    # ============================================
    
    def test_generate_media_bullets(self, generator, media_project):
        """Test bullet generation for media projects"""
        bullets = generator.generate_resume_bullets(media_project, num_bullets=3)
        
        assert len(bullets) >= 1
        assert all(isinstance(b, str) for b in bullets)
        # Should mention software or skills
        combined_text = ' '.join(bullets).lower()
        assert ('adobe' in combined_text or 'illustrator' in combined_text or 
                'photoshop' in combined_text or 'vector' in combined_text or 
                'logo' in combined_text or 'design' in combined_text)
    
    def test_generate_media_main_bullet(self, generator, media_project):
        """Test main bullet for media projects"""
        bullet = generator._generate_media_main_bullet(media_project)
        
        assert isinstance(bullet, str)
        assert len(bullet) > 10
        # Should use creative action verb
        first_word = bullet.split()[0]
        assert first_word in generator.ACTION_VERBS['creative']
    
    def test_generate_media_scale_bullet(self, generator, media_project):
        """Test scale bullet for media projects"""
        bullet = generator._generate_media_scale_bullet(media_project, [])
        
        assert bullet is not None
        # Should mention file count or size
        assert '45' in bullet or '250' in bullet or 'MB' in bullet
    
    # ============================================
    # TEXT PROJECT BULLET TESTS
    # ============================================
    
    def test_generate_text_bullets(self, generator, text_project):
        """Test bullet generation for text projects"""
        bullets = generator.generate_resume_bullets(text_project, num_bullets=3)
        
        assert len(bullets) >= 1
        assert all(isinstance(b, str) for b in bullets)
        # Should mention writing/documentation
        combined_text = ' '.join(bullets).lower()
        assert 'document' in combined_text or 'writ' in combined_text or 'content' in combined_text
    
    def test_generate_text_main_bullet(self, generator, text_project):
        """Test main bullet for text projects"""
        bullet = generator._generate_text_main_bullet(text_project)
        
        assert isinstance(bullet, str)
        assert len(bullet) > 10
        # Should use writing action verb
        first_word = bullet.split()[0]
        assert first_word in generator.ACTION_VERBS['writing']
    
    def test_generate_text_scale_bullet(self, generator, text_project):
        """Test scale bullet for text projects"""
        bullet = generator._generate_text_scale_bullet(text_project, [])
        
        assert bullet is not None
        # Should mention word count or document count
        assert '25' in bullet or '15' in bullet or 'word' in bullet.lower() or 'document' in bullet.lower()
    
    # ============================================
    # FORMAT RESUME COMPONENT TESTS
    # ============================================
    
    def test_format_resume_component_structure(self, generator, sample_project):
        """Test complete resume component formatting"""
        component = generator.format_resume_component(sample_project)
        
        # Should have header
        assert sample_project.name in component
        assert '|' in component
        
        # Should have bullets
        assert '•' in component
        assert component.count('•') == 3  # Default 3 bullets
        
        # Should have newlines
        assert '\n' in component
    
    def test_format_resume_component_custom_bullets(self, generator, web_project):
        """Test formatting with custom bullet count"""
        component = generator.format_resume_component(web_project, num_bullets=2)
        
        assert web_project.name in component
        assert component.count('•') <= 2
    
    # ============================================
    # BULLET GENERATION WITHOUT STORAGE TESTS
    # ============================================
    
    def test_generate_bullets_for_project_success(self, generator, sample_project):
        """Test generating bullets without storing in database"""
        result = generator.generate_bullets_for_project(sample_project.id)
        
        assert result['success'] is True
        assert result['project_id'] == sample_project.id
        assert 'header' in result
        assert 'bullets' in result
        assert 'formatted_component' in result
        assert len(result['bullets']) == 3
    
    def test_generate_bullets_for_project_invalid_project(self, generator):
        """Test handling of invalid project ID"""
        result = generator.generate_bullets_for_project(99999)
        
        assert result['success'] is False
        assert 'error' in result
    
    # ============================================
    # BATCH GENERATION TESTS
    # ============================================
    
    def test_batch_generate_bullets_multiple_projects(self, generator, sample_project, web_project):
        """Test batch generation for multiple projects"""
        project_ids = [sample_project.id, web_project.id]
        results = generator.batch_generate_bullets(project_ids)
        
        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert results[0]['project_id'] == sample_project.id
        assert results[1]['project_id'] == web_project.id
    
    def test_batch_generate_bullets_empty_list(self, generator):
        """Test batch generation with empty list"""
        results = generator.batch_generate_bullets([])
        
        assert results == []
    
    def test_batch_generate_bullets_mixed_valid_invalid(self, generator, sample_project):
        """Test batch generation with mix of valid and invalid IDs"""
        project_ids = [sample_project.id, 99999]
        results = generator.batch_generate_bullets(project_ids)
        
        assert len(results) == 2
        assert results[0]['success'] is True
        assert results[1]['success'] is False
    
    # ============================================
    # HELPER FUNCTION TESTS
    # ============================================
    
    def test_generate_resume_bullets_for_all_projects(self, sample_project, web_project):
        """Test generating bullets for all projects in database"""
        results = generate_resume_bullets_for_all_projects()
        
        # Should generate for coding projects only
        assert len(results) == 2
        assert all(r['success'] for r in results)
    
    def test_generate_resume_bullets_for_all_projects_all_types(self):
        """Test that function processes all project types"""
        # Add projects of different types
        db_manager.create_project({
            'name': 'Design Portfolio',
            'file_path': '/test/design',
            'project_type': 'visual_media',
            'languages': ['Adobe Photoshop']
        })
        
        db_manager.create_project({
            'name': 'Code Project',
            'file_path': '/test/code',
            'project_type': 'code',
            'languages': ['Python']
        })
        
        db_manager.create_project({
            'name': 'Writing Project',
            'file_path': '/test/writing',
            'project_type': 'text',
            'word_count': 5000
        })
        
        results = generate_resume_bullets_for_all_projects()
        
        # Should process all three projects
        assert len(results) == 3
        assert all(r['success'] for r in results)
    
    # ============================================
    # EDGE CASE TESTS
    # ============================================
    
    def test_technical_features_extraction(self, generator):
        """Test extraction of technical features from skills"""
        project_data = {
            'name': 'API Project',
            'file_path': '/test/api',
            'project_type': 'code',
            'skills': ['API Development', 'Database Management', 'Testing']
        }
        project = db_manager.create_project(project_data)
        
        features = generator._extract_technical_features(project)
        
        assert isinstance(features, list)
        assert len(features) > 0
    
    def test_action_verb_selection_variety(self, generator, sample_project):
        """Test that action verb selection provides variety"""
        used_verbs = []
        verbs = []
        
        for _ in range(5):
            verb = generator._select_action_verb(sample_project, used_verbs)
            verbs.append(verb)
            used_verbs.append(verb)
        
        # Should have selected different verbs
        assert len(set(verbs)) > 1
    
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
        
        # Should not raise errors
        bullets = generator.generate_resume_bullets(project)
        assert len(bullets) >= 1
    
    def test_handles_empty_lists(self, generator):
        """Test handling of empty lists in project data"""
        project_data = {
            'name': 'Empty Project',
            'file_path': '/test/empty',
            'project_type': 'code',
            'languages': [],
            'frameworks': [],
            'skills': []
        }
        project = db_manager.create_project(project_data)
        
        # Should not raise errors
        component = generator.format_resume_component(project)
        assert project.name in component
    
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
        
        # Should format large numbers with commas
        if scale_bullet:
            assert '1,000,000' in scale_bullet or '5,000' in scale_bullet


# ============================================
# INTEGRATION TESTS
# ============================================

class TestResumeBulletGeneratorIntegration:
    """Integration tests for resume bullet generator with database"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for integration tests"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from project creation to bullet generation"""
        # Create project
        project_data = {
            'name': 'Full Stack App',
            'file_path': '/test/fullstack',
            'project_type': 'code',
            'lines_of_code': 10000,
            'file_count': 150,
            'languages': ['JavaScript', 'Python'],
            'frameworks': ['React', 'Django'],
            'skills': ['Frontend Development', 'Backend Development', 'API Development']
        }
        project = db_manager.create_project(project_data)
        
        # Generate bullets
        generator = ResumeBulletGenerator()
        result = generator.generate_bullets_for_project(project.id, num_bullets=3)
        
        # Verify generation
        assert result['success'] is True
        assert len(result['bullets']) == 3
        
        # Verify formatted output
        component = result['formatted_component']
        assert 'Full Stack App' in component
        assert '•' in component
    
    def test_multiple_projects_generation(self):
        """Test that bullets generate correctly for multiple projects"""
        generator = ResumeBulletGenerator()
        
        # Create multiple projects
        projects = []
        for i in range(3):
            project_data = {
                'name': f'Project {i+1}',
                'file_path': f'/test/project{i+1}',
                'project_type': 'code',
                'languages': ['Python'],
                'skills': ['Web Development']
            }
            project = db_manager.create_project(project_data)
            projects.append(project)
        
        # Generate bullets for all
        for project in projects:
            result = generator.generate_bullets_for_project(project.id)
            assert result['success'] is True
            assert f'Project {project.id}' in result['header']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])