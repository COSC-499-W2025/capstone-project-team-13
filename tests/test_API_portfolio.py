import os
import sys
from fastapi import status
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from src.mainAPI import app
from src.Databases.database import db_manager

client = TestClient(app)


def setup_function():
    db_manager.clear_all_data()


def teardown_function():
    db_manager.clear_all_data()


def _create_project(project_type="code", name="Test Project"):
    project = db_manager.create_project({
        "name": name,
        "file_path": f"/test/{name.replace(' ', '_').lower()}",
        "project_type": project_type,
    })
    return project.id

# ── GET /portfolio ─────────────────────────────────────────────────────────────

def test_get_portfolio_empty():
    response = client.get("/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 0
    assert data["projects"] == []


def test_get_portfolio_with_projects():
    _create_project(name="Project A")
    _create_project(name="Project B")
    response = client.get("/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 2
    assert len(data["projects"]) == 2
    assert "summary" in data
    assert "stats" in data
    assert "generated_at" in data


def test_get_portfolio_excludes_hidden_by_default():
    pid = _create_project(name="Hidden Project")
    client.post(f"/portfolio/{pid}/edit", json={"is_hidden": True})

    response = client.get("/portfolio")
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden Project" not in names


def test_get_portfolio_include_hidden():
    pid = _create_project(name="Hidden Project")
    client.post(f"/portfolio/{pid}/edit", json={"is_hidden": True})

    response = client.get("/portfolio?include_hidden=true")
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden Project" in names


# ── GET /portfolio/stats ───────────────────────────────────────────────────────

def test_get_portfolio_stats_empty():
    response = client.get("/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 0

def test_get_portfolio_stats_with_projects():
    _create_project(project_type="code", name="Code Project")
    _create_project(project_type="text", name="Text Project")
    response = client.get("/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 2
    assert "by_type" in data
    assert "featured_count" in data


# ── GET /portfolio/summary ─────────────────────────────────────────────────────

def test_get_portfolio_summary_empty():
    response = client.get("/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "highlights" in data


def test_get_portfolio_summary_with_projects():
    _create_project(name="Cool Project")
    response = client.get("/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] != ""


# ── GET /portfolio/{project_id} ────────────────────────────────────────────────

def test_get_portfolio_project_success():
    pid = _create_project(name="My Project")
    response = client.get(f"/portfolio/{pid}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Project"


def test_get_portfolio_project_not_found():
    response = client.get("/portfolio/99999")
    assert response.status_code == 404


def test_get_portfolio_project_invalid_id():
    response = client.get("/portfolio/abc")
    assert response.status_code == 422


# ── POST /portfolio/generate ───────────────────────────────────────────────────

def test_generate_portfolio_returns_message_or_portfolio():
    _create_project(name="Gen Project")

    response = client.post("/portfolio/generate")
    assert response.status_code == 200

    data = response.json()

    if "message" in data:
        assert data["message"].lower().startswith("portfolio")
    else:
        assert "projects" in data
        assert "summary" in data
        assert "stats" in data


# ── POST /portfolio/{project_id}/edit ──────────────────────────────────────────

def test_edit_portfolio_project_success():
    pid = _create_project(name="Editable Project")

    response = client.post(
        f"/portfolio/{pid}/edit",
        json={
            "is_featured": True,
            "is_hidden": True,
            "importance_score": 0.9,
            "custom_description": "Updated via edit endpoint",
        },
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
    response = client.post("/portfolio/99999/edit", json={"is_featured": True})
    assert response.status_code == 404


def test_edit_portfolio_project_invalid_id():
    response = client.post("/portfolio/abc/edit", json={"is_featured": True})
    assert response.status_code == 422


def test_edit_portfolio_project_empty_body():
    pid = _create_project()
    response = client.post(f"/portfolio/{pid}/edit", json={})
    assert response.status_code in (200, 400)


def test_edit_portfolio_project_hides_from_default_portfolio():
    pid = _create_project(name="Hidden via Edit")

    response = client.post(f"/portfolio/{pid}/edit", json={"is_hidden": True})
    assert response.status_code == 200

    response = client.get("/portfolio")
    assert response.status_code == 200
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden via Edit" not in names

    response = client.get("/portfolio?include_hidden=true")
    assert response.status_code == 200
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden via Edit" in names