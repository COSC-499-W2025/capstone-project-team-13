import os
import sys

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
    client.patch(f"/portfolio/{pid}", json={"is_hidden": True})
    response = client.get("/portfolio")
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert "Hidden Project" not in names


def test_get_portfolio_include_hidden():
    pid = _create_project(name="Hidden Project")
    client.patch(f"/portfolio/{pid}", json={"is_hidden": True})
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


# ── PATCH /portfolio/{project_id} ──────────────────────────────────────────────

def test_update_portfolio_project_featured():
    pid = _create_project()
    response = client.patch(f"/portfolio/{pid}", json={"is_featured": True})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_featured"] is True


def test_update_portfolio_project_hidden():
    pid = _create_project()
    response = client.patch(f"/portfolio/{pid}", json={"is_hidden": True})
    assert response.status_code == 200
    assert response.json()["is_hidden"] is True


def test_update_portfolio_project_custom_description():
    pid = _create_project()
    response = client.patch(f"/portfolio/{pid}", json={"custom_description": "My custom desc"})
    assert response.status_code == 200
    assert response.json()["custom_description"] == "My custom desc"


def test_update_portfolio_project_not_found():
    response = client.patch("/portfolio/99999", json={"is_featured": True})
    assert response.status_code == 404


def test_update_portfolio_project_no_fields():
    pid = _create_project()
    response = client.patch(f"/portfolio/{pid}", json={})
    assert response.status_code == 400


def test_update_portfolio_project_invalid_id():
    response = client.patch("/portfolio/xyz", json={"is_featured": True})
    assert response.status_code == 422