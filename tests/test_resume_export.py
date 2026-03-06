"""tests/test_resume_export.py -- Run with: pytest tests/test_resume_export.py -v"""
import io, json, pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── factories ─────────────────────────────────────────────────────────────────
def make_user(uid=1, first="Jane", last="Doe", email="jane@test.com", resume=None):
    u = MagicMock()
    u.id, u.first_name, u.last_name, u.email, u.resume = uid, first, last, email, resume
    return u

def make_edu():
    e = MagicMock()
    e.to_dict.return_value = {"institution":"UBCO","degree_type":"Bachelor's",
                               "topic":"CS","start_date":"2020-09-01","end_date":None}
    return e

def make_project(pid=1, name="Capstone", ptype="code"):
    p = MagicMock()
    p.id, p.name, p.project_type = pid, name, ptype
    p.skills, p.languages, p.frameworks = ["Python","FastAPI"], ["Python"], ["FastAPI"]
    return p

def make_bullets():
    return {"header":"Capstone | Python, FastAPI",
            "bullets":["Built REST API with 50+ endpoints","Reduced latency by 40%"],
            "ats_score":82.0,"num_bullets":2,"generated_at":"2025-01-01T00:00:00"}

def minimal_data():
    return {"name":"Jane Doe","email":"jane@test.com",
            "education":[{"institution":"UBCO","degree_type":"Bachelor's",
                           "topic":"CS","start_date":"2020-09-01","end_date":None}],
            "awards":["Dean's List"],
            "skills_by_level":{"Expert":["Python"],"Proficient":["FastAPI"],"Familiar":["Docker"]},
            "projects":[{"name":"Capstone","header":"Capstone | Python",
                          "bullets":["Built REST API"],"ats_score":80.0}]}

def _setup(mock_db, mock_gwb, mock_pf, projects=None, bullets=None, edu=None, user=None):
    projs = projects or [make_project()]
    mock_db.get_user.return_value = user or make_user()
    mock_db.get_education_for_user.return_value = edu if edu is not None else [make_edu()]
    mock_db.get_all_projects.return_value = projs
    mock_db.get_resume_bullets.return_value = bullets if bullets is not None else make_bullets()
    mock_gwb.return_value = projs
    mock_pf.return_value._infer_skills.return_value = ["Python", "FastAPI"]

_P = "src.Services.resume_export_service"
_R = "src.Routers.resumes"

# ── get_resume_preview_data ───────────────────────────────────────────────────
class TestGetResumePreviewData:
    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_raises_if_user_not_found(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        mock_db.get_user.return_value = None
        with pytest.raises(ValueError, match="not found"): get_resume_preview_data(99)

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_returns_expected_keys(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        _setup(mock_db, mock_gwb, mock_pf)
        data = get_resume_preview_data(1)
        for key in ("name","email","education","awards","skills_by_level","projects"):
            assert key in data

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_all_projects_included_not_just_bullet_ones(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        pw, pwo = make_project(pid=1,name="Has Bullets"), make_project(pid=2,name="No Bullets")
        _setup(mock_db, mock_gwb, mock_pf, projects=[pw,pwo], bullets=None, edu=[])
        mock_db.get_resume_bullets.side_effect = lambda pid: make_bullets() if pid == 1 else None
        mock_gwb.return_value = [pw]
        mock_pf.return_value._infer_skills.return_value = []
        names = [p["name"] for p in get_resume_preview_data(1)["projects"]]
        assert "Has Bullets" in names and "No Bullets" in names

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_uuid_stripped_from_header(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        bd = make_bullets(); bd["header"] = "da0a6f20-f07d-4b47-bfd7-332685f5a351 | Image Editor"
        _setup(mock_db, mock_gwb, mock_pf, projects=[make_project(pid=1,name="Image Editor")],
               bullets=bd, edu=[])
        mock_pf.return_value._infer_skills.return_value = []
        assert get_resume_preview_data(1)["projects"][0]["header"] == "Image Editor"

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.get_projects_with_bullets")
    @patch(f"{_P}.db_manager")
    def test_awards_from_user_resume_blob(self, mock_db, mock_gwb, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        _setup(mock_db, mock_gwb, mock_pf,
               user=make_user(resume={"awards":["Dean's List","Best Project"]}),
               projects=[], edu=[])
        mock_gwb.return_value = []; mock_pf.return_value._infer_skills.return_value = []
        assert "Dean's List" in get_resume_preview_data(1)["awards"]

# ── file generation smoke tests ───────────────────────────────────────────────
class TestFileGeneration:
    def test_pdf_produces_valid_bytes(self):
        from src.Services.resume_export_service import _build_pdf
        b = _build_pdf(minimal_data())
        assert isinstance(b,bytes) and len(b)>1000 and b[:4]==b"%PDF"

    def test_docx_produces_valid_bytes(self):
        from src.Services.resume_export_service import _build_docx
        b = _build_docx(minimal_data())
        assert isinstance(b,bytes) and len(b)>1000 and b[:2]==b"PK"

    def test_pdf_handles_empty_sections(self):
        from src.Services.resume_export_service import _build_pdf
        d = minimal_data()
        d.update(education=[],awards=[],projects=[],skills_by_level={"Expert":[],"Proficient":[],"Familiar":[]})
        assert _build_pdf(d)[:4] == b"%PDF"

    def test_docx_handles_empty_sections(self):
        from src.Services.resume_export_service import _build_docx
        d = minimal_data()
        d.update(education=[],awards=[],projects=[],skills_by_level={"Expert":[],"Proficient":[],"Familiar":[]})
        assert _build_docx(d)[:2] == b"PK"

# ── API endpoint tests ────────────────────────────────────────────────────────
@pytest.fixture()
def client():
    from src.Routers.resumes import router
    app = FastAPI(); app.include_router(router)
    return TestClient(app)

class TestResumeEndpoints:
    @patch(f"{_R}.db_manager")
    def test_get_resume_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.get("/resume/99").status_code == 404

    @patch(f"{_R}.db_manager")
    def test_get_resume_not_generated_yet(self, mock_db, client):
        mock_db.get_user.return_value = make_user()
        r = client.get("/resume/1")
        assert r.status_code == 404 and "generate" in r.json()["detail"].lower()

    @patch(f"{_R}.db_manager")
    def test_get_resume_success(self, mock_db, client):
        mock_db.get_user.return_value = make_user(resume={"name":"Jane Doe"})
        r = client.get("/resume/1")
        assert r.status_code == 200 and r.json()["user_id"] == 1

    @patch(f"{_R}.get_resume_preview_data")
    @patch(f"{_R}.db_manager")
    def test_generate_success(self, mock_db, mock_preview, client):
        mock_db.get_user.return_value = make_user(); mock_db.update_user.return_value = None
        mock_preview.return_value = minimal_data()
        r = client.post("/resume/generate?user_id=1")
        assert r.status_code == 200 and r.json()["message"] == "Resume generated"

    @patch(f"{_R}.db_manager")
    def test_generate_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.post("/resume/generate?user_id=99").status_code == 404

    @patch(f"{_R}.get_resume_preview_data")
    @patch(f"{_R}.db_manager")
    def test_edit_awards(self, mock_db, mock_preview, client):
        mock_db.get_user.return_value = make_user(resume={}); mock_db.update_user.return_value = None
        mock_preview.return_value = minimal_data()
        r = client.post("/resume/1/edit", json={"awards":["Dean's List"]})
        assert r.status_code == 200 and "updated" in r.json()["message"]

    @patch(f"{_R}.db_manager")
    def test_edit_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.post("/resume/99/edit", json={}).status_code == 404

    @patch(f"{_R}.generate_resume_pdf")
    @patch(f"{_R}.db_manager")
    def test_pdf_download(self, mock_db, mock_gen, client):
        mock_db.get_user.return_value = make_user(); mock_gen.return_value = b"%PDF-1.4 fake"
        r = client.get("/resume/1/download/pdf")
        assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
        assert ".pdf" in r.headers["content-disposition"]

    @patch(f"{_R}.db_manager")
    def test_pdf_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.get("/resume/99/download/pdf").status_code == 404

    @patch(f"{_R}.generate_resume_pdf")
    @patch(f"{_R}.db_manager")
    def test_pdf_generation_error(self, mock_db, mock_gen, client):
        mock_db.get_user.return_value = make_user(); mock_gen.side_effect = Exception("render fail")
        assert client.get("/resume/1/download/pdf").status_code == 500

    @patch(f"{_R}.generate_resume_docx")
    @patch(f"{_R}.db_manager")
    def test_docx_download(self, mock_db, mock_gen, client):
        mock_db.get_user.return_value = make_user(); mock_gen.return_value = b"PK\x03\x04 fake"
        r = client.get("/resume/1/download/docx")
        assert r.status_code == 200 and "wordprocessingml" in r.headers["content-type"]
        assert ".docx" in r.headers["content-disposition"]

    @patch(f"{_R}.db_manager")
    def test_docx_user_not_found(self, mock_db, client):
        mock_db.get_user.return_value = None
        assert client.get("/resume/99/download/docx").status_code == 404

# ── section heading and awards regression ─────────────────────────────────────
class TestSectionHeadingAndAwards:
    def _pdf_text(self, pdf_bytes):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf_bytes)).pages)

    def test_pdf_section_heading_is_education_and_awards(self):
        from src.Services.resume_export_service import _build_pdf
        assert "Education and Awards" in self._pdf_text(_build_pdf(minimal_data()))

    def test_awards_appear_in_pdf(self):
        from src.Services.resume_export_service import _build_pdf
        d = minimal_data(); d["awards"] = ["Dean's List","Best Capstone Award"]
        text = self._pdf_text(_build_pdf(d))
        assert "Dean" in text and "Best Capstone" in text

    def test_awards_appear_in_docx(self):
        from src.Services.resume_export_service import _build_docx
        import zipfile
        d = minimal_data(); d["awards"] = ["Dean's List","Best Capstone Award"]
        with zipfile.ZipFile(io.BytesIO(_build_docx(d))) as zf:
            xml = zf.read("word/document.xml").decode("utf-8")
        assert "Dean" in xml and "Best Capstone" in xml

    @patch(f"{_R}.get_resume_preview_data")
    @patch(f"{_R}.db_manager")
    def test_edit_awards_appear_in_response(self, mock_db, mock_preview):
        from src.Routers.resumes import router
        expected = minimal_data(); expected["awards"] = ["Dean's List"]
        mock_db.get_user.return_value = make_user(resume={}); mock_db.update_user.return_value = None
        mock_preview.return_value = expected
        app = FastAPI(); app.include_router(router)
        r = TestClient(app).post("/resume/1/edit", json={"awards":["Dean's List"]})
        assert r.status_code == 200 and "Dean's List" in r.json()["resume"]["awards"]