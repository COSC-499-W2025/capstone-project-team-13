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


def test_get_analysis_preferences_returns_expected_keys():
    response = client.get("/configuration/analysis-preferences")

    assert response.status_code == 200
    data = response.json()

    assert "enable_keyword_extraction" in data
    assert "enable_language_detection" in data
    assert "enable_framework_detection" in data
    assert "enable_collaboration_analysis" in data
    assert "enable_duplicate_detection" in data


def test_patch_analysis_preferences_updates_values():
    payload = {
        "enable_keyword_extraction": False,
        "enable_language_detection": False,
        "enable_framework_detection": True,
        "enable_collaboration_analysis": True,
        "enable_duplicate_detection": False,
    }

    response = client.patch("/configuration/analysis-preferences", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["preferences"]["enable_keyword_extraction"] is False
    assert data["preferences"]["enable_language_detection"] is False
    assert data["preferences"]["enable_framework_detection"] is True
    assert data["preferences"]["enable_collaboration_analysis"] is True
    assert data["preferences"]["enable_duplicate_detection"] is False


def test_patch_analysis_preferences_persists_values():
    payload = {
        "enable_keyword_extraction": True,
        "enable_language_detection": False,
        "enable_framework_detection": False,
        "enable_collaboration_analysis": True,
        "enable_duplicate_detection": True,
    }

    patch_response = client.patch("/configuration/analysis-preferences", json=payload)
    assert patch_response.status_code == 200

    get_response = client.get("/configuration/analysis-preferences")
    assert get_response.status_code == 200
    data = get_response.json()

    assert data["enable_keyword_extraction"] is True
    assert data["enable_language_detection"] is False
    assert data["enable_framework_detection"] is False
    assert data["enable_collaboration_analysis"] is True
    assert data["enable_duplicate_detection"] is True


def test_enable_all_analysis_features_sets_all_true():
    response = client.post("/configuration/analysis-preferences/enable-all")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["preferences"]["enable_keyword_extraction"] is True
    assert data["preferences"]["enable_language_detection"] is True
    assert data["preferences"]["enable_framework_detection"] is True
    assert data["preferences"]["enable_collaboration_analysis"] is True
    assert data["preferences"]["enable_duplicate_detection"] is True


def test_disable_all_analysis_features_sets_all_false():
    response = client.post("/configuration/analysis-preferences/disable-all")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["preferences"]["enable_keyword_extraction"] is False
    assert data["preferences"]["enable_language_detection"] is False
    assert data["preferences"]["enable_framework_detection"] is False
    assert data["preferences"]["enable_collaboration_analysis"] is False
    assert data["preferences"]["enable_duplicate_detection"] is False
