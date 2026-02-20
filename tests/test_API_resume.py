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


def _create_project(project_type="code"):
    """Helper: insert a project and return its id."""
    project = db_manager.create_project({
        "name": "Test Project",
        "file_path": f"/test/{project_type}_project",
        "project_type": project_type,
    })
    return project.id


# ── GET /resume/{project_id} ──────────────────────────────────────────────────

def test_get_resume_no_bullets():
    pid = _create_project()
    response = client.get(f"/resume/{pid}")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == pid
    assert data["bullets"] is None


def test_get_resume_not_found():
    response = client.get("/resume/99999")
    assert response.status_code == 404


def test_get_resume_invalid_id():
    response = client.get("/resume/abc")
    assert response.status_code == 422


# ── POST /resume/generate ─────────────────────────────────────────────────────

def test_generate_resume_success():
    pid = _create_project()
    response = client.post("/resume/generate", json={"project_id": pid, "num_bullets": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["bullets"]) == 3
    assert data["project_id"] == pid


def test_generate_resume_project_not_found():
    response = client.post("/resume/generate", json={"project_id": 99999})
    assert response.status_code == 404


def test_generate_resume_persists():
    """Generated bullets should be retrievable afterwards."""
    pid = _create_project()
    client.post("/resume/generate", json={"project_id": pid, "num_bullets": 3})
    response = client.get(f"/resume/{pid}")
    assert response.status_code == 200
    assert response.json()["bullets"] is not None


# ── POST /resume/{project_id}/edit ────────────────────────────────────────────

def test_edit_resume_success():
    pid = _create_project()
    client.post("/resume/generate", json={"project_id": pid})
    new_bullets = ["Updated bullet one", "Updated bullet two"]
    response = client.post(f"/resume/{pid}/edit", json={"bullets": new_bullets})
    assert response.status_code == 200
    data = response.json()
    assert data["bullets"] == new_bullets


def test_edit_resume_not_found():
    response = client.post("/resume/99999/edit", json={"bullets": ["bullet"]})
    assert response.status_code == 404


def test_edit_resume_invalid_id():
    response = client.post("/resume/xyz/edit", json={"bullets": ["bullet"]})
    assert response.status_code == 422