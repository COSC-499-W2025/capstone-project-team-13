import pytest
from unittest.mock import MagicMock
from src.Services import analytics_service as analytics
from collections import namedtuple
import os
import sys

from src.mainAPI import app

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

# Create a fake Project object
FakeProject = namedtuple("FakeProject", ["id", "name", "skills"])

# --- Fixtures ---
@pytest.fixture
def mock_db(monkeypatch):
    """
    Mock db_manager.get_all_projects() to return fake projects
    """
    fake_projects = [
        FakeProject(id=1, name="Project A", skills=["Python", "FastAPI", "SQL"]),
        FakeProject(id=2, name="Project B", skills=["Python", "Django"]),
        FakeProject(id=3, name="Project C", skills=["Java", "Spring"]),
        FakeProject(id=4, name="Project D", skills=["Python", "FastAPI"]),
    ]

    monkeypatch.setattr(
        "src.Databases.database.db_manager.get_all_projects",
        lambda: fake_projects
    )

# --- Tests ---
def test_get_raw_skills_with_projects(mock_db):
    raw = analytics.get_raw_skills_with_projects()
    # Check that Python appears in 3 projects
    python_skill = next(s for s in raw if s["skill"] == "Python")
    assert python_skill["count"] == 3
    project_names = [p["project_name"] for p in python_skill["projects"]]
    assert set(project_names) == {"Project A", "Project B", "Project D"}

def test_get_skill_cooccurrence_with_projects(mock_db):
    co = analytics.get_skill_cooccurrence()
    # Find Python + FastAPI pair
    pair = next(p for p in co if p["skill_1"] == "FastAPI" and p["skill_2"] == "Python")
    assert pair["count"] == 2
    project_names = [p["project_name"] for p in pair["projects"]]
    assert set(project_names) == {"Project A", "Project D"}

def test_get_full_skill_analytics(mock_db):
    analytics_data = analytics.get_full_skill_analytics()
    assert "raw" in analytics_data
    assert "insights" in analytics_data

    # Check raw skills contains Python
    raw_python = next(s for s in analytics_data["raw"]["skills"] if s["skill"] == "Python")
    assert raw_python["count"] == 3

    # Check co-occurrence is included
    co_occurrence = analytics_data["raw"]["co_occurrence"]
    assert any(p["skill_1"] == "FastAPI" and p["skill_2"] == "Python" for p in co_occurrence)

    # Check insights include top_skills
    top_skills = analytics_data["insights"]["top_skills"]
    assert len(top_skills) > 0
    assert top_skills[0]["skill"] == "Python"
