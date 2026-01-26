"""
Comprehensive test suite for resume generator

Tests:
- Getting projects with bullets
- Project selection and display
- Project ordering (keep, reverse, manual)
- Resume header formatting
- Project section formatting
- Complete resume document generation
- Edge cases and error handling
"""

import os
import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Resume.resumeGenerator import (
    get_projects_with_bullets,
    display_projects_for_selection,
    select_projects_for_resume,
    order_projects,
    manual_reorder,
    format_resume_header,
    format_project_section,
    generate_resume_document
)
from src.Databases.database import db_manager, Project


class TestGetProjectsWithBullets:
    """Test suite for getting projects with stored bullets"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    def test_get_projects_with_bullets_empty(self):
        """Test getting projects when none have bullets"""
        projects = get_projects_with_bullets()
        assert projects == []
    
    def test_get_projects_with_bullets_some_have_bullets(self):
        """Test getting only projects that have bullets"""
        # Create project with bullets
        project1_data = {
            'name': 'Project 1',
            'file_path': '/test/p1',
            'project_type': 'code'
        }
        project1 = db_manager.create_project(project1_data)
        db_manager.save_resume_bullets(
            project1.id,
            ['Bullet 1', 'Bullet 2'],
            'Project 1 | Python',
            85.0
        )
        
        # Create project without bullets
        project2_data = {
            'name': 'Project 2',
            'file_path': '/test/p2',
            'project_type': 'code'
        }
        db_manager.create_project(project2_data)
        
        # Get projects with bullets
        projects = get_projects_with_bullets()
        
        assert len(projects) == 1
        assert projects[0].name == 'Project 1'
        assert projects[0].bullets is not None
    
    def test_get_projects_with_bullets_all_have_bullets(self):
        """Test getting all projects when all have bullets"""
        # Create multiple projects with bullets
        for i in range(3):
            project_data = {
                'name': f'Project {i+1}',
                'file_path': f'/test/p{i+1}',
                'project_type': 'code'
            }
            project = db_manager.create_project(project_data)
            db_manager.save_resume_bullets(
                project.id,
                [f'Bullet {i+1}'],
                f'Project {i+1} | Tech',
                80.0
            )
        
        projects = get_projects_with_bullets()
        assert len(projects) == 3


class TestProjectSelection:
    """Test suite for project selection functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_projects(self):
        """Create sample projects with bullets"""
        projects = []
        for i in range(3):
            project_data = {
                'name': f'Project {i+1}',
                'file_path': f'/test/p{i+1}',
                'project_type': 'code'
            }
            project = db_manager.create_project(project_data)
            db_manager.save_resume_bullets(
                project.id,
                [f'Bullet {i+1}a', f'Bullet {i+1}b'],
                f'Project {i+1} | Tech',
                85.0
            )
            projects.append(db_manager.get_project(project.id))
        return projects
    
    @patch('builtins.input', return_value='all')
    def test_select_projects_all(self, mock_input, sample_projects):
        """Test selecting all projects"""
        selected = select_projects_for_resume(sample_projects)
        
        assert len(selected) == 3
        assert selected == sample_projects
    
    @patch('builtins.input', return_value='c')
    def test_select_projects_cancel(self, mock_input, sample_projects):
        """Test cancelling project selection"""
        selected = select_projects_for_resume(sample_projects)
        
        assert len(selected) == 0
    
    @patch('builtins.input', return_value='1,3')
    def test_select_projects_specific(self, mock_input, sample_projects):
        """Test selecting specific projects by number"""
        selected = select_projects_for_resume(sample_projects)
        
        assert len(selected) == 2
        assert selected[0].name == 'Project 1'
        assert selected[1].name == 'Project 3'
    
    @patch('builtins.input', return_value='2')
    def test_select_projects_single(self, mock_input, sample_projects):
        """Test selecting single project"""
        selected = select_projects_for_resume(sample_projects)
        
        assert len(selected) == 1
        assert selected[0].name == 'Project 2'
    
    @patch('builtins.input', return_value='1,5,2')
    def test_select_projects_with_invalid(self, mock_input, sample_projects):
        """Test selecting with some invalid indices"""
        selected = select_projects_for_resume(sample_projects)
        
        # Should skip invalid index 5
        assert len(selected) == 2
        assert selected[0].name == 'Project 1'
        assert selected[1].name == 'Project 2'
    
    @patch('builtins.input', return_value='invalid')
    def test_select_projects_invalid_input(self, mock_input, sample_projects):
        """Test handling invalid input format"""
        selected = select_projects_for_resume(sample_projects)
        
        assert len(selected) == 0
    
    def test_select_projects_empty_list(self):
        """Test selecting from empty project list"""
        selected = select_projects_for_resume([])
        
        assert len(selected) == 0


class TestProjectOrdering:
    """Test suite for project ordering functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_projects(self):
        """Create sample projects"""
        projects = []
        for i in range(3):
            project_data = {
                'name': f'Project {i+1}',
                'file_path': f'/test/p{i+1}',
                'project_type': 'code'
            }
            project = db_manager.create_project(project_data)
            db_manager.save_resume_bullets(
                project.id,
                [f'Bullet {i+1}'],
                f'Project {i+1} | Tech',
                80.0
            )
            projects.append(db_manager.get_project(project.id))
        return projects
    
    @patch('builtins.input', return_value='1')
    def test_order_projects_keep_current(self, mock_input, sample_projects):
        """Test keeping current order"""
        ordered = order_projects(sample_projects)
        
        assert len(ordered) == 3
        assert ordered[0].name == 'Project 1'
        assert ordered[1].name == 'Project 2'
        assert ordered[2].name == 'Project 3'
    
    @patch('builtins.input', return_value='2')
    def test_order_projects_reverse(self, mock_input, sample_projects):
        """Test reversing order"""
        ordered = order_projects(sample_projects)
        
        assert len(ordered) == 3
        assert ordered[0].name == 'Project 3'
        assert ordered[1].name == 'Project 2'
        assert ordered[2].name == 'Project 1'
    
    @patch('src.Resume.resumeGenerator.manual_reorder')
    @patch('builtins.input', return_value='3')
    def test_order_projects_manual(self, mock_input, mock_manual, sample_projects):
        """Test manual reordering"""
        mock_manual.return_value = [sample_projects[2], sample_projects[0], sample_projects[1]]
        
        ordered = order_projects(sample_projects)
        
        assert mock_manual.called
        assert ordered[0].name == 'Project 3'
    
    @patch('builtins.input', return_value='invalid')
    def test_order_projects_invalid_choice(self, mock_input, sample_projects):
        """Test invalid ordering choice defaults to current order"""
        ordered = order_projects(sample_projects)
        
        assert ordered == sample_projects
    
    def test_order_projects_single_project(self, sample_projects):
        """Test ordering with single project (should return as-is)"""
        ordered = order_projects([sample_projects[0]])
        
        assert len(ordered) == 1
        assert ordered[0] == sample_projects[0]


class TestManualReorder:
    """Test suite for manual project reordering"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_projects(self):
        """Create sample projects"""
        projects = []
        for i in range(3):
            project_data = {
                'name': f'Project {i+1}',
                'file_path': f'/test/p{i+1}',
                'project_type': 'code'
            }
            project = db_manager.create_project(project_data)
            projects.append(project)
        return projects
    
    @patch('builtins.input', return_value='3,1,2')
    def test_manual_reorder_success(self, mock_input, sample_projects):
        """Test successful manual reordering"""
        reordered = manual_reorder(sample_projects)
        
        assert len(reordered) == 3
        assert reordered[0].name == 'Project 3'
        assert reordered[1].name == 'Project 1'
        assert reordered[2].name == 'Project 2'
    
    @patch('builtins.input', return_value='1,2')
    def test_manual_reorder_incomplete(self, mock_input, sample_projects):
        """Test manual reorder with incomplete list"""
        reordered = manual_reorder(sample_projects)
        
        # Should return original order
        assert reordered == sample_projects
    
    @patch('builtins.input', return_value='1,1,2')
    def test_manual_reorder_duplicates(self, mock_input, sample_projects):
        """Test manual reorder with duplicate indices"""
        reordered = manual_reorder(sample_projects)
        
        # Should return original order
        assert reordered == sample_projects
    
    @patch('builtins.input', return_value='1,5,2')
    def test_manual_reorder_invalid_index(self, mock_input, sample_projects):
        """Test manual reorder with invalid index"""
        reordered = manual_reorder(sample_projects)
        
        # Should return original order
        assert reordered == sample_projects
    
    @patch('builtins.input', return_value='invalid')
    def test_manual_reorder_invalid_format(self, mock_input, sample_projects):
        """Test manual reorder with invalid input format"""
        reordered = manual_reorder(sample_projects)
        
        # Should return original order
        assert reordered == sample_projects


class TestResumeFormatting:
    """Test suite for resume formatting functions"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    def test_format_resume_header(self):
        """Test resume header formatting"""
        header = format_resume_header("John Doe")
        
        assert "JOHN DOE" in header
        assert "=" in header
        assert len(header.split('\n')) >= 3
    
    def test_format_resume_header_long_name(self):
        """Test header with long name"""
        header = format_resume_header("Alexander Sebastian Montgomery")
        
        assert "ALEXANDER SEBASTIAN MONTGOMERY" in header
        assert "=" in header
    
    def test_format_project_section(self):
        """Test formatting project section with bullets"""
        project_data = {
            'name': 'Test Project',
            'file_path': '/test/project',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        db_manager.save_resume_bullets(
            project.id,
            ['Bullet 1', 'Bullet 2', 'Bullet 3'],
            'Test Project | Python, Django',
            85.0
        )
        
        project = db_manager.get_project(project.id)
        section = format_project_section(project)
        
        assert 'Test Project | Python, Django' in section
        assert '• Bullet 1' in section
        assert '• Bullet 2' in section
        assert '• Bullet 3' in section
    
    def test_format_project_section_no_bullets(self):
        """Test formatting project without bullets"""
        project_data = {
            'name': 'No Bullets',
            'file_path': '/test/no_bullets',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        
        section = format_project_section(project)
        
        assert section == ""


class TestResumeDocumentGeneration:
    """Test suite for complete resume document generation"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    @pytest.fixture
    def sample_projects(self):
        """Create sample projects with bullets"""
        projects = []
        for i in range(2):
            project_data = {
                'name': f'Project {i+1}',
                'file_path': f'/test/p{i+1}',
                'project_type': 'code'
            }
            project = db_manager.create_project(project_data)
            db_manager.save_resume_bullets(
                project.id,
                [f'Bullet {i+1}a', f'Bullet {i+1}b'],
                f'Project {i+1} | Tech Stack',
                85.0
            )
            projects.append(db_manager.get_project(project.id))
        return projects
    
    def test_generate_resume_document_complete(self, sample_projects):
        """Test generating complete resume document"""
        resume = generate_resume_document("Jane Smith", sample_projects)
        
        # Check header
        assert "JANE SMITH" in resume
        
        # Check section title
        assert "PROJECTS" in resume
        
        # Check both projects
        assert "Project 1 | Tech Stack" in resume
        assert "Project 2 | Tech Stack" in resume
        
        # Check bullets
        assert "• Bullet 1a" in resume
        assert "• Bullet 2b" in resume
        
        # Check footer
        assert "Generated on:" in resume
    
    def test_generate_resume_document_single_project(self, sample_projects):
        """Test generating resume with single project"""
        resume = generate_resume_document("John Doe", [sample_projects[0]])
        
        assert "JOHN DOE" in resume
        assert "Project 1 | Tech Stack" in resume
        assert "Project 2" not in resume
    
    def test_generate_resume_document_structure(self, sample_projects):
        """Test resume document has proper structure"""
        resume = generate_resume_document("Test User", sample_projects)
        
        lines = resume.split('\n')
        
        # Should have multiple sections
        assert len(lines) > 10
        
        # Should have separators
        assert any('=' in line for line in lines)
        assert any('-' in line for line in lines)
    
    def test_generate_resume_document_preserves_order(self, sample_projects):
        """Test that resume preserves project order"""
        # Reverse order
        reversed_projects = list(reversed(sample_projects))
        resume = generate_resume_document("Test User", reversed_projects)
        
        # Find positions of project headers
        pos_1 = resume.find("Project 1")
        pos_2 = resume.find("Project 2")
        
        # Project 2 should appear before Project 1
        assert pos_2 < pos_1


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        db_manager.clear_all_data()
        yield
        db_manager.clear_all_data()
    
    def test_format_resume_header_empty_name(self):
        """Test header with empty name"""
        header = format_resume_header("")
        
        assert "=" in header
        # Should still generate header even if name is empty
    
    def test_generate_resume_document_empty_projects(self):
        """Test generating resume with no projects"""
        resume = generate_resume_document("Test User", [])
        
        assert "TEST USER" in resume
        assert "PROJECTS" in resume
        assert "Generated on:" in resume
    
    def test_format_project_section_special_characters(self):
        """Test project section with special characters in bullets"""
        project_data = {
            'name': 'Special & Project',
            'file_path': '/test/special',
            'project_type': 'code'
        }
        project = db_manager.create_project(project_data)
        db_manager.save_resume_bullets(
            project.id,
            ['Bullet with "quotes"', 'Bullet with & ampersand'],
            'Special & Project | Tech',
            80.0
        )
        
        project = db_manager.get_project(project.id)
        section = format_project_section(project)
        
        assert 'Special & Project' in section
        assert '"quotes"' in section
        assert '& ampersand' in section


if __name__ == "__main__":
    pytest.main([__file__, '-v'])