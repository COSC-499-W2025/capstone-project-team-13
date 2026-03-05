"""
Tests for resume_export_service and the /resume endpoints.

Run with:
    pytest tests/test_resume_export.py -v
"""

import io
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures / factories
# ─────────────────────────────────────────────────────────────────────────────

def make_user(uid=1, first="Jane", last="Doe", email="jane@test.com", resume=None):
    u = MagicMock()
    u.id         = uid
    u.first_name = first
    u.last_name  = last
    u.email      = email
    u.resume     = resume
    return u


def make_edu():
    e = MagicMock()
    e.to_dict.return_value = {
        "institution": "UBCO", "degree_type": "Bachelor's",
        "topic": "CS", "start_date": "2020-09-01", "end_date": None,
    }
    return e


def make_project(pid=1, name="Capstone", ptype="code"):
    p = MagicMock()
    p.id           = pid
    p.name         = name
    p.project_type = ptype
    p.skills       = ["Python", "FastAPI"]
    p.languages    = ["Python"]
    p.frameworks   = ["FastAPI"]
    return p


def make_bullets():
    return {
        "header": "Capstone | Python, FastAPI",
        "bullets": ["Built REST API with 50+ endpoints", "Reduced latency by 40%"],
        "ats_score": 82.0,
        "num_bullets": 2,
        "generated_at": "2025-01-01T00:00:00",
    }


def minimal_data():
    return {
        "name": "Jane Doe", "email": "jane@test.com",
        "education": [{"institution": "UBCO", "degree_type": "Bachelor's",
                        "topic": "CS", "start_date": "2020-09-01", "end_date": None}],
        "awards": ["Dean's List"],
        "skills_by_level": {"Expert": ["Python"], "Proficient": ["FastAPI"], "Familiar": ["Docker"]},
        "projects": [{"name": "Capstone", "header": "Capstone | Python",
                       "bullets": ["Built REST API"], "ats_score": 80.0}],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Unit: get_resume_preview_data  (all sub-calls mocked)
# ─────────────────────────────────────────────────────────────────────────────

class TestGetResumePreviewData:

    @patch("src.Services.resume_export_service.PortfolioFormatter")
    @patch("src.Services.resume_export_service.get_projects_with_bullets")
    @patch("src.Services.resume_export_service.db_manager")
    def test_raises_if_user_not_found(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        mock_db.get_user.return_value = None
        with pytest.raises(ValueError, match="not found"):
            get_resume_preview_data(99)

    @patch("src.Services.resume_export_service.PortfolioFormatter")
    @patch("src.Services.resume_export_service.get_projects_with_bullets")
    @patch("src.Services.resume_export_service.db_manager")
    def test_returns_expected_keys(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data

        mock_db.get_user.return_value      = make_user()
        mock_db.get_education_for_user.return_value = [make_edu()]
        mock_db.get_all_projects.return_value       = [make_project()]
        mock_db.get_resume_bullets.return_value     = make_bullets()
        mock_gwb.return_value = [make_project()]
        mock_pf.return_value._infer_skills.return_value = ["Python", "FastAPI"]

        data = get_resume_preview_data(1)
        assert "name"            in data
        assert "email"           in data
        assert "education"       in data
        assert "awards"          in data
        assert "skills_by_level" in data
        assert "projects"        in data

    @patch("src.Services.resume_export_service.PortfolioFormatter")
    @patch("src.Services.resume_export_service.get_projects_with_bullets")
    @patch("src.Services.resume_export_service.db_manager")
    def test_all_projects_included_not_just_bullet_ones(self, mock_db, mock_gwb, mock_pf):
        """Projects without bullets must still appear in the output."""
        from src.Services.resume_export_service import get_resume_preview_data

        proj_with    = make_project(pid=1, name="Has Bullets")
        proj_without = make_project(pid=2, name="No Bullets")

        mock_db.get_user.return_value      = make_user()
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value       = [proj_with, proj_without]
        mock_db.get_resume_bullets.side_effect = lambda pid: make_bullets() if pid == 1 else None
        mock_gwb.return_value = [proj_with]          # only proj 1 has bullets
        mock_pf.return_value._infer_skills.return_value = []

        data = get_resume_preview_data(1)
        names = [p["name"] for p in data["projects"]]
        assert "Has Bullets" in names
        assert "No Bullets"  in names

    @patch("src.Services.resume_export_service.PortfolioFormatter")
    @patch("src.Services.resume_export_service.get_projects_with_bullets")
    @patch("src.Services.resume_export_service.db_manager")
    def test_uuid_stripped_from_header(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data

        proj = make_project(pid=1, name="Image Editor")
        bd   = make_bullets()
        bd["header"] = "da0a6f20-f07d-4b47-bfd7-332685f5a351 | Image Editor"

        mock_db.get_user.return_value      = make_user()
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value       = [proj]
        mock_db.get_resume_bullets.return_value     = bd
        mock_gwb.return_value = [proj]
        mock_pf.return_value._infer_skills.return_value = []

        data = get_resume_preview_data(1)
        assert data["projects"][0]["header"] == "Image Editor"

    @patch("src.Services.resume_export_service.PortfolioFormatter")
    @patch("src.Services.resume_export_service.get_projects_with_bullets")
    @patch("src.Services.resume_export_service.db_manager")
    def test_awards_from_user_resume_blob(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data

        user = make_user(resume={"awards": ["Dean's List", "Best Project"]})
        mock_db.get_user.return_value      = user
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value       = []
        mock_gwb.return_value = []
        mock_pf.return_value._infer_skills.return_value = []

        data = get_resume_preview_data(1)
        assert "Dean's List" in data["awards"]


# ─────────────────────────────────────────────────────────────────────────────
# Unit: PDF / DOCX byte generation (smoke tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestFileGeneration:

    def test_pdf_produces_valid_bytes(self):
        from src.Services.resume_export_service import _build_pdf
        b = _build_pdf(minimal_data())
        assert isinstance(b, bytes) and len(b) > 1000
        assert b[:4] == b"%PDF"

    def test_docx_produces_valid_bytes(self):
        from src.Services.resume_export_service import _build_docx
        b = _build_docx(minimal_data())
        assert isinstance(b, bytes) and len(b) > 1000
        assert b[:2] == b"PK"   # DOCX is a ZIP

    def test_pdf_handles_empty_sections(self):
        from src.Services.resume_export_service import _build_pdf
        d = minimal_data()
        d.update(education=[], awards=[], projects=[],
                 skills_by_level={"Expert":[],"Proficient":[],"Familiar":[]})
        assert _build_pdf(d)[:4] == b"%PDF"

    def test_docx_handles_empty_sections(self):
        from src.Services.resume_export_service import _build_docx
        d = minimal_data()
        d.update(education=[], awards=[], projects=[],
                 skills_by_level={"Expert":[],"Proficient":[],"Familiar":[]})
        assert _build_docx(d)[:2] == b"PK"


# ─────────────────────────────────────────────────────────────────────────────
# API endpoint tests (TestClient — no real server)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    from src.Routers.resumes import router
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestResumeEndpoints:

    # GET /{user_id} ──────────────────────────────────────────────────────────

    @patch("src.Routers.resumes.db_manager")
    def test_get_resume_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.get("/resume/99").status_code == 404

    @patch("src.Routers.resumes.db_manager")
    def test_get_resume_not_generated_yet(self, mock_db, client):
        mock_db.get_user.return_value = make_user()
        r = client.get("/resume/1")
        assert r.status_code == 404
        assert "generate" in r.json()["detail"].lower()

    @patch("src.Routers.resumes.db_manager")
    def test_get_resume_success(self, mock_db, client):
        u = make_user(resume={"name": "Jane Doe"})
        mock_db.get_user.return_value = u
        r = client.get("/resume/1")
        assert r.status_code == 200
        assert r.json()["user_id"] == 1

    # POST /generate ──────────────────────────────────────────────────────────

    @patch("src.Routers.resumes.get_resume_preview_data")
    @patch("src.Routers.resumes.db_manager")
    def test_generate_success(self, mock_db, mock_preview, client):
        mock_db.get_user.return_value = make_user()
        mock_db.update_user.return_value = None
        mock_preview.return_value = minimal_data()
        r = client.post("/resume/generate?user_id=1")
        assert r.status_code == 200
        assert r.json()["message"] == "Resume generated"

    @patch("src.Routers.resumes.db_manager")
    def test_generate_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.post("/resume/generate?user_id=99").status_code == 404

    # POST /{user_id}/edit ────────────────────────────────────────────────────

    @patch("src.Routers.resumes.get_resume_preview_data")
    @patch("src.Routers.resumes.db_manager")
    def test_edit_awards(self, mock_db, mock_preview, client):
        u = make_user(resume={})
        mock_db.get_user.return_value  = u
        mock_db.update_user.return_value = None
        mock_preview.return_value = minimal_data()
        r = client.post("/resume/1/edit", json={"awards": ["Dean's List"]})
        assert r.status_code == 200
        assert "updated" in r.json()["message"]

    @patch("src.Routers.resumes.db_manager")
    def test_edit_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.post("/resume/99/edit", json={}).status_code == 404

    # GET /{user_id}/download/pdf ─────────────────────────────────────────────

    @patch("src.Routers.resumes.generate_resume_pdf")
    @patch("src.Routers.resumes.db_manager")
    def test_pdf_download(self, mock_db, mock_gen, client):
        mock_db.get_user.return_value = make_user()
        mock_gen.return_value = b"%PDF-1.4 fake"
        r = client.get("/resume/1/download/pdf")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert ".pdf" in r.headers["content-disposition"]

    @patch("src.Routers.resumes.db_manager")
    def test_pdf_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.get("/resume/99/download/pdf").status_code == 404

    @patch("src.Routers.resumes.generate_resume_pdf")
    @patch("src.Routers.resumes.db_manager")
    def test_pdf_generation_error(self, mock_db, mock_gen, client):
        mock_db.get_user.return_value = make_user()
        mock_gen.side_effect = Exception("render fail")
        assert client.get("/resume/1/download/pdf").status_code == 500

    # GET /{user_id}/download/docx ────────────────────────────────────────────

    @patch("src.Routers.resumes.generate_resume_docx")
    @patch("src.Routers.resumes.db_manager")
    def test_docx_download(self, mock_db, mock_gen, client):
        mock_db.get_user.return_value = make_user()
        mock_gen.return_value = b"PK\x03\x04 fake"
        r = client.get("/resume/1/download/docx")
        assert r.status_code == 200
        assert "wordprocessingml" in r.headers["content-type"]
        assert ".docx" in r.headers["content-disposition"]

    @patch("src.Routers.resumes.db_manager")
    def test_docx_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.get("/resume/99/download/docx").status_code == 404


class TestSectionHeadingAndAwards:

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract plain text from PDF bytes using pypdf."""
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def test_pdf_section_heading_is_education_and_awards(self):
        """Section must be titled 'Education and Awards', not just 'Education'."""
        from src.Services.resume_export_service import _build_pdf
        text = self._extract_pdf_text(_build_pdf(minimal_data()))
        assert "Education and Awards" in text

    def test_awards_appear_in_pdf(self):
        """Awards passed in data must appear in PDF output."""
        from src.Services.resume_export_service import _build_pdf
        d = minimal_data()
        d["awards"] = ["Dean's List", "Best Capstone Award"]
        text = self._extract_pdf_text(_build_pdf(d))
        assert "Dean" in text
        assert "Best Capstone" in text

    def test_awards_appear_in_docx(self):
        """Awards passed in data must appear in DOCX output."""
        from src.Services.resume_export_service import _build_docx
        import zipfile, io
        d = minimal_data()
        d["awards"] = ["Dean's List", "Best Capstone Award"]
        buf = io.BytesIO(_build_docx(d))
        with zipfile.ZipFile(buf) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert "Dean" in doc_xml
        assert "Best Capstone" in doc_xml

    @patch("src.Routers.resumes.get_resume_preview_data")
    @patch("src.Routers.resumes.db_manager")
    def test_edit_awards_appear_in_response(self, mock_db, mock_preview, client):
        """Saving awards must return resume data that contains those awards."""
        from src.Routers.resumes import router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        app = FastAPI()
        app.include_router(router)
        c = TestClient(app)

        expected = minimal_data()
        expected["awards"] = ["Dean's List"]
        mock_db.get_user.return_value    = make_user(resume={})
        mock_db.update_user.return_value = None
        mock_preview.return_value        = expected

        r = c.post("/resume/1/edit", json={"awards": ["Dean's List"]})
        assert r.status_code == 200
        assert "Dean's List" in r.json()["resume"]["awards"]