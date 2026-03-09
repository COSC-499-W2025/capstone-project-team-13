import os
import sys
from fastapi import status
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from src.mainAPI import app
from src.Databases.database import db_manager
from src.Services.auth_service import create_access_token, hash_password

client = TestClient(app)


def setup_function():
    db_manager.clear_all_data()


def teardown_function():
    db_manager.clear_all_data()


def _create_user(email="test@example.com"):
    """Create a test user and return (user, auth_headers)."""
    user = db_manager.create_user({
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password_hash": hash_password("password123"),
    })
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _create_project(user_id, project_type="code", name="Test Project"):
    """Create a test project owned by the given user."""
    project = db_manager.create_project({
        "name": name,
        "file_path": f"/test/{name.replace(' ', '_').lower()}",
        "project_type": project_type,
        "user_id": user_id,
    })
    return project.id


# ── UNAUTHENTICATED REQUESTS ───────────────────────────────────────────────────

def test_get_portfolio_requires_auth():
    response = client.get("/portfolio")
    assert response.status_code == 401


def test_get_portfolio_stats_requires_auth():
    response = client.get("/portfolio/stats")
    assert response.status_code == 401


def test_get_portfolio_summary_requires_auth():
    response = client.get("/portfolio/summary")
    assert response.status_code == 401


def test_get_portfolio_project_requires_auth():
    response = client.get("/portfolio/1")
    assert response.status_code == 401


def test_generate_portfolio_requires_auth():
    response = client.post("/portfolio/generate")
    assert response.status_code == 401


def test_edit_portfolio_project_requires_auth():
    response = client.post("/portfolio/1/edit", json={"is_featured": True})
    assert response.status_code == 401


# ── GET /portfolio ─────────────────────────────────────────────────────────────

def test_get_portfolio_empty():
    _, headers = _create_user()
    response = client.get("/portfolio", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 0
    assert data["projects"] == []


def test_get_portfolio_with_projects():
    user, headers = _create_user()
    _create_project(user.id, name="Project A")
    _create_project(user.id, name="Project B")
    response = client.get("/portfolio", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 2
    assert len(data["projects"]) == 2
    assert "summary" in data
    assert "stats" in data
    assert "generated_at" in data


def test_get_portfolio_excludes_hidden_by_default():
    user, headers = _create_user()
    pid = _create_project(user.id, name="Hidden Project")
    client.post(f"/portfolio/{pid}/edit", json={"is_hidden": True}, headers=headers)

    response = client.get("/portfolio", headers=headers)
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden Project" not in names


def test_get_portfolio_include_hidden():
    user, headers = _create_user()
    pid = _create_project(user.id, name="Hidden Project")
    client.post(f"/portfolio/{pid}/edit", json={"is_hidden": True}, headers=headers)

    response = client.get("/portfolio?include_hidden=true", headers=headers)
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden Project" in names


def test_get_portfolio_only_shows_own_projects():
    """User A should not see User B's projects."""
    user_a, headers_a = _create_user(email="usera@example.com")
    user_b, headers_b = _create_user(email="userb@example.com")

    _create_project(user_a.id, name="User A Project")
    _create_project(user_b.id, name="User B Project")

    response = client.get("/portfolio", headers=headers_a)
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "User A Project" in names
    assert "User B Project" not in names


# ── GET /portfolio/stats ───────────────────────────────────────────────────────

def test_get_portfolio_stats_empty():
    _, headers = _create_user()
    response = client.get("/portfolio/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 0


def test_get_portfolio_stats_with_projects():
    user, headers = _create_user()
    _create_project(user.id, project_type="code", name="Code Project")
    _create_project(user.id, project_type="text", name="Text Project")
    response = client.get("/portfolio/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 2
    assert "by_type" in data
    assert "featured_count" in data


# ── GET /portfolio/summary ─────────────────────────────────────────────────────

def test_get_portfolio_summary_empty():
    _, headers = _create_user()
    response = client.get("/portfolio/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "highlights" in data


def test_get_portfolio_summary_with_projects():
    user, headers = _create_user()
    _create_project(user.id, name="Cool Project")
    response = client.get("/portfolio/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] != ""


# ── GET /portfolio/{project_id} ────────────────────────────────────────────────

def test_get_portfolio_project_success():
    user, headers = _create_user()
    pid = _create_project(user.id, name="My Project")
    response = client.get(f"/portfolio/{pid}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Project"


def test_get_portfolio_project_not_found():
    _, headers = _create_user()
    response = client.get("/portfolio/99999", headers=headers)
    assert response.status_code == 404


def test_get_portfolio_project_invalid_id():
    _, headers = _create_user()
    response = client.get("/portfolio/abc", headers=headers)
    assert response.status_code == 422


def test_get_portfolio_project_forbidden_for_other_user():
    """User B should not be able to view User A's project."""
    user_a, _ = _create_user(email="usera@example.com")
    _, headers_b = _create_user(email="userb@example.com")

    pid = _create_project(user_a.id, name="User A Private Project")
    response = client.get(f"/portfolio/{pid}", headers=headers_b)
    assert response.status_code == 403


# ── POST /portfolio/generate ───────────────────────────────────────────────────

def test_generate_portfolio_returns_portfolio():
    user, headers = _create_user()
    _create_project(user.id, name="Gen Project")

    response = client.post("/portfolio/generate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "summary" in data
    assert "stats" in data


def test_generate_portfolio_saves_to_user():
    """After generating, the portfolio should be persisted on the user record."""
    user, headers = _create_user()
    _create_project(user.id, name="Saved Project")

    client.post("/portfolio/generate", headers=headers)

    updated_user = db_manager.get_user(user.id)
    assert updated_user.portfolio is not None
    assert "projects" in updated_user.portfolio


# ── POST /portfolio/{project_id}/edit ──────────────────────────────────────────

def test_edit_portfolio_project_success():
    user, headers = _create_user()
    pid = _create_project(user.id, name="Editable Project")

    response = client.post(
        f"/portfolio/{pid}/edit",
        json={
            "is_featured": True,
            "is_hidden": True,
            "importance_score": 0.9,
            "custom_description": "Updated via edit endpoint",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == pid
    assert data["is_featured"] is True
    assert data["is_hidden"] is True

    if "importance_score" in data:
        assert data["importance_score"] == 0.9
    if "custom_description" in data:
        assert data["custom_description"] == "Updated via edit endpoint"


def test_edit_portfolio_project_not_found():
    _, headers = _create_user()
    response = client.post("/portfolio/99999/edit", json={"is_featured": True}, headers=headers)
    assert response.status_code == 404


def test_edit_portfolio_project_invalid_id():
    _, headers = _create_user()
    response = client.post("/portfolio/abc/edit", json={"is_featured": True}, headers=headers)
    assert response.status_code == 422


def test_edit_portfolio_project_empty_body():
    user, headers = _create_user()
    pid = _create_project(user.id)
    response = client.post(f"/portfolio/{pid}/edit", json={}, headers=headers)
    assert response.status_code in (200, 400)


def test_edit_portfolio_project_forbidden_for_other_user():
    """User B should not be able to edit User A's project."""
    user_a, _ = _create_user(email="usera@example.com")
    _, headers_b = _create_user(email="userb@example.com")

    pid = _create_project(user_a.id, name="User A Project")
    response = client.post(f"/portfolio/{pid}/edit", json={"is_featured": True}, headers=headers_b)
    assert response.status_code == 403


def test_edit_portfolio_project_hides_from_default_portfolio():
    user, headers = _create_user()
    pid = _create_project(user.id, name="Hidden via Edit")

    response = client.post(f"/portfolio/{pid}/edit", json={"is_hidden": True}, headers=headers)
    assert response.status_code == 200

    response = client.get("/portfolio", headers=headers)
    assert response.status_code == 200
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden via Edit" not in names

    response = client.get("/portfolio?include_hidden=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden via Edit" in names


def test_edit_portfolio_project_saves_portfolio_to_user():
    """After editing, the updated portfolio should be persisted on the user record."""
    user, headers = _create_user()
    pid = _create_project(user.id, name="Edit Saves Portfolio")

    client.post(f"/portfolio/{pid}/edit", json={"is_featured": True}, headers=headers)

    updated_user = db_manager.get_user(user.id)
    assert updated_user.portfolio is not None
    assert "projects" in updated_user.portfolio