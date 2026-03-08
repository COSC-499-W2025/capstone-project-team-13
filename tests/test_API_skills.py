import pytest
from unittest.mock import MagicMock
from src.Services import analytics_service as analytics
from src.Services import skills_service as skills
from collections import namedtuple
import os
import sys

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from src.mainAPI import app
from src.Databases.database import db_manager
from src.Services.auth_service import create_access_token, hash_password

client = TestClient(app)

# Create a fake Project object
FakeProject = namedtuple("FakeProject", ["id", "name", "skills", "project_type", "file_count"])

# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_user(email="skills_test@example.com"):
    user = db_manager.create_user({
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password_hash": hash_password("password123"),
    })
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _create_project(user_id, name="Test Project", skills=None):
    project = db_manager.create_project({
        "name": name,
        "file_path": f"/test/{name.replace(' ', '_').lower()}",
        "project_type": "code",
        "user_id": user_id,
        "skills": skills or [],
    })
    return project


def setup_function():
    db_manager.clear_all_data()


def teardown_function():
    db_manager.clear_all_data()


# ── Monkeypatch fixture ────────────────────────────────────────────────────────

FAKE_PROJECTS = [
    FakeProject(id=1, name="Project A", skills=["Python", "FastAPI", "SQL"], project_type="code", file_count=10),
    FakeProject(id=2, name="Project B", skills=["Python", "Django"], project_type="code", file_count=5),
    FakeProject(id=3, name="Project C", skills=["Java", "Spring"], project_type="code", file_count=8),
    FakeProject(id=4, name="Project D", skills=["Python", "FastAPI"], project_type="code", file_count=3),
]

@pytest.fixture
def mock_db(monkeypatch):
    """Mock get_all_projects to accept user_id kwarg and return fake projects."""
    monkeypatch.setattr(
        "src.Databases.database.db_manager.get_all_projects",
        lambda include_hidden=False, user_id=None: FAKE_PROJECTS
    )


# ── Unit tests (monkeypatched) ─────────────────────────────────────────────────

def test_get_raw_skills_with_projects(mock_db):
    raw = analytics.get_raw_skills_with_projects()
    python_skill = next(s for s in raw if s["skill"] == "Python")
    assert python_skill["count"] == 3
    project_names = [p["project_name"] for p in python_skill["projects"]]
    assert set(project_names) == {"Project A", "Project B", "Project D"}


def test_get_skill_cooccurrence_with_projects(mock_db):
    co = analytics.get_skill_cooccurrence()
    pair = next(p for p in co if set([p["skill_1"], p["skill_2"]]) == {"FastAPI", "Python"})
    assert pair["count"] == 2
    project_names = [p["project_name"] for p in pair["projects"]]
    assert set(project_names) == {"Project A", "Project D"}


def test_get_full_skill_analytics(mock_db):
    analytics_data = analytics.get_full_skill_analytics()
    assert "raw" in analytics_data
    assert "insights" in analytics_data

    raw_python = next(s for s in analytics_data["raw"]["skills"] if s["skill"] == "Python")
    assert raw_python["count"] == 3

    co_occurrence = analytics_data["raw"]["co_occurrence"]
    assert any(set([p["skill_1"], p["skill_2"]]) == {"FastAPI", "Python"} for p in co_occurrence)

    top_skills = analytics_data["insights"]["top_skills"]
    assert len(top_skills) > 0
    assert top_skills[0]["skill"] == "Python"


def test_get_skills_service(mock_db):
    result = skills.get_skills()
    assert "skills" in result
    python_skill = next(s for s in result["skills"] if s["name"] == "Python")
    assert python_skill["count"] == 3


def test_get_skill_detail_service(mock_db):
    result = skills.get_skill_detail("Python")
    assert result["skill"] == "Python"
    assert result["project_count"] == 3


def test_get_skill_detail_not_found_service(mock_db):
    result = skills.get_skill_detail("NonExistentSkill")
    assert result["project_count"] == 0
    assert result["projects"] == []


# ── API integration tests ──────────────────────────────────────────────────────

# GET /skills/

def test_get_skills_guest():
    """Guest user sees only guest projects' skills."""
    # Create a guest project (no user_id)
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["Python", "FastAPI"],
    })
    response = client.get("/skills/")
    assert response.status_code == 200
    data = response.json()
    skill_names = [s["name"] for s in data["skills"]]
    assert "Python" in skill_names
    assert "FastAPI" in skill_names


def test_get_skills_authenticated():
    """Authenticated user sees only their own projects' skills."""
    user, headers = _create_user()
    _create_project(user.id, name="My Project", skills=["Django", "PostgreSQL"])

    # Also create a guest project — should not appear
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["GuestSkill"],
    })

    response = client.get("/skills/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    skill_names = [s["name"] for s in data["skills"]]
    assert "Django" in skill_names
    assert "PostgreSQL" in skill_names
    assert "GuestSkill" not in skill_names


def test_get_skills_only_shows_own_projects():
    """User A should not see User B's skills."""
    user_a, headers_a = _create_user(email="user_a@example.com")
    user_b, headers_b = _create_user(email="user_b@example.com")

    _create_project(user_a.id, name="A Project", skills=["SkillA"])
    _create_project(user_b.id, name="B Project", skills=["SkillB"])

    response = client.get("/skills/", headers=headers_a)
    data = response.json()
    skill_names = [s["name"] for s in data["skills"]]
    assert "SkillA" in skill_names
    assert "SkillB" not in skill_names


# GET /skills/{skill_name}

def test_get_skill_detail_guest():
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["Python"],
    })
    response = client.get("/skills/Python")
    assert response.status_code == 200
    data = response.json()
    assert data["skill"] == "Python"
    assert data["project_count"] == 1


def test_get_skill_detail_authenticated():
    user, headers = _create_user()
    _create_project(user.id, name="My Project", skills=["Rust"])

    response = client.get("/skills/Rust", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["skill"] == "Rust"
    assert data["project_count"] == 1


def test_get_skill_detail_not_found():
    _, headers = _create_user()
    response = client.get("/skills/NonExistentSkill", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_count"] == 0


def test_get_skill_detail_no_cross_user_leakage():
    """User B's skill should not appear in User A's skill detail."""
    user_a, headers_a = _create_user(email="user_a@example.com")
    user_b, _ = _create_user(email="user_b@example.com")

    _create_project(user_b.id, name="B Project", skills=["SharedSkill"])

    response = client.get("/skills/SharedSkill", headers=headers_a)
    data = response.json()
    assert data["project_count"] == 0