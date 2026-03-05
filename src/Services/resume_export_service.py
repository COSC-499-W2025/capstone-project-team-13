"""
src/Services/resume_export_service.py
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

    has_bullets = {p.id for p in get_projects_with_bullets()}
    resume_projects = []
    for project in all_projects:
        if project.id in has_bullets:
            bd     = db_manager.get_resume_bullets(project.id) or {}
            header = _clean_header(bd.get("header", ""), project.name)
            bullets, ats = bd.get("bullets", []), bd.get("ats_score")
        else:
            header, bullets, ats = project.name, [], None
        resume_projects.append({"name": project.name, "header": header,
                                 "bullets": bullets, "ats_score": ats})

    return {"name": f"{user.first_name} {user.last_name}", "email": user.email,
            "education": [e.to_dict() for e in education], "awards": awards,
            "skills_by_level": skills_by_level, "projects": resume_projects}


# ── PDF builder ───────────────────────────────────────────────────────────────

def _build_pdf(data: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.6*inch,  bottomMargin=0.6*inch)
    base = getSampleStyleSheet()
    G    = colors.HexColor(_GREEN)

    def S(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    s_name  = S("PName", fontSize=22, fontName="Times-Bold",
                alignment=TA_CENTER, leading=28, spaceAfter=6, textColor=G)
    s_role  = S("PRole", fontSize=11, fontName="Times-Italic",
                alignment=TA_CENTER, leading=16, spaceAfter=6)
    s_cont  = S("PCont", fontSize=9, alignment=TA_CENTER, leading=14,
                textColor=colors.HexColor("#444444"), spaceAfter=10)
    s_sect  = S("PSect", fontSize=11, fontName="Times-Bold",
                alignment=TA_CENTER, spaceBefore=10, spaceAfter=2, textColor=G)
    s_body  = S("PBody", fontSize=9.5, spaceAfter=2, leading=14)
    s_bold  = S("PBold", fontSize=9.5, fontName="Helvetica-Bold", spaceAfter=0, leading=13)
    s_ital  = S("PItal", fontSize=9.5, fontName="Times-Italic", spaceAfter=2, leading=13)
    s_right = S("PRight", fontSize=9.5, alignment=TA_RIGHT, leading=13)
    s_nobul = S("PNoBul", fontSize=9, fontName="Times-Italic",
                textColor=colors.HexColor("#888888"), spaceAfter=2, leading=13)

    def HR(t=0.5, c=None):
        return HRFlowable(width="100%", thickness=t, color=c or colors.HexColor("#aaaaaa"))

    def section(title):
        return [Spacer(1, 6), HR(), Paragraph(title, s_sect), HR(), Spacer(1, 4)]

    story = [Paragraph(data["name"], s_name)]
    role = _role_line(data["education"])
    if role:
        story.append(Paragraph(role, s_role))
    story += [Paragraph(data["email"], s_cont), HR(0.75, colors.HexColor("#cccccc"))]

    story += section("Education")
    for edu in data["education"]:
        start = (edu.get("start_date") or "")[:7].replace("-", "/")
        end   = (edu.get("end_date") or "")[:7].replace("-", "/") or "Present"
        tbl = Table([[Paragraph(f"{edu.get('degree_type','')} in {edu.get('topic','')}", s_bold),
                      Paragraph(f"{start} - {end}", s_right)]],
                    colWidths=["70%", "30%"])
        tbl.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                 ("LEFTPADDING",(0,0),(-1,-1),0),
                                 ("RIGHTPADDING",(0,0),(-1,-1),0),
                                 ("TOPPADDING",(0,0),(-1,-1),0),
                                 ("BOTTOMPADDING",(0,0),(-1,-1),2)]))
        story += [tbl, Paragraph(edu.get("institution",""), s_ital), Spacer(1, 6)]
    for award in data["awards"]:
        story.append(Paragraph(f"  {award}", s_body))
    if not data["education"] and not data["awards"]:
        story.append(Paragraph("No education or awards on record.", s_body))

    story += section("Skills")
    has_skills = False
    for level, items in data["skills_by_level"].items():
        if items:
            story.append(Paragraph(
                f'<font name="Helvetica-Bold">{level} — </font>{" | ".join(items)}', s_body))
            has_skills = True
    if not has_skills:
        story.append(Paragraph("No skills extracted yet.", s_body))

    story += section("Projects")
    for proj in data["projects"]:
        story.append(Paragraph(proj["name"], s_bold))
        if proj["header"] and proj["header"] != proj["name"]:
            story.append(Paragraph(proj["header"], s_ital))
        if proj["bullets"]:
            story.append(Paragraph("  ".join(proj["bullets"]), s_body))
        else:
            story.append(Paragraph(
                "No bullets generated yet. Use the CLI Resume menu to generate them.", s_nobul))
        if proj.get("ats_score"):
            story.append(Paragraph(
                f'<font color="#888888" size="7.5">ATS score: {proj["ats_score"]:.0f}/100</font>',
                s_body))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buf.getvalue()


# ── DOCX builder ──────────────────────────────────────────────────────────────

def _build_docx(data: dict[str, Any]) -> bytes:
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = sec.bottom_margin = Pt(36)
        sec.left_margin = sec.right_margin = Pt(50)

    G = RGBColor(0x2D, 0x6A, 0x4F)

    def para(text="", bold=False, italic=False, size=10,
             align=WD_ALIGN_PARAGRAPH.LEFT, color=None, space_after=4):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after  = Pt(space_after)
        p.paragraph_format.space_before = Pt(0)
        if text:
            r = p.add_run(text)
            r.bold, r.italic, r.font.size = bold, italic, Pt(size)
            r.font.color.rgb = color or RGBColor(0x22, 0x22, 0x22)
        return p

    def hr(color_hex="aaaaaa"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = p.paragraph_format.space_before = Pt(0)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bot  = OxmlElement("w:bottom")
        for k, v in [("w:val","single"),("w:sz","4"),("w:space","1"),("w:color",color_hex)]:
            bot.set(qn(k), v)
        pBdr.append(bot)
        pPr.append(pBdr)

    def section_heading(title):
        hr(); para(title, bold=True, size=11,
                   align=WD_ALIGN_PARAGRAPH.CENTER, color=G, space_after=2); hr()

    para(data["name"], bold=True, size=20,
         align=WD_ALIGN_PARAGRAPH.CENTER, color=G, space_after=6)
    role = _role_line(data["education"])
    if role:
        para(role, italic=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    para(data["email"], size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
         color=RGBColor(0x44,0x44,0x44), space_after=8)
    hr("cccccc")

    section_heading("Education")
    for edu in data["education"]:
        start  = (edu.get("start_date") or "")[:7].replace("-", "/")
        end    = (edu.get("end_date") or "")[:7].replace("-", "/") or "Present"
        degree = f"{edu.get('degree_type','')} in {edu.get('topic','')}"
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
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
    for award in data["awards"]:
        para(f"  {award}", size=9.5, space_after=3)
    if not data["education"] and not data["awards"]:
        para("No education or awards on record.", size=9.5)

    section_heading("Skills")
    has_skills = False
    for level, items in data["skills_by_level"].items():
        if items:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.space_before = Pt(0)
            r1 = p.add_run(f"{level} — "); r1.bold = True; r1.font.size = Pt(9.5)
            p.add_run(" | ".join(items)).font.size = Pt(9.5)
            has_skills = True
    if not has_skills:
        para("No skills extracted yet.", size=9.5)

    section_heading("Projects")
    for proj in data["projects"]:
        para(proj["name"], bold=True, size=9.5, space_after=1)
        if proj["header"] and proj["header"] != proj["name"]:
            para(proj["header"], italic=True, size=9.5, space_after=2)
        if proj["bullets"]:
            para("  ".join(proj["bullets"]), size=9.5, space_after=2)
        else:
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
            r = p.add_run("No bullets generated yet. Use the CLI Resume menu to generate them.")
            r.italic = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x88,0x88,0x88)
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