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


def test_get_current_configuration_returns_expected_sections():
    response = client.get("/configuration/current-configuration")

    assert response.status_code == 200
    data = response.json()

    assert "consent" in data
    assert "privacy_settings" in data
    assert "analysis_preferences" in data
    assert "scanning_preferences" in data
    assert "ai_settings" in data
    assert "output_preferences" in data
    assert "ui_preferences" in data
    assert "performance_settings" in data
    assert "notification_settings" in data
    assert "backup_settings" in data
    assert "meta" in data


def test_get_current_configuration_reflects_privacy_updates():
    update_payload = {
        "anonymous_mode": True,
        "store_file_contents": False,
        "store_contributor_names": False,
        "store_file_paths": False,
        "max_file_size_scan": 444444,
    }
    patch_response = client.patch("/configuration/privacy-settings", json=update_payload)
    assert patch_response.status_code == 200

    response = client.get("/configuration/current-configuration")
    assert response.status_code == 200

    data = response.json()
    privacy = data["privacy_settings"]

    assert privacy["anonymous_mode"] is True
    assert privacy["store_file_contents"] is False
    assert privacy["store_contributor_names"] is False
    assert privacy["store_file_paths"] is False
    assert privacy["max_file_size_scan"] == 444444


def test_get_current_configuration_reflects_analysis_updates():
    update_payload = {
        "enable_keyword_extraction": False,
        "enable_language_detection": False,
        "enable_framework_detection": True,
        "enable_collaboration_analysis": False,
        "enable_duplicate_detection": True,
    }
    patch_response = client.patch("/configuration/analysis-preferences", json=update_payload)
    assert patch_response.status_code == 200

    response = client.get("/configuration/current-configuration")
    assert response.status_code == 200

    data = response.json()
    preferences = data["analysis_preferences"]

    assert preferences["enable_keyword_extraction"] is False
    assert preferences["enable_language_detection"] is False
    assert preferences["enable_framework_detection"] is True
    assert preferences["enable_collaboration_analysis"] is False
    assert preferences["enable_duplicate_detection"] is True


def test_get_current_configuration_reflects_consent_updates():
    grant_basic_response = client.post("/consent/basic-consent-grant")
    assert grant_basic_response.status_code == 200

    grant_ai_response = client.post("/consent/ai-consent-grant")
    assert grant_ai_response.status_code == 200

    response = client.get("/configuration/current-configuration")
    assert response.status_code == 200

    data = response.json()
    consent = data["consent"]

    assert consent["basic_consent_granted"] is True
    assert consent["ai_consent_granted"] is True
    assert consent["basic_consent_timestamp"] is not None
    assert consent["ai_consent_timestamp"] is not None
