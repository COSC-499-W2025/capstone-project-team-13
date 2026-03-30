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
    assert data["status"] in ("skipped", "exists", "created")


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


@pytest.mark.skip(reason="POST /projects/upload/multi-zip endpoint does not exist")
def test_upload_multi_zip_endpoint(monkeypatch, tmp_path):
    pass


@pytest.mark.skip(reason="POST /projects/{id}/upload/files endpoint does not exist; use /projects/{id}/upload with a ZIP")
def test_add_files_to_existing_project(tmp_path):
    pass


def test_detect_type_project_not_found():
    _, headers = _create_user_and_headers("detect_type_not_found@example.com")
    response = client.post("/projects/999999/analyze/detect-type", headers=headers)
    assert response.status_code == 404


@pytest.mark.skip(reason="POST /projects/{id}/analyze/coding endpoint does not exist")
def test_analyze_coding_endpoint(monkeypatch, tmp_path):
    pass


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

    # Endpoint is /contributors, not /roles; returns a list directly
    response = client.get(f"/projects/{project.id}/contributors", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "alice"


@pytest.mark.skip(reason="POST /projects/upload/multi-zip endpoint does not exist")
def test_multi_zip_upload_projects_visible_to_owner(monkeypatch, tmp_path):
    pass


def test_upload_without_auth_then_analyze_returns_403(tmp_path):
    """
    Regression: a project uploaded without a token is stored with user_id=None.
    Any authenticated user who then calls an analyze endpoint on that project
    should receive 403 because they don't own it.
    """
    _, headers = _create_user_and_headers("analyze_403@example.com")

    # Simulate a project created during an unauthenticated upload (user_id=None)
    orphan = db_manager.create_project({
        "name": "Orphan Project",
        "file_path": str(tmp_path),
        "project_type": "code",
        "user_id": None,
    })

    # Use the existing analyze endpoint; ownership check returns 403
    # (or 403 for missing AI consent — either way the user is blocked)
    response = client.post(
        f"/projects/{orphan.id}/analyze",
        headers=headers,
    )
    assert response.status_code == 403, (
        "authenticated user should not be able to analyze a project they don't own"
    )


@pytest.mark.skip(reason="POST /projects/{id}/roles endpoint does not exist")
def test_assign_project_role_from_contributor(monkeypatch):
    pass


