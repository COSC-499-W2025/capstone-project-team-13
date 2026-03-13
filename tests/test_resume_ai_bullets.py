"""
tests/test_resume_ai_bullets.py
================================
Tests that get_resume_preview_data auto-generates AI bullets
when AI consent is granted and a project has no stored bullets.
"""

import pytest
from unittest.mock import patch, MagicMock

_P = "src.Services.resume_export_service"


def make_user():
    u = MagicMock()
    u.first_name = "Jane"
    u.last_name  = "Doe"
    u.email      = "jane@example.com"
    u.resume     = {}
    return u


def make_project(pid=1, name="Test Project", project_type="code"):
    p = MagicMock()
    p.id           = pid
    p.name         = name
    p.project_type = project_type
    p.skills       = "python,fastapi"
    p.file_count   = 10
    p.lines_of_code = 300
    p.importance_score   = 0.8
    p.contribution_score = 0.7
    return p


def _base_patches(mock_db, mock_gwb, mock_pf,
                  projects=None, ai_consent=False):
    """Wire up the three mocks that every test needs."""
    mock_db.get_user.return_value     = make_user()
    mock_db.get_education_for_user.return_value = []
    mock_db.get_all_projects.return_value = projects or [make_project()]
    mock_db.get_resume_bullets.return_value = None   # no stored bullets
    mock_gwb.return_value = []                        # no projects with bullets yet
    mock_pf.return_value._infer_skills.return_value = []


class TestAiBulletsAutoGeneration:

    @patch(f"{_P}.has_ai_consent", return_value=True)
    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_ai_bullets_called_when_consent_granted_and_no_stored_bullets(
        self, mock_db, mock_gwb, mock_pf, _consent
    ):
        """When AI consent is on and no bullets exist, _try_generate_ai_bullets is called."""
        _base_patches(mock_db, mock_gwb, mock_pf, ai_consent=True)

        with patch(f"{_P}._try_generate_ai_bullets",
                   return_value=["Built REST API", "Wrote tests"]) as mock_gen:
            from src.Services.resume_export_service import get_resume_preview_data
            data = get_resume_preview_data(1)

        mock_gen.assert_called_once()
        assert data["projects"][0]["bullets"] == ["Built REST API", "Wrote tests"]

    @patch(f"{_P}.has_ai_consent", return_value=False)
    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_ai_bullets_not_called_without_consent(
        self, mock_db, mock_gwb, mock_pf, _consent
    ):
        """When AI consent is off, bullets stay empty and AI is never called."""
        _base_patches(mock_db, mock_gwb, mock_pf, ai_consent=False)

        with patch(f"{_P}._try_generate_ai_bullets") as mock_gen:
            from src.Services.resume_export_service import get_resume_preview_data
            data = get_resume_preview_data(1)

        mock_gen.assert_not_called()
        assert data["projects"][0]["bullets"] == []

    @patch(f"{_P}.has_ai_consent", return_value=True)
    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_stored_bullets_are_not_overwritten(
        self, mock_db, mock_gwb, mock_pf, _consent
    ):
        """Projects that already have stored bullets are never re-generated."""
        proj = make_project()
        _base_patches(mock_db, mock_gwb, mock_pf, projects=[proj], ai_consent=True)

        # Mark project as already having bullets
        mock_gwb.return_value = [proj]
        mock_db.get_resume_bullets.return_value = {
            "bullets": ["Existing bullet"],
            "header":  "Test Project",
            "ats_score": 75,
        }

        with patch(f"{_P}._try_generate_ai_bullets") as mock_gen:
            from src.Services.resume_export_service import get_resume_preview_data
            data = get_resume_preview_data(1)

        mock_gen.assert_not_called()
        assert data["projects"][0]["bullets"] == ["Existing bullet"]

    @patch(f"{_P}.has_ai_consent", return_value=True)
    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_ai_failure_falls_back_to_empty_bullets(
        self, mock_db, mock_gwb, mock_pf, _consent
    ):
        """If AI generation throws, bullets are empty and no exception propagates."""
        _base_patches(mock_db, mock_gwb, mock_pf, ai_consent=True)

        with patch(f"{_P}._try_generate_ai_bullets", return_value=[]):
            from src.Services.resume_export_service import get_resume_preview_data
            data = get_resume_preview_data(1)

        assert data["projects"][0]["bullets"] == []
        # Resume data is still returned correctly
        assert data["name"] == "Jane Doe"
