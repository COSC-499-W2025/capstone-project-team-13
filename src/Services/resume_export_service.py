"""
Thin export layer — PDF and DOCX rendering only.
Data is gathered via existing modules:
  - src.Resume.resumeGenerator       : get_projects_with_bullets()
  - src.Portfolio.portfolioFormatter : PortfolioFormatter._infer_skills()
  - src.Databases.database           : db_manager
Deps: pip install reportlab python-docx
"""
from __future__ import annotations
import io, re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.Databases.database import db_manager
from src.Resume.resumeGenerator import get_projects_with_bullets
from src.Portfolio.portfolioFormatter import PortfolioFormatter
from src.UserPrompts.config_integration import has_ai_consent

_UUID_RE = re.compile(r"^[0-9a-f\-]{36}$", re.IGNORECASE)
_GREEN   = "#2d6a4f"


# ── helpers ───────────────────────────────────────────────────────────────────

def _skill_level(count: int) -> str:
    if count >= 5: return "Expert"
    if count >= 2: return "Proficient"
    return "Familiar"

def _clean_header(raw: str, fallback: str) -> str:
    if " | " in raw:
        parts = raw.split(" | ", 1)
        if _UUID_RE.match(parts[0].strip()):
            return parts[1]
    return raw or fallback

def _role_line(education: list) -> str:
    if not education:
        return ""
    e = education[0]
    return f"{e.get('degree_type','')} in {e.get('topic','')}".strip(" in")


def _try_generate_ai_bullets(project) -> list[str]:
    """
    Attempt to generate AI resume bullets for a project and save them.
    Returns the generated bullets, or [] if AI is unavailable or fails.
    Called only when has_ai_consent() is True and the project has no stored bullets.
    """
    try:
        from src.AI.ai_enhanced_summarizer import generate_resume_bullets
        from src.Resume.resumeAnalytics import score_all_bullets

        # Build a project dict matching what generate_resume_bullets expects
        project_dict = {
            "project_name": project.name,
            "skills": [s.strip() for s in (project.skills or "").split(",") if s.strip()]
                      if isinstance(project.skills, str)
                      else (project.skills or []),
            "file_count": project.file_count,
            "lines_of_code": project.lines_of_code,
            "success_score": getattr(project, "importance_score", 0) or 0,
            "contribution_score": getattr(project, "contribution_score", 0) or 0,
        }

        bullets = generate_resume_bullets(project_dict, num_bullets=3)
        if not bullets:
            return []

        # Persist so subsequent loads don't regenerate
        scoring = score_all_bullets(bullets, project.project_type)
        db_manager.save_resume_bullets(
            project_id=project.id,
            bullets=bullets,
            header=project.name,
            ats_score=scoring["overall_score"],
        )
        return bullets

    except Exception:
        return []


# ── data gathering ────────────────────────────────────────────────────────────

def get_resume_preview_data(user_id: int) -> dict[str, Any]:
    """Assemble resume data using existing helpers. Returns plain dict."""
    user = db_manager.get_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    education = db_manager.get_education_for_user(user_id)
    awards: list[str] = (user.resume or {}).get("awards", [])

    formatter    = PortfolioFormatter()
    all_projects = db_manager.get_all_projects()

    skill_counts: dict[str, int] = {}
    for p in all_projects:
        for skill in formatter._infer_skills(p):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    skills_by_level: dict[str, list[str]] = {"Expert": [], "Proficient": [], "Familiar": []}
    for skill, count in sorted(skill_counts.items()):
        skills_by_level[_skill_level(count)].append(skill)

    ai_enabled = has_ai_consent()
    has_bullets = {p.id for p in get_projects_with_bullets()}
    resume_projects = []

    for project in all_projects:
        if project.id in has_bullets:
            bd     = db_manager.get_resume_bullets(project.id) or {}
            header = _clean_header(bd.get("header", ""), project.name)
            bullets = bd.get("bullets", [])
            ats     = bd.get("ats_score")
        else:
            header = project.name
            ats    = None
            # Auto-generate AI bullets if consent is granted
            if ai_enabled:
                bullets = _try_generate_ai_bullets(project)
            else:
                bullets = []

        resume_projects.append({
            "name":      project.name,
            "header":    header,
            "bullets":   bullets,
            "ats_score": ats,
        })

    return {
        "name":           f"{user.first_name} {user.last_name}",
        "email":          user.email,
        "education":      [e.to_dict() for e in education],
        "awards":         awards,
        "skills_by_level": skills_by_level,
        "projects":       resume_projects,
    }


# ── PDF builder ───────────────────────────────────────────────────────────────

def _build_pdf(data: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    styles = getSampleStyleSheet()

    GREEN = colors.HexColor(_GREEN)

    name_style = ParagraphStyle("name", fontSize=22, textColor=GREEN,
                                alignment=TA_CENTER, fontName="Times-Bold",
                                spaceAfter=2)
    role_style = ParagraphStyle("role", fontSize=11, textColor=colors.HexColor("#555555"),
                                alignment=TA_CENTER, fontName="Times-Italic",
                                spaceAfter=4)
    contact_style = ParagraphStyle("contact", fontSize=8, textColor=colors.HexColor("#555555"),
                                   alignment=TA_CENTER, spaceAfter=8)
    section_style = ParagraphStyle("section", fontSize=10, textColor=GREEN,
                                   fontName="Times-Bold", alignment=TA_CENTER,
                                   spaceBefore=4, spaceAfter=2)
    body_style = ParagraphStyle("body", fontSize=9, leading=13, spaceAfter=2)
    label_style = ParagraphStyle("label", fontSize=9, fontName="Times-Bold",
                                 spaceAfter=1)
    italic_style = ParagraphStyle("italic", fontSize=8.5, fontName="Times-Italic",
                                  textColor=colors.HexColor("#555555"), spaceAfter=2)
    muted_style = ParagraphStyle("muted", fontSize=7.5,
                                 textColor=colors.HexColor("#888888"), spaceAfter=4)

    def rule():
        return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#b7c9bf"),
                          spaceAfter=0, spaceBefore=0)

    def section_block(title):
        return [rule(), Paragraph(title, section_style), rule()]

    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch)
    story = []

    # Header
    story.append(Paragraph(data.get("name", ""), name_style))
    role = _role_line(data.get("education", []))
    if role:
        story.append(Paragraph(role, role_style))
    if data.get("email"):
        story.append(Paragraph(data["email"], contact_style))
    story.append(rule())

    # Education & Awards
    story += section_block("Education and Awards")
    for edu in data.get("education", []):
        start = (edu.get("start_date") or "")[:7].replace("-", "/")
        end   = (edu.get("end_date") or "")[:7].replace("-", "/") or "Present"
        degree = f"{edu.get('degree_type','')} in {edu.get('topic','')}".strip()
        row = [[Paragraph(degree, label_style),
                Paragraph(f"{start} – {end}", ParagraphStyle("r", fontSize=9,
                          alignment=TA_RIGHT, textColor=colors.HexColor("#555555")))]]
        t = Table(row, colWidths=[4.5*inch, 2.5*inch])
        t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "BOTTOM"),
                               ("BOTTOMPADDING", (0,0), (-1,-1), 0)]))
        story.append(t)
        story.append(Paragraph(edu.get("institution",""), italic_style))
    for award in data.get("awards", []):
        story.append(Paragraph(f"\u2014 {award}", body_style))
    if not data.get("education") and not data.get("awards"):
        story.append(Paragraph("No education or awards on record.", italic_style))

    # Skills
    story += section_block("Skills")
    has_skills = False
    for level, items in data.get("skills_by_level", {}).items():
        if items:
            story.append(Paragraph(f"<b>{level}:</b> {', '.join(items)}", body_style))
            has_skills = True
    if not has_skills:
        story.append(Paragraph("No skills extracted yet.", italic_style))

    # Projects
    story += section_block("Projects")
    for proj in data.get("projects", []):
        story.append(Paragraph(proj["name"], label_style))
        if proj.get("header") and proj["header"] != proj["name"]:
            story.append(Paragraph(proj["header"], italic_style))
        if proj.get("bullets"):
            for b in proj["bullets"]:
                story.append(Paragraph(f"\u2022 {b}", body_style))
        else:
            story.append(Paragraph("No bullets generated yet.", italic_style))
        if proj.get("ats_score"):
            story.append(Paragraph(f"ATS score: {proj['ats_score']:.0f}/100", muted_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()


# ── DOCX builder ──────────────────────────────────────────────────────────────

def _build_docx(data: dict[str, Any]) -> bytes:
    doc = Document()

    # Narrow margins
    for section in doc.sections:
        section.top_margin    = Pt(43)
        section.bottom_margin = Pt(43)
        section.left_margin   = Pt(54)
        section.right_margin  = Pt(54)

    def para(text, bold=False, italic=False, size=10, align=None,
             color=None, space_after=4):
        p = doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(space_after)
        p.paragraph_format.space_before = Pt(0)
        if align:
            p.alignment = align
        r = p.add_run(text)
        r.bold   = bold
        r.italic = italic
        r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor(*bytes.fromhex(color.lstrip("#")))
        return p

    def section_heading(title):
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
        p = doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title)
        r.bold = True; r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(0x2d, 0x6a, 0x4f)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # Name / contact
    para(data.get("name",""), bold=True, size=20,
         align=WD_ALIGN_PARAGRAPH.CENTER, color=_GREEN, space_after=2)
    role = _role_line(data.get("education", []))
    if role:
        para(role, italic=True, size=11,
             align=WD_ALIGN_PARAGRAPH.CENTER, color="#555555", space_after=4)
    if data.get("email"):
        para(data["email"], size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER, color="#555555", space_after=8)

    section_heading("Education and Awards")
    for edu in data.get("education", []):
        start  = (edu.get("start_date") or "")[:7].replace("-", "/")
        end    = (edu.get("end_date") or "")[:7].replace("-", "/") or "Present"
        degree = f"{edu.get('degree_type','')} in {edu.get('topic','')}"
        p = doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(0)
        p.paragraph_format.space_before = Pt(4)
        r1 = p.add_run(degree); r1.bold = True; r1.font.size = Pt(9.5)
        p.add_run("\t")
        r2 = p.add_run(f"{start} - {end}")
        r2.font.size = Pt(9.5); r2.font.color.rgb = RGBColor(0x44,0x44,0x44)
        pPr = p._p.get_or_add_pPr()
        tabs = OxmlElement("w:tabs"); tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right"); tab.set(qn("w:pos"), "8640")
        tabs.append(tab); pPr.append(tabs)
        para(edu.get("institution",""), italic=True, size=9.5, space_after=6)
    for award in data.get("awards", []):
        para(f"  {award}", size=9.5, space_after=3)
    if not data.get("education") and not data.get("awards"):
        para("No education or awards on record.", italic=True, size=9.5)

    section_heading("Skills")
    has_skills = False
    for level, items in data.get("skills_by_level", {}).items():
        if items:
            p = doc.add_paragraph()
            p.paragraph_format.space_after  = Pt(3)
            p.paragraph_format.space_before = Pt(0)
            r1 = p.add_run(f"{level} — "); r1.bold = True; r1.font.size = Pt(9.5)
            p.add_run(" | ".join(items)).font.size = Pt(9.5)
            has_skills = True
    if not has_skills:
        para("No skills extracted yet.", italic=True, size=9.5)

    section_heading("Projects")
    for proj in data.get("projects", []):
        para(proj["name"], bold=True, size=9.5, space_after=1)
        if proj.get("header") and proj["header"] != proj["name"]:
            para(proj["header"], italic=True, size=9.5, space_after=2)
        if proj.get("bullets"):
            para("  ".join(proj["bullets"]), size=9.5, space_after=2)
        else:
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
            r = p.add_run("No bullets generated yet.")
            r.italic = True; r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x88,0x88,0x88)
        if proj.get("ats_score"):
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
            r = p.add_run(f"ATS score: {proj['ats_score']:.0f}/100")
            r.font.size = Pt(7.5); r.font.color.rgb = RGBColor(0x88,0x88,0x88)
        else:
            doc.add_paragraph().paragraph_format.space_after = Pt(6)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── public API ────────────────────────────────────────────────────────────────

def generate_resume_pdf(user_id: int) -> bytes:
    return _build_pdf(get_resume_preview_data(user_id))

def generate_resume_docx(user_id: int) -> bytes:
    return _build_docx(get_resume_preview_data(user_id))