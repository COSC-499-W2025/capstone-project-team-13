"""
Unit tests for Showcase Selector

Tests project selection functionality for portfolio showcase.
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager, Project
from src.Portfolio.showcaseSelector import (
    list_projects_with_showcase_status,
    toggle_project_showcase,
    get_showcased_projects,
)


@pytest.fixture(scope='function')
def clean_db():
    """Clean database before each test"""
    session = db_manager.get_session()
    try:
        session.query(Project).delete()
        session.commit()
    finally:
        session.close()
    
    yield
    
    session = db_manager.get_session()
    try:
        session.query(Project).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def sample_projects(clean_db):
    """Create sample projects for testing"""
    projects = []
    
    # Create 3 projects with different showcase states
    p1 = db_manager.create_project({
        'name': 'Showcased Project',
        'file_path': '/test/path1',
        'project_type': 'code',
        'is_hidden': False  # Showcased
    })
    
    p2 = db_manager.create_project({
        'name': 'Hidden Project',
        'file_path': '/test/path2',
        'project_type': 'media',
        'is_hidden': True  # Hidden
    })
    
    p3 = db_manager.create_project({
        'name': 'Default Project',
        'file_path': '/test/path3',
        'project_type': 'text',
        # is_hidden defaults to False
    })
    
    projects = [p1, p2, p3]
    return projects


class TestShowcaseSelector:
    """Test showcase selector functionality"""
    
    def test_list_projects_with_status(self, sample_projects):
        """Test listing projects with showcase status"""
        projects_with_status = list_projects_with_showcase_status()
        
        assert len(projects_with_status) == 3
        
        # Check structure
        for project, is_showcased in projects_with_status:
            assert isinstance(project, Project)
            assert isinstance(is_showcased, bool)
        
        # Check specific statuses
        statuses = {p.name: is_showcased for p, is_showcased in projects_with_status}
        assert statuses['Showcased Project'] is True
        assert statuses['Hidden Project'] is False
        assert statuses['Default Project'] is True  # Default is showcased
    
    def test_toggle_showcase_hide(self, sample_projects):
        """Test toggling project from showcased to hidden"""
        project = sample_projects[0]  # Showcased Project
        
        assert project.is_hidden is False
        
        # Toggle to hidden
        toggle_project_showcase(project)
        
        # Verify in database
        updated = db_manager.get_project(project.id)
        assert updated.is_hidden is True
    
    def test_toggle_showcase_show(self, sample_projects):
        """Test toggling project from hidden to showcased"""
        project = sample_projects[1]  # Hidden Project
        
        assert project.is_hidden is True
        
        # Toggle to showcased
        toggle_project_showcase(project)
        
        # Verify in database
        updated = db_manager.get_project(project.id)
        assert updated.is_hidden is False
    
    def test_toggle_multiple_times(self, sample_projects):
        """Test toggling same project multiple times"""
        project = sample_projects[0]
        
        original_state = project.is_hidden
        
        # Toggle twice should return to original
        toggle_project_showcase(project)
        toggle_project_showcase(project)
        
        updated = db_manager.get_project(project.id)
        assert updated.is_hidden == original_state
    
    def test_get_showcased_projects(self, sample_projects):
        """Test getting only showcased projects"""
        showcased = get_showcased_projects()
        
        showcased_names = [p.name for p in showcased]
        
        assert 'Showcased Project' in showcased_names
        assert 'Default Project' in showcased_names
        assert 'Hidden Project' not in showcased_names
        
        assert len(showcased) == 2
    
    def test_get_showcased_empty_db(self, clean_db):
        """Test getting showcased projects from empty database"""
        showcased = get_showcased_projects()
        assert showcased == []
    
    def test_all_hidden(self, sample_projects):
        """Test when all projects are hidden"""
        # Hide all projects
        for project in sample_projects:
            db_manager.update_project(project.id, {"is_hidden": True})
        
        showcased = get_showcased_projects()
        assert len(showcased) == 0
    
    def test_all_showcased(self, sample_projects):
        """Test when all projects are showcased"""
        # Show all projects
        for project in sample_projects:
            db_manager.update_project(project.id, {"is_hidden": False})
        
        showcased = get_showcased_projects()
        assert len(showcased) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])