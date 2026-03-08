import pytest
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

# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_user(email="analytics_test@example.com"):
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


# ── GET /analytics/co-occurrence ───────────────────────────────────────────────

def test_cooccurrence_guest():
    """Guest sees co-occurrence from guest projects only."""
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["Python", "FastAPI"],
    })
    response = client.get("/analytics/co-occurrence")
    assert response.status_code == 200
    data = response.json()
    assert "pairs" in data
    pair_sets = [set([p["skill_1"], p["skill_2"]]) for p in data["pairs"]]
    assert {"Python", "FastAPI"} in pair_sets


def test_cooccurrence_authenticated():
    """Authenticated user sees co-occurrence from their own projects only."""
    user, headers = _create_user()
    _create_project(user.id, name="My Project", skills=["Django", "PostgreSQL"])

    # Guest project — should not appear
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["GuestSkillA", "GuestSkillB"],
    })

    response = client.get("/analytics/co-occurrence", headers=headers)
    assert response.status_code == 200
    data = response.json()
    pair_sets = [set([p["skill_1"], p["skill_2"]]) for p in data["pairs"]]
    assert {"Django", "PostgreSQL"} in pair_sets
    assert {"GuestSkillA", "GuestSkillB"} not in pair_sets


def test_cooccurrence_empty():
    """Returns empty pairs when no projects exist."""
    _, headers = _create_user()
    response = client.get("/analytics/co-occurrence", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pairs"] == []


def test_cooccurrence_single_skill_project():
    """Projects with only one skill produce no pairs."""
    user, headers = _create_user()
    _create_project(user.id, name="Solo Skill Project", skills=["Python"])
    response = client.get("/analytics/co-occurrence", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pairs"] == []


def test_cooccurrence_no_cross_user_leakage():
    """User A should not see User B's skill pairs."""
    user_a, headers_a = _create_user(email="user_a@example.com")
    user_b, _ = _create_user(email="user_b@example.com")

    _create_project(user_b.id, name="B Project", skills=["SkillX", "SkillY"])

    response = client.get("/analytics/co-occurrence", headers=headers_a)
    data = response.json()
    pair_sets = [set([p["skill_1"], p["skill_2"]]) for p in data["pairs"]]
    assert {"SkillX", "SkillY"} not in pair_sets


# ── GET /analytics/skills ──────────────────────────────────────────────────────

def test_analytics_skills_guest():
    """Guest sees analytics from guest projects only."""
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["Python", "FastAPI"],
    })
    response = client.get("/analytics/skills")
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert "insights" in data
    skill_names = [s["skill"] for s in data["raw"]["skills"]]
    assert "Python" in skill_names


def test_analytics_skills_authenticated():
    """Authenticated user sees analytics from their own projects only."""
    user, headers = _create_user()
    _create_project(user.id, name="My Project A", skills=["Rust", "WebAssembly"])
    _create_project(user.id, name="My Project B", skills=["Rust", "LLVM"])

    # Guest project — should not appear
    db_manager.create_project({
        "name": "Guest Project",
        "file_path": "/test/guest_project",
        "project_type": "code",
        "skills": ["GuestOnlySkill"],
    })

    response = client.get("/analytics/skills", headers=headers)
    assert response.status_code == 200
    data = response.json()
    skill_names = [s["skill"] for s in data["raw"]["skills"]]
    assert "Rust" in skill_names
    assert "GuestOnlySkill" not in skill_names


def test_analytics_skills_structure():
    """Response always contains the expected structure."""
    _, headers = _create_user()
    response = client.get("/analytics/skills", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "raw" in data
    assert "skills" in data["raw"]
    assert "co_occurrence" in data["raw"]
    assert "insights" in data
    assert "top_skills" in data["insights"]
    assert "most_common_pair" in data["insights"]
    assert "skill_diversity" in data["insights"]


def test_analytics_skills_diversity_score():
    """Diversity score should be > 0 when projects have skills."""
    user, headers = _create_user()
    _create_project(user.id, name="Project A", skills=["Python", "SQL"])
    _create_project(user.id, name="Project B", skills=["Java", "Spring"])

    response = client.get("/analytics/skills", headers=headers)
    data = response.json()
    assert data["insights"]["skill_diversity"] > 0


def test_analytics_skills_top_skill_is_most_common():
    """The first top skill should be the one appearing in the most projects."""
    user, headers = _create_user()
    _create_project(user.id, name="Project A", skills=["Python", "SQL"])
    _create_project(user.id, name="Project B", skills=["Python", "Django"])
    _create_project(user.id, name="Project C", skills=["Java"])

    response = client.get("/analytics/skills", headers=headers)
    data = response.json()
    top_skills = data["insights"]["top_skills"]
    assert top_skills[0]["skill"] == "Python"


def test_analytics_skills_no_cross_user_leakage():
    """User A should not see User B's skills in analytics."""
    user_a, headers_a = _create_user(email="user_a@example.com")
    user_b, _ = _create_user(email="user_b@example.com")

    _create_project(user_b.id, name="B Project", skills=["UniqueSkillB"])

    response = client.get("/analytics/skills", headers=headers_a)
    data = response.json()
    skill_names = [s["skill"] for s in data["raw"]["skills"]]
    assert "UniqueSkillB" not in skill_names