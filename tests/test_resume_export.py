"""tests/test_resume_export.py -- Run with: pytest tests/test_resume_export.py -v"""
import io
import pytest
from unittest.mock import MagicMock, patch

_P = "src.Services.resume_export_service"


# ── factories ──────────────────────────────────────────────────────────────────

def make_user(uid=1, first="Jane", last="Doe", email="jane@test.com", resume=None):
    u = MagicMock()
    u.id, u.first_name, u.last_name, u.email, u.resume = uid, first, last, email, resume
    return u


def make_project(pid=1, name="Capstone", ptype="code", has_bullets=True):
    p = MagicMock()
    p.id, p.name, p.project_type = pid, name, ptype
    p.skills    = ["Python", "FastAPI"]
    p.languages = ["Python"]
    p.frameworks = ["FastAPI"]
    p.bullets   = {"header": "Capstone | Python"} if has_bullets else None
    p.custom_description = None
    return p


def make_bullets():
    return {
        "header":       "Capstone | Python, FastAPI",
        "bullets":      ["Built REST API with 50+ endpoints", "Reduced latency by 40%"],
        "ats_score":    82.0,
        "num_bullets":  2,
        "generated_at": "2025-01-01T00:00:00",
    }


def minimal_resume_data():
    """Minimal user.resume dict as stored by generate_full_resume."""
    return {
        "name":     "Jane Doe",
        "projects": [
            {
                "name":    "Capstone",
                "header":  "Capstone | Python",
                "bullets": ["Built REST API", "Reduced latency by 40%"],
                "ats_score": 80.0,
            }
        ],
        "generated_at": "2025-01-01T00:00:00",
    }


def enriched_resume_data():
    """Resume dict after the user has added optional sections via the frontend."""
    return {
        "name":     "Jane Doe",
        "email":    "jane@test.com",
        "phone":    "(250) 555-0101",
        "linkedin": "linkedin.com/in/janedoe",
        "github":   "github.com/janedoe",
        "education": [
            {
                "institution": "UBCO",
                "degree_type": "Bachelor's",
                "topic":       "Computer Science",
                "end_date":    "2025-05",
                "gpa":         "3.8",
                "location":    "Kelowna, BC",
                "details":     ["Courses: Algorithms, OS", "Honors: Dean's List"],
            }
        ],
        "awards": ["Dean's List", "Best Capstone Award"],
        "skills_by_level": {
            "Expert":     ["Python"],
            "Proficient": ["FastAPI"],
            "Familiar":   ["Docker"],
        },
        "work_history": [
            {
                "company":    "Acme Corp",
                "location":   "Vancouver, BC",
                "role":       "Software Engineering Intern",
                "start_date": "May 2024",
                "end_date":   "Aug 2024",
                "bullets":    ["Developed feature X", "Improved performance by 20%"],
            }
        ],
        "projects": [
            {
                "name":    "Capstone",
                "header":  "Capstone | Python",
                "bullets": ["Built REST API", "Reduced latency by 40%"],
                "date":    "Jan 2025",
            }
        ],
        "generated_at": "2025-01-01T00:00:00",
    }


# ── get_resume_preview_data ────────────────────────────────────────────────────

class TestGetResumePreviewData:

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.db_manager")
    def test_raises_if_user_not_found(self, mock_db, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        mock_db.get_user.return_value = None
        with pytest.raises(ValueError, match="not found"):
            get_resume_preview_data(99)

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.db_manager")
    def test_returns_expected_keys(self, mock_db, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        mock_db.get_user.return_value = make_user()
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value = []
        mock_pf.return_value._infer_skills.return_value = []
        data = get_resume_preview_data(1)
        for key in ("name", "email", "education", "awards", "skills_by_level", "projects"):
            assert key in data

    @patch(f"{_P}.has_ai_consent", return_value=False)
    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.db_manager")
    def test_all_projects_included_not_just_bullet_ones(self, mock_db, mock_pf, _consent):
        from src.Services.resume_export_service import get_resume_preview_data
        pw  = make_project(pid=1, name="Has Bullets",  has_bullets=True)
        pwo = make_project(pid=2, name="No Bullets",   has_bullets=False)
        mock_db.get_user.return_value = make_user()
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value = [pw, pwo]
        mock_db.get_resume_bullets.side_effect = lambda pid: make_bullets() if pid == 1 else None
        mock_pf.return_value._infer_skills.return_value = []
        names = [p["name"] for p in get_resume_preview_data(1)["projects"]]
        assert "Has Bullets" in names and "No Bullets" in names

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.db_manager")
    def test_uuid_stripped_from_header(self, mock_db, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        p  = make_project(pid=1, name="Image Editor", has_bullets=True)
        bd = make_bullets()
        bd["header"] = "da0a6f20-f07d-4b47-bfd7-332685f5a351 | Image Editor"
        mock_db.get_user.return_value = make_user()
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value = [p]
        mock_db.get_resume_bullets.return_value = bd
        mock_pf.return_value._infer_skills.return_value = []
        assert get_resume_preview_data(1)["projects"][0]["header"] == "Image Editor"

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.db_manager")
    def test_awards_from_user_resume_blob(self, mock_db, mock_pf):
        from src.Services.resume_export_service import get_resume_preview_data
        mock_db.get_user.return_value = make_user(resume={"awards": ["Dean's List", "Best Project"]})
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value = []
        mock_pf.return_value._infer_skills.return_value = []
        assert "Dean's List" in get_resume_preview_data(1)["awards"]

    @patch(f"{_P}.PortfolioFormatter")
    @patch(f"{_P}.db_manager")
    def test_projects_scoped_to_user(self, mock_db, mock_pf):
        """get_all_projects should always be called with user_id."""
        from src.Services.resume_export_service import get_resume_preview_data
        mock_db.get_user.return_value = make_user()
        mock_db.get_education_for_user.return_value = []
        mock_db.get_all_projects.return_value = []
        mock_pf.return_value._infer_skills.return_value = []
        get_resume_preview_data(1)
        mock_db.get_all_projects.assert_called_once_with(user_id=1)


# ── PDF builder ────────────────────────────────────────────────────────────────

class TestBuildPdf:

    def _pdf_bytes(self, data):
        from src.Services.resume_export_service import _build_pdf
        b, _ = _build_pdf(data)
        return b

    def test_minimal_resume_produces_valid_pdf(self):
        b = self._pdf_bytes(minimal_resume_data())
        assert isinstance(b, bytes) and b[:4] == b"%PDF"

    def test_enriched_resume_produces_valid_pdf(self):
        b = self._pdf_bytes(enriched_resume_data())
        assert isinstance(b, bytes) and b[:4] == b"%PDF"

    def test_empty_optional_sections_no_crash(self):
        d = minimal_resume_data()
        d.update(education=[], awards=[], work_history=[],
                 skills_by_level={"Expert": [], "Proficient": [], "Familiar": []})
        assert self._pdf_bytes(d)[:4] == b"%PDF"

    def test_no_ats_score_in_pdf(self):
        from PyPDF2 import PdfReader
        text = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(enriched_resume_data()))).pages
        )
        assert "ATS" not in text and "ats_score" not in text

    def test_name_appears_in_pdf(self):
        from PyPDF2 import PdfReader
        text = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(enriched_resume_data()))).pages
        )
        assert "Jane Doe" in text

    def test_education_section_only_when_present(self):
        from PyPDF2 import PdfReader
        # Without education
        d = minimal_resume_data()
        text_no_edu = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(d))).pages
        )
        assert "EDUCATION" not in text_no_edu
        # With education
        text_with_edu = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(enriched_resume_data()))).pages
        )
        assert "EDUCATION" in text_with_edu

    def test_awards_appear_in_pdf(self):
        from PyPDF2 import PdfReader
        d = enriched_resume_data()
        d["awards"] = ["Dean's List", "Best Capstone Award"]
        text = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(d))).pages
        )
        assert "Dean" in text and "Best Capstone" in text

    def test_skills_section_only_when_present(self):
        from PyPDF2 import PdfReader
        d = minimal_resume_data()
        text_no_skills = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(d))).pages
        )
        assert "TECHNICAL SKILLS" not in text_no_skills

    def test_project_bullets_appear_in_pdf(self):
        from PyPDF2 import PdfReader
        text = "\n".join(
            p.extract_text() or ""
            for p in PdfReader(io.BytesIO(self._pdf_bytes(minimal_resume_data()))).pages
        )
        assert "Built REST API" in text


# ── DOCX builder ───────────────────────────────────────────────────────────────

class TestBuildDocx:

    def _xml(self, data):
        from src.Services.resume_export_service import _build_docx
        import zipfile
        with zipfile.ZipFile(io.BytesIO(_build_docx(data))) as zf:
            return zf.read("word/document.xml").decode("utf-8")

    def test_minimal_resume_produces_valid_docx(self):
        from src.Services.resume_export_service import _build_docx
        b = _build_docx(minimal_resume_data())
        assert isinstance(b, bytes) and b[:2] == b"PK"

    def test_enriched_resume_produces_valid_docx(self):
        from src.Services.resume_export_service import _build_docx
        b = _build_docx(enriched_resume_data())
        assert isinstance(b, bytes) and b[:2] == b"PK"

    def test_empty_optional_sections_no_crash(self):
        from src.Services.resume_export_service import _build_docx
        d = minimal_resume_data()
        d.update(education=[], awards=[], work_history=[],
                 skills_by_level={"Expert": [], "Proficient": [], "Familiar": []})
        assert _build_docx(d)[:2] == b"PK"

    def test_no_ats_score_in_docx(self):
        xml = self._xml(enriched_resume_data())
        assert "ATS" not in xml and "ats_score" not in xml

    def test_name_appears_in_docx(self):
        assert "Jane Doe" in self._xml(enriched_resume_data())

    def test_awards_appear_in_docx(self):
        d = enriched_resume_data()
        d["awards"] = ["Dean's List", "Best Capstone Award"]
        xml = self._xml(d)
        assert "Dean" in xml and "Best Capstone" in xml

    def test_education_section_only_when_present(self):
        # Without education
        assert "EDUCATION" not in self._xml(minimal_resume_data())
        # With education
        assert "EDUCATION" in self._xml(enriched_resume_data())

    def test_skills_section_only_when_present(self):
        assert "TECHNICAL SKILLS" not in self._xml(minimal_resume_data())

    def test_project_bullets_appear_in_docx(self):
        assert "Built REST API" in self._xml(minimal_resume_data())

    def test_work_history_only_when_present(self):
        assert "RELEVANT EXPERIENCE" not in self._xml(minimal_resume_data())
        assert "RELEVANT EXPERIENCE" in self._xml(enriched_resume_data())


# ── generate_resume_pdf / generate_resume_docx public API ─────────────────────

class TestPublicExportApi:

    @patch(f"{_P}.db_manager")
    def test_pdf_raises_if_no_resume(self, mock_db):
        from src.Services.resume_export_service import generate_resume_pdf
        mock_db.get_resume_by_id.return_value = None
        with pytest.raises(ValueError, match="No resume found"):
            generate_resume_pdf(1, 1)

    @patch(f"{_P}.db_manager")
    def test_docx_raises_if_no_resume(self, mock_db):
        from src.Services.resume_export_service import generate_resume_docx
        mock_db.get_resume_by_id.return_value = None
        with pytest.raises(ValueError, match="No resume found"):
            generate_resume_docx(1, 1)

    @patch(f"{_P}.db_manager")
    def test_pdf_raises_if_user_not_found(self, mock_db):
        from src.Services.resume_export_service import generate_resume_pdf
        mock_db.get_resume_by_id.return_value = None
        with pytest.raises(ValueError, match="No resume found"):
            generate_resume_pdf(99, 99)

    @patch(f"{_P}.db_manager")
    def test_pdf_uses_stored_resume_not_preview_data(self, mock_db):
        """generate_resume_pdf reads from get_resume_by_id, not user.resume."""
        from src.Services.resume_export_service import generate_resume_pdf
        mock_db.get_resume_by_id.return_value = {"resume_data": minimal_resume_data()}
        b = generate_resume_pdf(1, 1)
        assert b[:4] == b"%PDF"

    @patch(f"{_P}.db_manager")
    def test_docx_uses_stored_resume_not_preview_data(self, mock_db):
        from src.Services.resume_export_service import generate_resume_docx
        mock_db.get_resume_by_id.return_value = {"resume_data": minimal_resume_data()}
        b = generate_resume_docx(1, 1)
        assert b[:2] == b"PK"