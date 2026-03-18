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
    resp = client.post("/auth/signup", json={
        "first_name": "Test", "last_name": "User",
        "email": email, "password": "password123"
    })
    assert resp.status_code == 200
    return resp.json()["user"]["id"], {"Authorization": f"Bearer {resp.json()['token']}"}


EDU_PAYLOAD = {
    "institution": "UBCO",
    "degree_type": "Bachelor's",
    "topic": "Computer Science",
    "start_date": "2021-09-01",
    "end_date": "2025-05-01",
    "location": "Kelowna, BC",
    "gpa": "3.8",
    "details": ["Dean's List", "Algorithms, OS"],
}

WORK_PAYLOAD = {
    "company": "Acme Corp",
    "role": "Software Engineer Intern",
    "start_date": "2024-05-01",
    "end_date": "2024-08-01",
    "location": "Vancouver, BC",
    "bullets": ["Built feature X", "Improved performance by 20%"],
}


# ── education auth ────────────────────────────────────────────────────────────

def test_get_education_requires_auth():
    assert client.get("/education").status_code == 401

def test_add_education_requires_auth():
    assert client.post("/education", json=EDU_PAYLOAD).status_code == 401

def test_delete_education_requires_auth():
    assert client.delete("/education/1").status_code == 401


# ── education CRUD ────────────────────────────────────────────────────────────

def test_get_education_empty():
    _, headers = _create_user()
    resp = client.get("/education", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["education"] == []

def test_add_education_success():
    _, headers = _create_user()
    resp = client.post("/education", json=EDU_PAYLOAD, headers=headers)
    assert resp.status_code == 200
    edu = resp.json()["education"]
    assert edu["institution"] == "UBCO"
    assert edu["location"] == "Kelowna, BC"
    assert edu["gpa"] == "3.8"
    assert "Dean's List" in edu["details"]

def test_add_education_persists():
    _, headers = _create_user()
    client.post("/education", json=EDU_PAYLOAD, headers=headers)
    resp = client.get("/education", headers=headers)
    assert len(resp.json()["education"]) == 1

def test_delete_education_success():
    _, headers = _create_user()
    edu_id = client.post("/education", json=EDU_PAYLOAD, headers=headers).json()["education"]["id"]
    resp = client.delete(f"/education/{edu_id}", headers=headers)
    assert resp.status_code == 200
    assert client.get("/education", headers=headers).json()["education"] == []

def test_delete_education_wrong_user():
    user_a_id, _ = _create_user("a@example.com")
    _, headers_b = _create_user("b@example.com")
    edu_id = client.post("/education", json=EDU_PAYLOAD,
                         headers={"Authorization": f"Bearer {client.post('/auth/login', json={'email': 'a@example.com', 'password': 'password123'}).json()['token']}"}).json()["education"]["id"]
    assert client.delete(f"/education/{edu_id}", headers=headers_b).status_code == 404

def test_add_education_invalid_date():
    _, headers = _create_user()
    bad = {**EDU_PAYLOAD, "start_date": "not-a-date"}
    assert client.post("/education", json=bad, headers=headers).status_code == 422


# ── work history auth ─────────────────────────────────────────────────────────

def test_get_work_history_requires_auth():
    assert client.get("/work-history").status_code == 401

def test_add_work_history_requires_auth():
    assert client.post("/work-history", json=WORK_PAYLOAD).status_code == 401

def test_delete_work_history_requires_auth():
    assert client.delete("/work-history/1").status_code == 401


# ── work history CRUD ─────────────────────────────────────────────────────────

def test_get_work_history_empty():
    _, headers = _create_user()
    resp = client.get("/work-history", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["work_history"] == []

def test_add_work_history_success():
    _, headers = _create_user()
    resp = client.post("/work-history", json=WORK_PAYLOAD, headers=headers)
    assert resp.status_code == 200
    work = resp.json()["work_history"]
    assert work["company"] == "Acme Corp"
    assert work["location"] == "Vancouver, BC"
    assert "Built feature X" in work["bullets"]

def test_add_work_history_persists():
    _, headers = _create_user()
    client.post("/work-history", json=WORK_PAYLOAD, headers=headers)
    resp = client.get("/work-history", headers=headers)
    assert len(resp.json()["work_history"]) == 1

def test_delete_work_history_success():
    _, headers = _create_user()
    work_id = client.post("/work-history", json=WORK_PAYLOAD, headers=headers).json()["work_history"]["id"]
    resp = client.delete(f"/work-history/{work_id}", headers=headers)
    assert resp.status_code == 200
    assert client.get("/work-history", headers=headers).json()["work_history"] == []

def test_delete_work_history_wrong_user():
    _, headers_a = _create_user("a@example.com")
    _, headers_b = _create_user("b@example.com")
    work_id = client.post("/work-history", json=WORK_PAYLOAD, headers=headers_a).json()["work_history"]["id"]
    assert client.delete(f"/work-history/{work_id}", headers=headers_b).status_code == 404

def test_add_work_history_invalid_date():
    _, headers = _create_user()
    bad = {**WORK_PAYLOAD, "start_date": "not-a-date"}
    assert client.post("/work-history", json=bad, headers=headers).status_code == 422