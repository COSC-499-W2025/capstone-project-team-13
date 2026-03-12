"""
tests/test_api_ai_analyze.py
============================
Tests for POST /projects/{project_id}/analyze

Run with:
    pytest tests/test_api_ai_analyze.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Build a minimal app with just the projects router
from src.Routers.projects import router

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)

_ROUTER_PATH = "src.Routers.projects"


def _make_project(project_id=1, user_id=None, ai_description=None):
    p = MagicMock()
    p.id = project_id
    p.user_id = user_id
    p.ai_description = ai_description
    p.to_dict.return_value = {
        "id": project_id,
        "name": "Test Project",
        "ai_description": ai_description,
    }
    return p


class TestAnalyzeEndpointNoConsent:
    """Endpoint must return 403 when AI consent is not granted."""

    @patch(f"{_ROUTER_PATH}.has_ai_consent", return_value=False)
    def test_returns_403_when_no_ai_consent(self, _mock):
        response = client.post("/projects/1/analyze")
        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()


class TestAnalyzeEndpointWithConsent:
    """Happy-path and error cases when AI consent IS granted."""

    @patch(f"{_ROUTER_PATH}.has_ai_consent", return_value=True)
    @patch(f"{_ROUTER_PATH}.db_manager")
    def test_returns_404_for_missing_project(self, mock_db, _consent):
        mock_db.get_project.return_value = None
        response = client.post("/projects/999/analyze")
        assert response.status_code == 404

    @patch(f"{_ROUTER_PATH}.has_ai_consent", return_value=True)
    @patch("src.AI.ai_project_analyzer.AIProjectAnalyzer")
    @patch(f"{_ROUTER_PATH}.db_manager")
    def test_returns_200_with_ai_description(self, mock_db, MockAnalyzer, _consent):
        project = _make_project(project_id=1)
        mock_db.get_project.return_value = project

        analyzer_instance = MockAnalyzer.return_value
        analyzer_instance.analyze_project_complete.return_value = {
            "overview": "A Python CLI tool for data analysis.",
        }
        analyzer_instance.update_database_with_analysis.return_value = True

        updated = _make_project(project_id=1, ai_description="A Python CLI tool for data analysis.")
        mock_db.get_project.side_effect = [project, updated]

        response = client.post("/projects/1/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AI analysis complete"
        assert "Python" in data["ai_description"]

    @patch(f"{_ROUTER_PATH}.has_ai_consent", return_value=True)
    @patch("src.AI.ai_project_analyzer.AIProjectAnalyzer")
    @patch(f"{_ROUTER_PATH}.db_manager")
    def test_returns_500_when_analyzer_errors(self, mock_db, MockAnalyzer, _consent):
        mock_db.get_project.return_value = _make_project()

        analyzer_instance = MockAnalyzer.return_value
        analyzer_instance.analyze_project_complete.return_value = {
            "error": "API quota exceeded"
        }

        response = client.post("/projects/1/analyze")
        assert response.status_code == 500
        assert "quota" in response.json()["detail"].lower()

    @patch(f"{_ROUTER_PATH}.has_ai_consent", return_value=True)
    @patch("src.AI.ai_project_analyzer.AIProjectAnalyzer")
    @patch(f"{_ROUTER_PATH}.db_manager")
    def test_returns_500_on_unexpected_exception(self, mock_db, MockAnalyzer, _consent):
        mock_db.get_project.return_value = _make_project()
        MockAnalyzer.side_effect = RuntimeError("Unexpected failure")

        response = client.post("/projects/1/analyze")
        assert response.status_code == 500
