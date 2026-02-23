import os
import sys

from fastapi.testclient import TestClient

from src.mainAPI import app

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

client = TestClient(app)


# Test: get basic consent status

def test_get_basic_consent_status():
    response = client.get("/consent/basic-consent-status")

    assert response.status_code == 200
    data = response.json()
    assert "basic_consent_granted" in data
    assert "basic_consent_timestamp" in data


# Test: get ai consent status

def test_get_ai_consent_status():
    response = client.get("/consent/ai-consent-status")

    assert response.status_code == 200
    data = response.json()
    assert "ai_consent_granted" in data
    assert "ai_consent_timestamp" in data


# Test: grant basic consent

def test_grant_basic_consent():
    response = client.post("/consent/basic-consent-grant")

    assert response.status_code == 200
    data = response.json()
    assert data["basic_consent_granted"] is True


# Test: revoke basic consent

def test_revoke_basic_consent():
    response = client.post("/consent/basic-consent-revoke")

    assert response.status_code == 200
    data = response.json()
    assert data["basic_consent_granted"] is False


# Test: grant ai consent

def test_grant_ai_consent():
    response = client.post("/consent/ai-consent-grant")

    assert response.status_code == 200
    data = response.json()
    assert data["ai_consent_granted"] is True


# Test: revoke ai consent

def test_revoke_ai_consent():
    response = client.post("/consent/ai-consent-revoke")

    assert response.status_code == 200
    data = response.json()
    assert data["ai_consent_granted"] is False