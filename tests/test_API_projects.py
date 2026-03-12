import io
import os
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.mainAPI import app
from src.Databases.database import db_manager
from src.Services.auth_service import create_access_token, hash_password

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

client = TestClient(app)


def _create_user_and_headers(email: str = "projects_test@example.com"):
    user = db_manager.create_user({
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password_hash": hash_password("password123"),
    })
    token = create_access_token(user.id)
    return user, {"Authorization": f"Bearer {token}"}


def setup_function():
    db_manager.clear_all_data()


def teardown_function():
    db_manager.clear_all_data()


# Helper: create a zip project

def create_test_zip(tmp_path: Path) -> Path:
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Multiple files = code project
    (project_dir / "main.py").write_text("print('hello world')")
    (project_dir / "utils.py").write_text("def helper(): pass")
    (project_dir / "README.md").write_text("# Test Project")

    zip_path = tmp_path / "test_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in project_dir.iterdir():
            zipf.write(file, arcname=file.name)

    return zip_path


# Test: upload ZIP project

def test_upload_project_zip(tmp_path):
    zip_path = create_test_zip(tmp_path)

    with open(zip_path, "rb") as f:
        response = client.post(
            "/projects/upload",
            files={"file": ("test_project.zip", f, "application/zip")}
        )

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ("created", "exists", "skipped")
    if data["status"] != "skipped":
        assert "project_id" in data


# Test: upload unsupported file

def test_upload_unsupported_file(tmp_path):
    fake_file = tmp_path / "random.txt"
    fake_file.write_text("just some text")

    with open(fake_file, "rb") as f:
        response = client.post(
            "/projects/upload",
            files={"file": ("random.txt", f, "text/plain")}
        )

    # Either skipped or rejected
    assert response.status_code in (200, 400)


# Test: list projects

def test_list_projects():
    response = client.get("/projects")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Test: get non-existent project

def test_get_project_not_found():
    response = client.get("/projects/999999")

    assert response.status_code == 404


# Test: invalid file type
def test_upload_non_zip_file():
    with open(__file__, "rb") as f:
        response = client.post(
            "/projects/upload",
            files={"file": ("not_a_zip.txt", f, "text/plain")}
        )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ("skipped", "exists")


# test: upload without file - fastapi should reject it

def test_upload_without_file():
    response = client.post("/projects/upload")
    assert response.status_code == 422


#test: empty zip

def test_upload_empty_zip(tmp_path):
    zip_path = tmp_path / "empty.zip"

    with zipfile.ZipFile(zip_path, "w"):
        pass

    with open(zip_path, "rb") as f:
        response = client.post(
            "/projects/upload",
            files={"file": ("empty.zip", f, "application/zip")}
        )

    assert response.status_code == 200
    assert response.json()["status"] in ("skipped", "exists")


def test_upload_multi_zip_endpoint(monkeypatch, tmp_path):
    user, headers = _create_user_and_headers("multi_zip@example.com")

    zip_path = tmp_path / "multi.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.writestr("a/main.py", "print('x')")

    monkeypatch.setattr(
        "src.Routers.projects.processZipFile",
        lambda path: [{"name": "a", "type": "code"}]
    )

    with open(zip_path, "rb") as f:
        response = client.post(
            "/projects/upload/multi-zip",
            files={"file": ("multi.zip", f, "application/zip")},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["count"] == 1


def test_add_files_to_existing_project(tmp_path):
    user, headers = _create_user_and_headers("add_files@example.com")

    project = db_manager.create_project({
        "name": "Upload Target",
        "file_path": "/tmp/upload-target",
        "project_type": "code",
        "file_count": 0,
        "user_id": user.id,
    })

    file_to_add = tmp_path / "new_file.py"
    file_to_add.write_text("print('new')")

    with open(file_to_add, "rb") as f:
        response = client.post(
            f"/projects/{project.id}/upload/files",
            files=[("files", ("new_file.py", f, "text/x-python"))],
            headers=headers,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "updated"
    assert payload["files_added"] == 1


def test_detect_type_project_not_found():
    _, headers = _create_user_and_headers("detect_type_not_found@example.com")
    response = client.post("/projects/999999/analyze/detect-type", headers=headers)
    assert response.status_code == 404


def test_analyze_coding_endpoint(monkeypatch, tmp_path):
    user, headers = _create_user_and_headers("analyze_coding@example.com")

    code_dir = tmp_path / "code_project"
    code_dir.mkdir()
    (code_dir / "main.py").write_text("print('hello')")

    project = db_manager.create_project({
        "name": "Analyzed Project",
        "file_path": str(code_dir),
        "project_type": "code",
        "user_id": user.id,
    })

    monkeypatch.setattr("src.Routers.projects.scan_coding_project", lambda path, user_id=None: project.id)

    response = client.post(f"/projects/{project.id}/analyze/coding", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["project_id"] == project.id


def test_analyze_coding_project_path_missing(monkeypatch):
    user, headers = _create_user_and_headers("analyze_missing@example.com")

    project = db_manager.create_project({
        "name": "Missing Path Project",
        "file_path": "/definitely/missing/path",
        "project_type": "code",
        "user_id": user.id,
    })

    response = client.post(f"/projects/{project.id}/analyze/coding", headers=headers)
    assert response.status_code == 404


def test_get_project_roles_returns_contributors():
    user, headers = _create_user_and_headers("roles_get@example.com")

    project = db_manager.create_project({
        "name": "Role Project",
        "file_path": "/tmp/role-project",
        "project_type": "code",
        "user_id": user.id,
    })
    db_manager.add_contributor_to_project({
        "project_id": project.id,
        "name": "alice",
        "contributor_identifier": "alice@example.com",
        "contribution_percent": 55.0,
        "commit_count": 10,
    })

    response = client.get(f"/projects/{project.id}/roles", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project.id
    assert len(data["contributors"]) == 1
    assert data["contributors"][0]["name"] == "alice"


def test_assign_project_role_from_contributor(monkeypatch):
    user, headers = _create_user_and_headers("roles_assign@example.com")

    project = db_manager.create_project({
        "name": "Role Assign Project",
        "file_path": "/tmp/role-assign-project",
        "project_type": "code",
        "user_id": user.id,
    })
    db_manager.add_contributor_to_project({
        "project_id": project.id,
        "name": "bob",
        "contributor_identifier": "bob@example.com",
        "contribution_percent": 60.0,
        "commit_count": 8,
    })

    monkeypatch.setattr("src.Routers.projects.identify_project_type", lambda path, project_data: "Collaborative Project")

    response = client.post(
        f"/projects/{project.id}/roles",
        json={
            "contributor": "bob",
            "role_type": "Backend Developer"
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["collaboration_type"] == "Collaborative Project"
    assert body["user_contribution_percent"] == 60.0
    assert "Backend Developer" in body["user_role"]


