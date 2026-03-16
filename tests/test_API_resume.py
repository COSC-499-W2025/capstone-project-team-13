import os
import sys

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from src.mainAPI import app
from src.Databases.database import db_manager

client = TestClient(app)


# ── helpers ───────────────────────────────────────────────────────────────────

def setup_function():
    db_manager.clear_all_data()


def teardown_function():
    db_manager.clear_all_data()


def _create_user(email="test@example.com"):
    """Register a user and return (user_id, auth_headers)."""
    resp = client.post("/auth/signup", json={
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": "password123"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]
    return resp.json()["user"]["id"], {"Authorization": f"Bearer {token}"}


def _create_project_for_user(user_id, project_type="code"):
    """Directly insert a project owned by user_id and return its id."""
    project = db_manager.create_project({
        "name": "Test Project",
        "file_path": f"/test/{project_type}_project",
        "project_type": project_type,
        "user_id": user_id,
    })
    return project.id


# ── auth guard tests ──────────────────────────────────────────────────────────

def test_get_bullets_requires_auth():
    user_id, _ = _create_user()
    pid = _create_project_for_user(user_id)
    response = client.get(f"/resume/projects/{pid}")
    assert response.status_code == 401


def test_generate_bullets_requires_auth():
    response = client.post("/resume/projects/1/generate")
    assert response.status_code == 401


def test_edit_bullets_requires_auth():
    response = client.post("/resume/projects/1/edit", json={"bullets": ["bullet"]})
    assert response.status_code == 401


def test_regenerate_bullets_requires_auth():
    response = client.post("/resume/projects/1/regenerate")
    assert response.status_code == 401


def test_get_ats_requires_auth():
    response = client.get("/resume/projects/1/ats")
    assert response.status_code == 401


def test_delete_bullets_requires_auth():
    response = client.delete("/resume/projects/1")
    assert response.status_code == 401


def test_generate_full_resume_requires_auth():
    response = client.post("/resume/generate")
    assert response.status_code == 401


def test_get_full_resume_requires_auth():
    response = client.get("/resume")
    assert response.status_code == 401


def test_save_resume_requires_auth():
    response = client.post("/resume/save", json={"name": "Test"})
    assert response.status_code == 401


# ── ownership tests ───────────────────────────────────────────────────────────

def test_get_bullets_wrong_user():
    """User B cannot access User A's project bullets."""
    user_a_id, _ = _create_user("a@example.com")
    _, headers_b = _create_user("b@example.com")
    pid = _create_project_for_user(user_a_id)
    response = client.get(f"/resume/projects/{pid}", headers=headers_b)
    assert response.status_code == 403


def test_generate_bullets_wrong_user():
    user_a_id, _ = _create_user("a@example.com")
    _, headers_b = _create_user("b@example.com")
    pid = _create_project_for_user(user_a_id)
    response = client.post(f"/resume/projects/{pid}/generate", headers=headers_b)
    assert response.status_code == 403


def test_edit_bullets_wrong_user():
    user_a_id, _ = _create_user("a@example.com")
    _, headers_b = _create_user("b@example.com")
    pid = _create_project_for_user(user_a_id)
    response = client.post(
        f"/resume/projects/{pid}/edit",
        json={"bullets": ["bullet"]},
        headers=headers_b
    )
    assert response.status_code == 403


def test_delete_bullets_wrong_user():
    user_a_id, _ = _create_user("a@example.com")
    _, headers_b = _create_user("b@example.com")
    pid = _create_project_for_user(user_a_id)
    # Give project A some bullets first
    client.post(f"/resume/projects/{pid}/generate", headers={"Authorization": "Bearer " + client.post("/auth/login", json={"email": "a@example.com", "password": "password123"}).json()["token"]})
    response = client.delete(f"/resume/projects/{pid}", headers=headers_b)
    assert response.status_code == 403


# ── GET /resume/projects/{project_id} ────────────────────────────────────────

def test_get_bullets_no_bullets_yet():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    response = client.get(f"/resume/projects/{pid}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == pid
    assert data["bullets"] is None
    assert "message" in data


def test_get_bullets_not_found():
    _, headers = _create_user()
    response = client.get("/resume/projects/99999", headers=headers)
    assert response.status_code == 404


def test_get_bullets_invalid_id():
    _, headers = _create_user()
    response = client.get("/resume/projects/abc", headers=headers)
    assert response.status_code == 422


# ── POST /resume/projects/{project_id}/generate ───────────────────────────────

def test_generate_bullets_success():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    response = client.post(f"/resume/projects/{pid}/generate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["project_id"] == pid
    assert len(data["bullets"]) == 3
    assert data["header"] is not None
    assert data["ats_score"] is not None


def test_generate_bullets_custom_count():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    response = client.post(
        f"/resume/projects/{pid}/generate",
        json={"num_bullets": 5},
        headers=headers
    )
    assert response.status_code == 200
    # Generator returns up to num_bullets; sparse test projects may produce fewer
    assert 1 <= len(response.json()["bullets"]) <= 5


def test_generate_bullets_persists():
    """Bullets should be retrievable after generation."""
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    response = client.get(f"/resume/projects/{pid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["bullets"] is not None


def test_generate_bullets_project_not_found():
    _, headers = _create_user()
    response = client.post("/resume/projects/99999/generate", headers=headers)
    assert response.status_code == 404


# ── POST /resume/projects/{project_id}/edit ───────────────────────────────────

def test_edit_bullets_success():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    new_bullets = ["Updated bullet one", "Updated bullet two"]
    response = client.post(
        f"/resume/projects/{pid}/edit",
        json={"bullets": new_bullets},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bullets"] == new_bullets
    assert data["success"] is True


def test_edit_bullets_with_custom_header():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    response = client.post(
        f"/resume/projects/{pid}/edit",
        json={"bullets": ["A bullet"], "header": "Custom Header | Python"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["header"] == "Custom Header | Python"


def test_edit_bullets_not_found():
    _, headers = _create_user()
    response = client.post(
        "/resume/projects/99999/edit",
        json={"bullets": ["bullet"]},
        headers=headers
    )
    assert response.status_code == 404


def test_edit_bullets_invalid_id():
    _, headers = _create_user()
    response = client.post(
        "/resume/projects/xyz/edit",
        json={"bullets": ["bullet"]},
        headers=headers
    )
    assert response.status_code == 422


# ── POST /resume/projects/{project_id}/regenerate ─────────────────────────────

def test_regenerate_bullets_success():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    original = client.get(f"/resume/projects/{pid}", headers=headers).json()["bullets"]
    response = client.post(f"/resume/projects/{pid}/regenerate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["bullets"]) == len(original)


def test_regenerate_bullets_project_not_found():
    _, headers = _create_user()
    response = client.post("/resume/projects/99999/regenerate", headers=headers)
    assert response.status_code == 404


# ── GET /resume/projects/{project_id}/ats ─────────────────────────────────────

def test_get_ats_success():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    response = client.get(f"/resume/projects/{pid}/ats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == pid
    assert "overall_score" in data
    assert "individual_scores" in data
    assert "grade_distribution" in data
    assert len(data["individual_scores"]) == 3


def test_get_ats_no_bullets():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    response = client.get(f"/resume/projects/{pid}/ats", headers=headers)
    assert response.status_code == 404


def test_get_ats_project_not_found():
    _, headers = _create_user()
    response = client.get("/resume/projects/99999/ats", headers=headers)
    assert response.status_code == 404


# ── DELETE /resume/projects/{project_id} ──────────────────────────────────────

def test_delete_bullets_success():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    response = client.delete(f"/resume/projects/{pid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    # Verify bullets are gone
    get_response = client.get(f"/resume/projects/{pid}", headers=headers)
    assert get_response.json()["bullets"] is None


def test_delete_bullets_none_exist():
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    response = client.delete(f"/resume/projects/{pid}", headers=headers)
    assert response.status_code == 404


def test_delete_bullets_project_not_found():
    _, headers = _create_user()
    response = client.delete("/resume/projects/99999", headers=headers)
    assert response.status_code == 404


# ── POST /resume/generate ─────────────────────────────────────────────────────

def test_generate_full_resume_success():
    user_id, headers = _create_user()
    _create_project_for_user(user_id)
    response = client.post("/resume/generate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "resume" in data
    assert data["resume"]["name"] == "Test User"
    assert len(data["resume"]["projects"]) == 1


def test_generate_full_resume_fills_missing_bullets():
    """Projects with no bullets should have bullets generated automatically."""
    user_id, headers = _create_user()
    _create_project_for_user(user_id)
    response = client.post("/resume/generate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["bullets_generated_for"] == 1
    assert len(data["resume"]["projects"][0]["bullets"]) > 0


def test_generate_full_resume_skips_existing_bullets():
    """Projects that already have bullets should not be regenerated."""
    user_id, headers = _create_user()
    pid = _create_project_for_user(user_id)
    client.post(f"/resume/projects/{pid}/generate", headers=headers)
    response = client.post("/resume/generate", headers=headers)
    assert response.status_code == 200
    assert response.json()["bullets_generated_for"] == 0


def test_generate_full_resume_no_projects():
    _, headers = _create_user()
    response = client.post("/resume/generate", headers=headers)
    assert response.status_code == 404


def test_generate_full_resume_persists():
    """Generated resume should be retrievable via GET /resume."""
    user_id, headers = _create_user()
    _create_project_for_user(user_id)
    client.post("/resume/generate", headers=headers)
    response = client.get("/resume", headers=headers)
    assert response.status_code == 200
    assert "resume" in response.json()


# ── GET /resume ───────────────────────────────────────────────────────────────

def test_get_full_resume_not_generated_yet():
    _, headers = _create_user()
    response = client.get("/resume", headers=headers)
    assert response.status_code == 404


def test_get_full_resume_success():
    user_id, headers = _create_user()
    _create_project_for_user(user_id)
    client.post("/resume/generate", headers=headers)
    response = client.get("/resume", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "resume" in data
    assert data["resume"]["name"] == "Test User"


# ── POST /resume/save ─────────────────────────────────────────────────────────

def test_save_resume_success():
    user_id, headers = _create_user()
    resume_payload = {
        "name": "Test User",
        "projects": [],
        "education": [{"institution": "UBC", "degree_type": "BSc", "topic": "CS"}],
        "skills": ["Python", "FastAPI"],
        "work_history": [{"company": "Acme", "role": "Dev", "years": 2}],
    }
    response = client.post("/resume/save", json=resume_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_save_resume_persists():
    """Saved resume should be returned by GET /resume."""
    user_id, headers = _create_user()
    resume_payload = {"name": "Test User", "projects": [], "custom_field": "value"}
    client.post("/resume/save", json=resume_payload, headers=headers)
    response = client.get("/resume", headers=headers)
    assert response.status_code == 200
    assert response.json()["resume"]["custom_field"] == "value"