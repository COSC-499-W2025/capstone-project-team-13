import os
import sys

from fastapi.testclient import TestClient

from src.mainAPI import app
from src.Databases.database import db_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

client = TestClient(app)


def setup_function():
	db_manager.clear_all_data()


def teardown_function():
	db_manager.clear_all_data()


def test_get_privacy_settings_returns_expected_keys():
    response = client.get("/configuration/privacy-settings")

    assert response.status_code == 200
    data = response.json()

    assert "anonymous_mode" in data
    assert "store_file_contents" in data
    assert "store_contributor_names" in data
    assert "store_file_paths" in data
    assert "max_file_size_scan" in data
    assert "excluded_folders" in data
    assert "excluded_file_types" in data


def test_patch_privacy_settings_updates_values():
	payload = {
		"anonymous_mode": True,
		"store_file_contents": False,
		"store_contributor_names": False,
		"store_file_paths": False,
		"max_file_size_scan": 123456,
	}

	response = client.patch("/configuration/privacy-settings", json=payload)

	assert response.status_code == 200
	data = response.json()
	assert data["success"] is True
	assert data["settings"]["anonymous_mode"] is True
	assert data["settings"]["store_file_contents"] is False
	assert data["settings"]["store_contributor_names"] is False
	assert data["settings"]["store_file_paths"] is False
	assert data["settings"]["max_file_size_scan"] == 123456


def test_patch_privacy_settings_persists_values():
	payload = {
		"anonymous_mode": True,
		"store_file_contents": False,
		"store_contributor_names": False,
		"store_file_paths": False,
		"max_file_size_scan": 654321,
	}

	patch_response = client.patch("/configuration/privacy-settings", json=payload)
	assert patch_response.status_code == 200

	get_response = client.get("/configuration/privacy-settings")
	assert get_response.status_code == 200
	data = get_response.json()

	assert data["anonymous_mode"] is True
	assert data["store_file_contents"] is False
	assert data["store_contributor_names"] is False
	assert data["store_file_paths"] is False
	assert data["max_file_size_scan"] == 654321


def test_add_and_remove_excluded_folder():
    folder_path = "node_modules"

    add_response = client.post(
        "/configuration/privacy-settings/excluded-folders",
        json={"folder_path": folder_path},
    )

    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data["success"] is True
    assert folder_path in add_data["excluded_folders"]

    remove_response = client.request(
        "DELETE",
        "/configuration/privacy-settings/excluded-folders",
        json={"folder_path": folder_path},
    )

    assert remove_response.status_code == 200
    remove_data = remove_response.json()
    assert remove_data["success"] is True
    assert folder_path not in remove_data["excluded_folders"]


def test_add_and_remove_excluded_file_type():
    file_type = ".log"

    add_response = client.post(
        "/configuration/privacy-settings/excluded-file-types",
        json={"file_type": file_type},
    )

    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data["success"] is True
    assert file_type in add_data["excluded_file_types"]

    remove_response = client.request(
        "DELETE",
        "/configuration/privacy-settings/excluded-file-types",
        json={"file_type": file_type},
    )

    assert remove_response.status_code == 200
    remove_data = remove_response.json()
    assert remove_data["success"] is True
    assert file_type not in remove_data["excluded_file_types"]


def test_add_excluded_folder_empty_path_returns_400():
	response = client.post(
		"/configuration/privacy-settings/excluded-folders",
		json={"folder_path": ""},
	)

	assert response.status_code == 400


def test_add_excluded_file_type_empty_value_returns_400():
	response = client.post(
		"/configuration/privacy-settings/excluded-file-types",
		json={"file_type": ""},
	)

	assert response.status_code == 400
