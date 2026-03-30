"""
Tests for get_skills_timeline service function
"""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from src.Services.skills_service import get_skills_timeline


def make_project(id, name, skills, project_type="code"):
    project = MagicMock()
    project.id = id
    project.name = name
    project.skills = skills
    project.project_type = project_type
    project.custom_description = None
    return project


@patch("src.Services.skills_service.db_manager")
def test_returns_empty_when_no_projects(mock_db):
    mock_db.get_all_projects.return_value = []
    result = get_skills_timeline(user_id=1)
    assert result == {"skills": []}


@patch("src.Services.skills_service.db_manager")
def test_returns_empty_when_projects_have_no_skills(mock_db):
    project = make_project(1, "Project A", skills=[])
    mock_db.get_all_projects.return_value = [project]
    mock_db.get_project_duration.return_value = (date(2024, 1, 1), date(2024, 6, 1), 152)
    result = get_skills_timeline(user_id=1)
    assert result == {"skills": []}


@patch("src.Services.skills_service.db_manager")
def test_single_project_single_skill(mock_db):
    project = make_project(1, "Project A", skills=["Python"])
    mock_db.get_all_projects.return_value = [project]
    mock_db.get_project_duration.return_value = (date(2024, 1, 1), date(2024, 6, 1), 152)

    result = get_skills_timeline(user_id=1)
    skills = result["skills"]

    assert len(skills) == 1
    assert skills[0]["name"] == "Python"
    assert skills[0]["first_seen"] == "2024-01-01"
    assert skills[0]["last_seen"] == "2024-06-01"
    assert skills[0]["project_count"] == 1


@patch("src.Services.skills_service.db_manager")
def test_skill_appears_in_multiple_projects_tracks_date_range(mock_db):
    project1 = make_project(1, "Project A", skills=["Python"])
    project2 = make_project(2, "Project B", skills=["Python"])

    mock_db.get_all_projects.return_value = [project1, project2]
    mock_db.get_project_duration.side_effect = [
        (date(2023, 1, 1), date(2023, 6, 1), 151),
        (date(2024, 3, 1), date(2024, 9, 1), 185),
    ]

    result = get_skills_timeline(user_id=1)
    skills = result["skills"]

    assert len(skills) == 1
    python = skills[0]
    assert python["name"] == "Python"
    assert python["first_seen"] == "2023-01-01"
    assert python["last_seen"] == "2024-09-01"
    assert python["project_count"] == 2


@patch("src.Services.skills_service.db_manager")
def test_multiple_skills_sorted_by_first_seen(mock_db):
    project1 = make_project(1, "Project A", skills=["Python"])
    project2 = make_project(2, "Project B", skills=["React"])

    mock_db.get_all_projects.return_value = [project1, project2]
    mock_db.get_project_duration.side_effect = [
        (date(2024, 6, 1), date(2024, 9, 1), 92),
        (date(2023, 1, 1), date(2023, 6, 1), 151),
    ]

    result = get_skills_timeline(user_id=1)
    skills = result["skills"]

    assert len(skills) == 2
    assert skills[0]["name"] == "React"
    assert skills[1]["name"] == "Python"


@patch("src.Services.skills_service.db_manager")
def test_handles_none_dates_gracefully(mock_db):
    project = make_project(1, "Project A", skills=["Python"])
    mock_db.get_all_projects.return_value = [project]
    mock_db.get_project_duration.return_value = (None, None, 0)

    result = get_skills_timeline(user_id=1)
    skills = result["skills"]

    assert len(skills) == 1
    assert skills[0]["first_seen"] is None
    assert skills[0]["last_seen"] is None


@patch("src.Services.skills_service.db_manager")
def test_project_details_included_in_skill(mock_db):
    project = make_project(1, "My App", skills=["Django"], project_type="code")
    mock_db.get_all_projects.return_value = [project]
    mock_db.get_project_duration.return_value = (date(2024, 1, 1), date(2024, 3, 1), 60)

    result = get_skills_timeline(user_id=1)
    skill = result["skills"][0]

    assert len(skill["projects"]) == 1
    p = skill["projects"][0]
    assert p["project_id"] == 1
    assert p["project_name"] == "My App"
    assert p["project_type"] == "code"
    assert p["first_activity_date"] == "2024-01-01"
    assert p["last_activity_date"] == "2024-03-01"
    assert p["duration_days"] == 60