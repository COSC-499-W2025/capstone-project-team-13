import io
import os
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.mainAPI import app

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

client = TestClient(app)


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


