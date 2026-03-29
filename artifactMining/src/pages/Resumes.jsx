import { Joyride } from 'react-joyride';
import React, { useEffect, useState, useRef, useMemo } from "react";
import confetti from "canvas-confetti";
import { toast } from "../components/Toast";
import "./Resumes.css";

const API_BASE = "http://127.0.0.1:8000";

// ── helpers ───────────────────────────────────────────────────────────────────

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function formatDateDisplay(iso) {
  if (!iso || iso === "Present") return "Present";
  // Strip timezone/time info, keep only YYYY-MM or YYYY-MM-DD
  const clean = iso.slice(0, 7); // "YYYY-MM"
  const [year, month] = clean.split("-").map(Number);
  if (!year || !month) return iso;
  const d = new Date(year, month - 1, 1);
  return d.toLocaleDateString("en-CA", { year: "numeric", month: "short" });
}

// Normalize a date value to "YYYY-MM" for storage (strips time/timezone)
function normalizeDate(val) {
  if (!val || val === "Present") return null;
  return val.slice(0, 7); // keep only "YYYY-MM"
}

function blankEducation() {
  return {
    _id: crypto.randomUUID(),
    _isNew: true,
    _endPresent: true,
    institution: "",
    degree_type: "",
    topic: "",
    start_date: "",
    end_date: null,
    location: "",
    gpa: "",
    details: [],
  };
}

function blankWorkHistory() {
  return {
    _id: crypto.randomUUID(),
    _isNew: true,
    _endPresent: true,
    company: "",
    role: "",
    start_date: "",
    end_date: null,
    location: "",
    bullets: [],
  };
}

// ── MonthPicker — dropdown calendar for year + month ─────────────────────────

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function MonthPicker({ value, onChange, placeholder = "Select date" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 60 }, (_, i) => currentYear - i);

  const parsed = value ? value.slice(0, 7).split("-") : [];
  const selYear = parsed[0] ? parseInt(parsed[0]) : null;
  const selMonth = parsed[1] ? parseInt(parsed[1]) : null;

  const [viewYear, setViewYear] = useState(selYear || currentYear);

  // Close on outside click
  useEffect(() => {
    function handle(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  function selectMonth(month) {
    onChange(`${viewYear}-${String(month).padStart(2, "0")}`);
    setOpen(false);
  }

  const displayVal = value
    ? (() => {
        const [y, m] = value.slice(0,7).split("-").map(Number);
        return `${MONTHS[m-1] || ""} ${y}`;
      })()
    : placeholder;

  return (
    <span className="month-picker-wrap" ref={ref}>
      <button
        type="button"
        className="month-picker-trigger r-inline-input"
        onClick={() => { setViewYear(selYear || currentYear); setOpen(o => !o); }}
      >
        {displayVal}
        <span className="month-picker-caret">▾</span>
      </button>
      {open && (
        <div className="month-picker-popup">
          <div className="month-picker-year-row">
            <button type="button" className="month-picker-nav" onClick={() => setViewYear(y => y - 1)}>‹</button>
            <select
              className="month-picker-year-select"
              value={viewYear}
              onChange={e => setViewYear(parseInt(e.target.value))}
            >
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
            <button type="button" className="month-picker-nav" onClick={() => setViewYear(y => y + 1)}>›</button>
          </div>
          <div className="month-picker-grid">
            {MONTHS.map((m, i) => (
              <button
                key={m}
                type="button"
                className={`month-picker-month${selYear === viewYear && selMonth === i + 1 ? " selected" : ""}`}
                onClick={() => selectMonth(i + 1)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      )}
    </span>
  );
}

// ── SkillInput — local raw string, parsed to array only on blur ───────────────

function SkillInput({ level, skills, onChange }) {
  const [raw, setRaw] = useState(skills.join(", "));

  // Sync if parent skills change (e.g. on refresh)
  useEffect(() => { setRaw(skills.join(", ")); }, [skills.join(",")]);

  return (
    <input
      className="r-inline-input r-skills-input"
      value={raw}
      onChange={e => setRaw(e.target.value)}
      onBlur={() => {
        const updated = raw.split(",").map(s => s.trim()).filter(Boolean);
        onChange(updated);
      }}
      placeholder="Skill 1, Skill 2, ..."
    />
  );
}

// ── sub-components ────────────────────────────────────────────────────────────

function InlineEdit({ value, onChange, editing, placeholder = "", className = "", multiline = false, style = {} }) {
  if (!editing) {
    return (
      <span className={className} style={style}>
        {value || <span className="r-placeholder">{placeholder}</span>}
      </span>
    );
  }
  if (multiline) {
    return (
      <textarea
        className={`r-inline-input r-inline-textarea ${className}`}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={style}
        rows={2}
      />
    );
  }
  return (
    <input
      className={`r-inline-input ${className}`}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={style}
    />
  );
}


function AtsTooltip() {
  const [open, setOpen] = useState(false);
  return (
    <span className="ats-tooltip-wrap">
      <button
        className="ats-help-btn"
        onClick={() => setOpen(o => !o)}
        title="How is the ATS score calculated?"
      >?</button>
      {open && (
        <div className="ats-tooltip-bubble">
          <strong>How ATS scores are calculated</strong>
          <ul>
            <li><strong>40 pts</strong> — Technical keywords matched to role-relevant terms</li>
            <li><strong>30 pts</strong> — Quantifiable metrics (numbers, %, $ amounts)</li>
            <li><strong>20 pts</strong> — Bullet length &amp; specificity</li>
            <li><strong>10 pts</strong> — Strong action verbs (e.g. "built", "reduced", "led")</li>
          </ul>
          <button className="ats-close-btn" onClick={() => setOpen(false)}>✕ Close</button>
        </div>
      )}
    </span>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export default function Resumes() {
  // Only run walkthrough if not seen
  const [runWalkthrough, setRunWalkthrough] = useState(() => {
    return localStorage.getItem('resumes_walkthrough_seen') !== '1';
  });
  // Set flag as soon as walkthrough starts
  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('resumes_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);
  const walkthroughSteps = [
    {
      target: 'body',
      placement: 'center',
      title: 'Resume Builder',
      content: 'This page lets you build, edit, and export your resume. Let’s take a quick tour!'
    },
    {
      target: '.resume-sidebar',
      placement: 'right',
      title: 'Resume Controls',
      content: 'Once you have projects, click Generate Resume and we will make one for you. In this panel, you can also add and remove elements.'
    },
    {
      target: '.resume-main',
      placement: 'left',
      title: 'Resume Preview',
      content: 'Once created, you can view and directly edit your resume here.'
    },
    {
      target: 'body',
      placement: 'center',
      title: 'Other Tools',
      content: 'Once generated, you can also track your completeness and word count as you go.'
    }
  ];
  // ── auth state — null = still checking, false = not authed, true = authed
  const [authed, setAuthed] = useState(null);

  // ── resume data (mirrors the JSON shape resume_export_service expects)
  const [resume, setResume] = useState(null);
  const [originalEdu, setOriginalEdu] = useState([]); // DB state at load time
  const [originalWork, setOriginalWork] = useState([]);

  // ── UI state
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [status, setStatus] = useState({ msg: "", type: "" });
  const [aiConsent, setAiConsent] = useState(false);

  // ── section visibility flags (which optional sections have been added)
  const [showEdu, setShowEdu] = useState(false);
  const [showWork, setShowWork] = useState(false);
  const [showSkills, setShowSkills] = useState(false);

  // ── export preview mode (hides UI-only elements so view matches export)
  const [previewMode, setPreviewMode] = useState(false);

  // ── page count (result of /resume/page-count check)
  const [pageCount, setPageCount] = useState(null);
  const [pageCountLoading, setPageCountLoading] = useState(false);

  // ── bullet count (2-5, passed to /resume/generate)
  const [numBullets, setNumBullets] = useState(3);

  // ── section order (keys: "projects" | "education" | "work_history" | "skills")
  const [sectionOrder, setSectionOrder] = useState(["projects"]);

  // ── drag state
  const dragSrc = useRef(null);
  const [dragOver, setDragOver] = useState(null);

  // ── section header labels (user-editable)
  const [sectionLabels, setSectionLabels] = useState({
    projects: "Projects",
    education: "Education",
    work_history: "Relevant Experience",
    skills: "Technical Skills",
  });

  // ── multi-resume list view state
  const [view, setView] = useState("list"); // "list" | "editor"
  const [resumeList, setResumeList] = useState([]);
  const [listLoading, setListLoading] = useState(false);
  const [activeResumeId, setActiveResumeId] = useState(null);
  const [activeResumeName, setActiveResumeName] = useState("");
  const [renamingCardId, setRenamingCardId] = useState(null);
  const [renameCardValue, setRenameCardValue] = useState("");

  // ── Validate token against backend on mount ──────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setAuthed(false);
      return;
    }
    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (res.ok) {
          setAuthed(true);
        } else {
          // Expired or invalid token — clear it so the user isn't stuck
          localStorage.removeItem("token");
          setAuthed(false);
        }
      })
      .catch(() => {
        // Network error — clear token and show auth wall to be safe
        localStorage.removeItem("token");
        setAuthed(false);
      });
  }, []);

  useEffect(() => {
    if (authed !== true) return;
    checkAiConsent();
    loadResumeList();
  }, [authed]);

  // Keep a ref in sync with resume so cleanup can read latest value
  const resumeRef = useRef(resume);
  useEffect(() => { resumeRef.current = resume; }, [resume]);

  // On unmount, clear resume_saved if no resume is loaded
  useEffect(() => {
    return () => {
      if (!resumeRef.current?.name?.trim()) {
        localStorage.removeItem("resume_saved");
        window.dispatchEvent(new Event("resume-updated"));
      }
    };
  }, []);

  // Ctrl+S to save
  useEffect(() => {
    function onKey(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        if (dirty && !loading) saveChanges();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // ── resume completeness score (0-100) ────────────────────────────────────────
  const completeness = useMemo(() => {
    if (!resume) return 0;
    let score = 0;

    // Contact info (up to 20pts)
    if (resume.name?.trim()) score += 8;
    if (resume.email?.trim()) score += 5;
    if (resume.phone?.trim()) score += 4;
    if (resume.linkedin?.trim() || resume.github?.trim()) score += 3;

    // Projects (up to 20pts — 3+ projects maxes it)
    const projects = resume.projects || [];
    score += Math.min(projects.length * 7, 20);

    // Education (up to 20pts — 1 entry maxes it)
    const edu = resume.education || [];
    score += Math.min(edu.length * 20, 20);

    // Work experience (up to 20pts — 2+ jobs maxes it)
    const work = resume.work_history || [];
    score += Math.min(work.length * 10, 20);

    // Skills (up to 20pts — 5+ skills maxes it)
    const allSkills = Object.values(resume.skills_by_level || {}).flat().filter(Boolean);
    score += Math.min(allSkills.length * 4, 20);

    return Math.min(Math.round(score), 100);
  }, [resume]);

  // ── word count + page estimate ────────────────────────────────────────────────
  const wordCount = useMemo(() => {
    if (!resume) return 0;
    const chunks = [
      resume.name, resume.email, resume.phone, resume.linkedin, resume.github,
      ...(resume.projects || []).flatMap(p => [p.name, ...(p.bullets || [])]),
      ...(resume.education || []).flatMap(e => [
        e.institution, e.degree_type, e.topic, ...(e.details || []),
      ]),
      ...(resume.work_history || []).flatMap(w => [w.company, w.role, ...(w.bullets || [])]),
      ...Object.values(resume.skills_by_level || {}).flat(),
      ...(resume.awards || []),
    ];
    return chunks.filter(Boolean).join(" ").split(/\s+/).filter(Boolean).length;
  }, [resume]);

  // 🎉 100% completeness celebration — fires once when bar first hits 100
  const prevCompleteness = useRef(0);
  useEffect(() => {
    if (completeness === 100 && prevCompleteness.current < 100) {
      // Side cannons
      const end = Date.now() + 1200;
      const colors = ["#a78bfa","#6366f1","#fbbf24","#34d399","#f472b6","#60a5fa"];
      (function frame() {
        confetti({ particleCount: 3, angle: 60,  spread: 50, origin: { x: 0 }, colors });
        confetti({ particleCount: 3, angle: 120, spread: 50, origin: { x: 1 }, colors });
        if (Date.now() < end) requestAnimationFrame(frame);
      })();
      // Central burst
      setTimeout(() => confetti({
        particleCount: 60, spread: 80, origin: { y: 0.6 },
        colors, startVelocity: 35, gravity: 0.9,
      }), 300);
      toast("🎉 Resume 100% complete!", "ok", 4000);
    }
    prevCompleteness.current = completeness;
  }, [completeness]);

  // ── helpers ──────────────────────────────────────────────────────────────────

  function showStatus(msg, type = "ok") {
    setStatus({ msg, type });
    setTimeout(() => setStatus({ msg: "", type: "" }), 4000);
  }

  function markDirty() { setDirty(true); }

  function setResumeField(path, value) {
    setResume(prev => {
      const next = { ...prev };
      const keys = path.split(".");
      let cur = next;
      for (let i = 0; i < keys.length - 1; i++) {
        cur[keys[i]] = { ...cur[keys[i]] };
        cur = cur[keys[i]];
      }
      cur[keys[keys.length - 1]] = value;
      return next;
    });
    markDirty();
  }

  // ── API calls ────────────────────────────────────────────────────────────────

  async function checkAiConsent() {
    try {
      const res = await fetch(`${API_BASE}/consent/ai-consent-status`);
      const data = await res.json();
      setAiConsent(Boolean(data.granted ?? data.ai_consent_granted ?? false));
    } catch { setAiConsent(false); }
  }

  // ── Multi-resume list management ─────────────────────────────────────────────

  async function loadResumeList() {
    setListLoading(true);
    try {
      const res = await fetch(`${API_BASE}/resume/list`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setResumeList(data.resumes || []);
      } else {
        setResumeList([]);
      }
    } catch {
      // If listing fails, just show empty
      setResumeList([]);
    } finally {
      setListLoading(false);
    }
  }

  async function openResume(id, name) {
    setActiveResumeId(id);
    setView("editor");
    await loadExisting(id);
  }

  async function handleNewResume() {
    try {
      const res = await fetch(`${API_BASE}/resume/create`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ name: "New Resume" }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const newId = data.resume?.id;
      if (!newId) throw new Error("No resume ID returned");
      setResume(null);
      setDirty(false);
      setEditing(false);
      setPageCount(null);
      setSectionOrder(["projects"]);
      setSectionLabels({ projects: "Projects", education: "Education", work_history: "Relevant Experience", skills: "Technical Skills" });
      setShowEdu(false);
      setShowWork(false);
      setShowSkills(false);
      setActiveResumeId(newId);
      setActiveResumeName("New Resume");
      setView("editor");
    } catch (e) {
      toast("Failed to create resume: " + e.message, "err");
    }
  }

  async function duplicateResume(id) {
    try {
      const res = await fetch(`${API_BASE}/resume/${id}/duplicate`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        toast("Resume duplicated!", "ok");
        await loadResumeList();
      } else {
        toast("Duplicate failed", "err");
      }
    } catch {
      toast("Duplicate failed", "err");
    }
  }

  async function deleteResumeFromList(id) {
    if (!window.confirm("Delete this resume?")) return;
    try {
      const res = await fetch(`${API_BASE}/resume/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (res.ok) {
        toast("Resume deleted", "ok");
        setResumeList(prev => prev.filter(r => r.id !== id));
      } else {
        toast("Delete failed", "err");
      }
    } catch {
      toast("Delete failed", "err");
    }
  }

  async function saveCardRename(id) {
    const name = renameCardValue.trim();
    if (!name) { setRenamingCardId(null); return; }
    try {
      const res = await fetch(`${API_BASE}/resume/${id}/rename`, {
        method: "PUT",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResumeList(prev => prev.map(r => r.id === id ? { ...r, name } : r));
      if (activeResumeId === id) setActiveResumeName(name);
    } catch (e) {
      toast("Rename failed: " + e.message, "err");
    } finally {
      setRenamingCardId(null);
    }
  }

  function renderList() {
    return (
      <div className="resume-list-container">
        <div className="resume-list-header">
          <div>
            <h2 className="resume-list-title">My Resumes</h2>
            <p className="resume-list-subtitle">Select a resume to edit or create a new one</p>
          </div>
        </div>

        {listLoading ? (
          <div className="resume-loader">Loading resumes...</div>
        ) : resumeList.length === 0 ? (
          <div className="resume-list-empty">
            <div className="resume-list-empty-icon">📄</div>
            <p className="resume-list-empty-title">No resumes yet</p>
            <p className="resume-list-empty-sub">Create your first resume to get started</p>
            <button className="resume-btn resume-btn-primary" onClick={handleNewResume}>
              Create Resume
            </button>
          </div>
        ) : (
          <div className="resume-list-grid">
            <div className="resume-new-card" onClick={handleNewResume}>
              <span className="resume-new-card-icon">+</span>
              <span className="resume-new-card-label">New Resume</span>
            </div>
            {resumeList.map(r => (
              <div key={r.id} className="resume-list-card" onClick={() => renamingCardId === r.id ? null : openResume(r.id, r.name)}>
                <div className="resume-card-accent" />
                <div className="resume-card-body">
                  <div className="resume-card-icon">📄</div>
                  <div className="resume-card-info">
                    {renamingCardId === r.id ? (
                      <input
                        className="resume-card-rename-input"
                        autoFocus
                        value={renameCardValue}
                        onChange={e => setRenameCardValue(e.target.value)}
                        onClick={e => e.stopPropagation()}
                        onKeyDown={e => { if (e.key === "Enter") saveCardRename(r.id); if (e.key === "Escape") setRenamingCardId(null); }}
                        onBlur={() => saveCardRename(r.id)}
                      />
                    ) : (
                      <div className="resume-card-name">{r.name}</div>
                    )}
                    <div className="resume-card-date">
                      {r.updated_at ? `Edited ${new Date(r.updated_at).toLocaleDateString("en-CA", { month: "short", day: "numeric", year: "numeric" })}` : "Not yet saved"}
                    </div>
                  </div>
                </div>
                <div className="resume-card-actions" onClick={e => e.stopPropagation()}>
                  <button
                    className="resume-card-icon-btn"
                    title="Rename"
                    onClick={() => { setRenamingCardId(r.id); setRenameCardValue(r.name); }}
                  >✏</button>
                  <button
                    className="resume-card-icon-btn"
                    title="Duplicate"
                    onClick={async () => { await duplicateResume(r.id); }}
                  >⧉</button>
                  <button
                    className="resume-card-icon-btn resume-card-icon-btn-danger"
                    title="Delete"
                    onClick={async () => { await deleteResumeFromList(r.id); }}
                  >🗑</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  async function loadExisting(resumeIdOverride) {
    const rid = resumeIdOverride ?? activeResumeId;
    if (!rid) return;
    setLoading(true);
    try {
      // Fetch resume JSON + education + work history in parallel
      const [resumeRes, eduRes, workRes] = await Promise.all([
        fetch(`${API_BASE}/resume?resume_id=${rid}`, { headers: authHeaders() }),
        fetch(`${API_BASE}/education`, { headers: authHeaders() }),
        fetch(`${API_BASE}/work-history`, { headers: authHeaders() }),
      ]);

      const eduData = eduRes.ok ? (await eduRes.json()).education || [] : [];
      const workData = workRes.ok ? (await workRes.json()).work_history || [] : [];

      // Tag existing DB entries with a stable _id for React keys
      const taggedEdu = eduData.map(e => ({ ...e, _id: String(e.id), _isNew: false, _endPresent: !e.end_date || e.end_date === "Present" }));
      const taggedWork = workData.map(w => ({ ...w, _id: String(w.id), _isNew: false, _endPresent: !w.end_date || w.end_date === "Present" }));

      setOriginalEdu(taggedEdu);
      setOriginalWork(taggedWork);

      if (resumeRes.ok) {
        const data = await resumeRes.json();
        const r = data.resume || data;
        if (r && r.name?.trim()) {
          localStorage.setItem("resume_saved", "1");
          window.dispatchEvent(new Event("resume-updated"));
          // Use only what's stored in the resume blob — never pre-populate
          // from the global DB (which spans all resumes and would bleed data).
          const resumeEdu = (r.education || []).map(e => ({ ...e, _id: e._id || String(e.id || ""), _isNew: false, _endPresent: !e.end_date || e.end_date === "Present" }));
          const resumeWork = (r.work_history || []).map(w => ({ ...w, _id: w._id || String(w.id || ""), _isNew: false, _endPresent: !w.end_date || w.end_date === "Present" }));
          applyResume({ ...r, education: resumeEdu, work_history: resumeWork });
          if (r.section_order) setSectionOrder(r.section_order);
          if (r.section_labels) setSectionLabels(prev => ({ ...prev, ...r.section_labels }));
          if (resumeEdu.length > 0) { setShowEdu(true); addSection("education"); }
          if (resumeWork.length > 0) { setShowWork(true); addSection("work_history"); }
          if (r.skills_by_level && Object.values(r.skills_by_level).some(v => v.length > 0)) {
            setShowSkills(true); addSection("skills");
          }
        }
      } else {
        // 404 = new empty resume — reset to a clean slate
        setResume(null);
        setSectionOrder(["projects"]);
        setSectionLabels({ projects: "Projects", education: "Education", work_history: "Relevant Experience", skills: "Technical Skills" });
        setShowEdu(false);
        setShowWork(false);
        setShowSkills(false);
        setDirty(false);
      }
    } catch (e) {
      showStatus("Failed to load resume data: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  function applyResume(data) {
    setResume({
      name: data.name || "",
      email: data.email || "",
      phone: data.phone || "",
      linkedin: data.linkedin || "",
      github: data.github || "",
      education: data.education || [],
      awards: data.awards || [],
      skills_by_level: data.skills_by_level || { Expert: [], Proficient: [], Familiar: [] },
      work_history: data.work_history || [],
      projects: data.projects || [],
    });
  }

  async function generateResume() {
    setLoading(true);
    try {
      if (!activeResumeId) { toast("No resume selected", "err"); return; }
      const res = await fetch(`${API_BASE}/resume/generate?resume_id=${activeResumeId}`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ num_bullets: numBullets }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const r = data.resume || data;

      // Re-fetch education + work from DB
      const [eduRes, workRes] = await Promise.all([
        fetch(`${API_BASE}/education`, { headers: authHeaders() }),
        fetch(`${API_BASE}/work-history`, { headers: authHeaders() }),
      ]);
      const eduData = eduRes.ok ? (await eduRes.json()).education || [] : [];
      const workData = workRes.ok ? (await workRes.json()).work_history || [] : [];
      const taggedEdu = eduData.map(e => ({ ...e, _id: String(e.id), _isNew: false, _endPresent: !e.end_date || e.end_date === "Present" }));
      const taggedWork = workData.map(w => ({ ...w, _id: String(w.id), _isNew: false, _endPresent: !w.end_date || w.end_date === "Present" }));

      setOriginalEdu(taggedEdu);
      setOriginalWork(taggedWork);
      const resumeEdu = (r.education || []).map(e => ({ ...e, _id: e._id || String(e.id || ""), _isNew: false, _endPresent: !e.end_date || e.end_date === "Present" }));
      const resumeWork = (r.work_history || []).map(w => ({ ...w, _id: w._id || String(w.id || ""), _isNew: false, _endPresent: !w.end_date || w.end_date === "Present" }));
      applyResume({ ...r, education: resumeEdu, work_history: resumeWork });

      // Reset section visibility to match refreshed data
      const hasSkills = r.skills_by_level && Object.values(r.skills_by_level).some(v => v.length > 0);
      setShowSkills(hasSkills);
      if (!hasSkills) setSectionOrder(prev => prev.filter(k => k !== "skills"));

      setDirty(false);
      showStatus("Resume generated.");
    } catch (e) {
      showStatus("Generation failed: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  async function addSkillsSection() {
    if (showSkills) return;
    try {
      const res = await fetch(`${API_BASE}/skills/`, { headers: authHeaders() });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // skills endpoint returns { skills: [ { name, projects, ... } ] } or similar
      const skillList = data.skills || data;

      // Categorize by project count using same thresholds as backend
      // (>=5 projects → Expert, >=2 → Proficient, else → Familiar)
      const byLevel = { Expert: [], Proficient: [], Familiar: [] };
      if (Array.isArray(skillList)) {
        for (const s of skillList) {
          const name = typeof s === "string" ? s : (s.name || s.skill_name || "");
          if (!name) continue;
          const count = typeof s === "object" ? (s.project_count ?? (Array.isArray(s.projects) ? s.projects.length : 0)) : 0;
          if (count >= 5) byLevel.Expert.push(name);
          else if (count >= 2) byLevel.Proficient.push(name);
          else byLevel.Familiar.push(name);
        }
      }

      setResume(prev => ({ ...prev, skills_by_level: byLevel }));
      setShowSkills(true);
      addSection("skills");
      markDirty();
    } catch (e) {
      showStatus("Failed to load skills: " + e.message, "err");
    }
  }

  async function saveChanges() {
    if (!resume) return;
    // Check page count before saving — abort if resume exceeds 1 page
    const currentPageCount = await checkPageCount();
    if (currentPageCount !== null && currentPageCount > 1) {
      toast("Resume exceeds 1 page — trim content before saving", "err");
      return;
    }
    setLoading(true);
    try {
      // 1. Sync education: delete removed entries, add new ones
      const currentEduIds = resume.education
        .filter(e => !e._isNew && e.id)
        .map(e => String(e.id));
      const originalEduIds = originalEdu.map(e => String(e.id));

      // Deletions
      for (const origId of originalEduIds) {
        if (!currentEduIds.includes(origId)) {
          await fetch(`${API_BASE}/education/${origId}`, {
            method: "DELETE",
            headers: authHeaders(),
          });
        }
      }

      // Additions
      const newEduEntries = resume.education.filter(e => e._isNew);
      const savedEdu = [];
      for (const entry of newEduEntries) {
        // Normalize dates to YYYY-MM-01 (ISO full date required by backend)
        const startIso = entry.start_date
          ? entry.start_date.slice(0, 7) + "-01"
          : "2000-01-01";
        const endIso = (!entry._endPresent && entry.end_date && entry.end_date !== "Present")
          ? entry.end_date.slice(0, 7) + "-01"
          : null;
        const res = await fetch(`${API_BASE}/education`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            institution: entry.institution,
            degree_type: entry.degree_type,
            topic: entry.topic,
            start_date: startIso,
            end_date: endIso,
            location: entry.location || null,
            gpa: entry.gpa || null,
            details: entry.details || [],
          }),
        });
        if (res.ok) {
          const data = await res.json();
          savedEdu.push({ ...data.education, _id: String(data.education.id), _isNew: false });
        }
      }

      // 2. Sync work history
      const currentWorkIds = resume.work_history
        .filter(w => !w._isNew && w.id)
        .map(w => String(w.id));
      const originalWorkIds = originalWork.map(w => String(w.id));

      for (const origId of originalWorkIds) {
        if (!currentWorkIds.includes(origId)) {
          await fetch(`${API_BASE}/work-history/${origId}`, {
            method: "DELETE",
            headers: authHeaders(),
          });
        }
      }

      const newWorkEntries = resume.work_history.filter(w => w._isNew);
      const savedWork = [];
      for (const entry of newWorkEntries) {
        const startIso = entry.start_date
          ? entry.start_date.slice(0, 7) + "-01"
          : "2000-01-01";
        const endIso = (!entry._endPresent && entry.end_date && entry.end_date !== "Present")
          ? entry.end_date.slice(0, 7) + "-01"
          : null;
        const res = await fetch(`${API_BASE}/work-history`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            company: entry.company,
            role: entry.role,
            start_date: startIso,
            end_date: endIso,
            location: entry.location || null,
            bullets: entry.bullets || [],
          }),
        });
        if (res.ok) {
          const data = await res.json();
          savedWork.push({ ...data.work_history, _id: String(data.work_history.id), _isNew: false });
        }
      }

      // 3. Build clean resume JSON for /resume/save
      // Normalize helper: strip datetime noise, keep YYYY-MM only for display/export
      const normDate = (v) => {
        if (!v || v === "Present") return v || null;
        return v.slice(0, 7); // "YYYY-MM"
      };

      const cleanEdu = [
        ...resume.education.filter(e => !e._isNew),
        ...savedEdu,
      ].map(({ _id, _isNew, _endPresent, ...rest }) => ({
        ...rest,
        start_date: normDate(rest.start_date),
        end_date: _endPresent ? null : normDate(rest.end_date),
      }));

      const cleanWork = [
        ...resume.work_history.filter(w => !w._isNew),
        ...savedWork,
      ].map(({ _id, _isNew, _endPresent, ...rest }) => ({
        ...rest,
        start_date: normDate(rest.start_date),
        end_date: _endPresent ? "Present" : normDate(rest.end_date) || "Present",
      }));

      const cleanProjects = (resume.projects || []).map(
        // eslint-disable-next-line no-unused-vars
        ({ lines_of_code, file_count, importance_score, ...rest }) => rest
      );

      const resumePayload = {
        name: resume.name,
        email: resume.email,
        phone: resume.phone || null,
        linkedin: resume.linkedin || null,
        github: resume.github || null,
        education: cleanEdu,
        awards: resume.awards || [],
        skills_by_level: resume.skills_by_level || {},
        work_history: cleanWork,
        projects: cleanProjects,
        section_order: sectionOrder,
        section_labels: sectionLabels,
      };

      const saveRes = await fetch(`${API_BASE}/resume/save?resume_id=${activeResumeId}`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify(resumePayload),
      });

      if (!saveRes.ok) throw new Error(`Save failed: HTTP ${saveRes.status}`);

      // 4. Update originalEdu/Work to reflect new DB state
      const allEdu = [
        ...resume.education.filter(e => !e._isNew),
        ...savedEdu,
      ].map(e => ({ ...e, _isNew: false }));
      const allWork = [
        ...resume.work_history.filter(w => !w._isNew),
        ...savedWork,
      ].map(w => ({ ...w, _isNew: false }));

      setOriginalEdu(allEdu);
      setOriginalWork(allWork);
      setResume(prev => ({ ...prev, education: allEdu, work_history: allWork }));
      setDirty(false);
      setEditing(false);
      localStorage.setItem("resume_saved", "1");
      window.dispatchEvent(new Event("resume-updated"));
      showStatus("Changes saved.");
      toast("Resume saved!", "ok");
      checkPageCount();
      // Subtle upward ticker-tape for regular saves
      confetti({ particleCount: 20, angle: 90, spread: 30, origin: { x: 0.5, y: 1 },
        colors: ["#6366f1","#a78bfa","#818cf8"], startVelocity: 40, ticks: 60, scalar: 0.8 });
    } catch (e) {
      showStatus("Save failed: " + e.message, "err");
      toast("Save failed: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  async function deleteResume() {
    if (!window.confirm("Delete this resume? Your projects and bullets are not affected.")) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/resume/${activeResumeId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      toast("Resume deleted", "ok");
      await loadResumeList();
      setView("list");
    } catch (e) {
      showStatus("Delete failed: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  async function checkPageCount() {
    if (!resume) return null;
    setPageCountLoading(true);
    try {
      const normDate = (v) => (!v || v === "Present") ? (v || null) : v.slice(0, 7);
      const cleanEdu = (resume.education || [])
        .filter(e => !e._isNew)
        .map(({ _id, _isNew, _endPresent, ...rest }) => ({
          ...rest,
          start_date: normDate(rest.start_date),
          end_date: _endPresent ? null : normDate(rest.end_date),
        }));
      const cleanWork = (resume.work_history || [])
        .filter(w => !w._isNew)
        .map(({ _id, _isNew, _endPresent, ...rest }) => ({
          ...rest,
          start_date: normDate(rest.start_date),
          end_date: _endPresent ? "Present" : normDate(rest.end_date) || "Present",
        }));
      const cleanProjects = (resume.projects || []).map(
        // eslint-disable-next-line no-unused-vars
        ({ lines_of_code, file_count, importance_score, ...rest }) => rest
      );
      const res = await fetch(`${API_BASE}/resume/page-count`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          name: resume.name,
          email: resume.email,
          phone: resume.phone || null,
          linkedin: resume.linkedin || null,
          github: resume.github || null,
          education: cleanEdu,
          awards: resume.awards || [],
          skills_by_level: resume.skills_by_level || {},
          work_history: cleanWork,
          projects: cleanProjects,
          section_order: sectionOrder,
          section_labels: sectionLabels,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPageCount(data.pages);
      return data.pages;
    } catch (e) {
      showStatus("Page count check failed: " + e.message, "err");
      return null;
    } finally {
      setPageCountLoading(false);
    }
  }

  async function downloadFile(endpoint, filename) {
    try {
      // Save current state first so the export reflects the latest section order + changes
      const normDate = (v) => {
        if (!v || v === "Present") return v || null;
        return v.slice(0, 7);
      };
      const cleanEdu = (resume.education || [])
        .filter(e => !e._isNew)
        .map(({ _id, _isNew, ...rest }) => ({
          ...rest,
          start_date: normDate(rest.start_date),
          end_date: normDate(rest.end_date),
        }));
      const cleanWork = (resume.work_history || [])
        .filter(w => !w._isNew)
        .map(({ _id, _isNew, ...rest }) => ({
          ...rest,
          start_date: normDate(rest.start_date),
          end_date: rest.end_date === "Present" || !rest.end_date ? "Present" : normDate(rest.end_date),
        }));
      const dlCleanProjects = (resume.projects || []).map(
        // eslint-disable-next-line no-unused-vars
        ({ lines_of_code, file_count, importance_score, ...rest }) => rest
      );

      await fetch(`${API_BASE}/resume/save?resume_id=${activeResumeId}`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          name: resume.name,
          email: resume.email,
          phone: resume.phone || null,
          linkedin: resume.linkedin || null,
          github: resume.github || null,
          education: cleanEdu,
          awards: resume.awards || [],
          skills_by_level: resume.skills_by_level || {},
          work_history: cleanWork,
          projects: dlCleanProjects,
          section_order: sectionOrder,
          section_labels: sectionLabels,
        }),
      });

      const res = await fetch(`${API_BASE}${endpoint}?resume_id=${activeResumeId}`, { headers: authHeaders() });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      toast("Downloaded " + filename, "ok");
      // Two diagonal bursts for download
      confetti({ particleCount: 25, angle: 135, spread: 40, origin: { x: 1, y: 0 }, colors: ["#34d399","#6366f1","#a78bfa"] });
      confetti({ particleCount: 25, angle: 45,  spread: 40, origin: { x: 0, y: 0 }, colors: ["#fbbf24","#818cf8","#34d399"] });
    } catch (e) {
      showStatus("Download failed: " + e.message, "err");
      toast("Download failed: " + e.message, "err");
    }
  }

  // ── section management ───────────────────────────────────────────────────────

  function addSection(key) {
    setSectionOrder(prev => prev.includes(key) ? prev : [...prev, key]);
  }

  function removeSection(key) {
    setSectionOrder(prev => prev.filter(k => k !== key));
    if (key === "education") {
      setShowEdu(false);
      setResume(prev => ({ ...prev, education: [] }));
      markDirty();
    }
    if (key === "work_history") {
      setShowWork(false);
      setResume(prev => ({ ...prev, work_history: [] }));
      markDirty();
    }
    if (key === "skills") {
      setShowSkills(false);
      setResume(prev => ({ ...prev, skills_by_level: { Expert: [], Proficient: [], Familiar: [] } }));
      markDirty();
    }
  }

  // ── drag-and-drop ────────────────────────────────────────────────────────────

  function handleDragStart(key) { dragSrc.current = key; }
  function handleDragOver(e, key) { e.preventDefault(); setDragOver(key); }
  function handleDrop(e, key) {
    e.preventDefault();
    if (!dragSrc.current || dragSrc.current === key) { setDragOver(null); return; }
    setSectionOrder(prev => {
      const next = [...prev];
      const from = next.indexOf(dragSrc.current);
      const to = next.indexOf(key);
      next.splice(from, 1);
      next.splice(to, 0, dragSrc.current);
      return next;
    });
    dragSrc.current = null;
    setDragOver(null);
    markDirty();
  }

  // ── education helpers ────────────────────────────────────────────────────────

  function addEduEntry() {
    if (!showEdu) { setShowEdu(true); addSection("education"); }
    setResume(prev => ({ ...prev, education: [...(prev.education || []), blankEducation()] }));
    markDirty();
  }

  function updateEduEntry(idx, field, value) {
    setResume(prev => {
      const edu = [...prev.education];
      edu[idx] = { ...edu[idx], [field]: value };
      return { ...prev, education: edu };
    });
    markDirty();
  }

  function removeEduEntry(idx) {
    setResume(prev => {
      const edu = prev.education.filter((_, i) => i !== idx);
      if (edu.length === 0) { setShowEdu(false); setSectionOrder(o => o.filter(k => k !== "education")); }
      return { ...prev, education: edu };
    });
    markDirty();
  }

  // ── work history helpers ─────────────────────────────────────────────────────

  function addWorkEntry() {
    if (!showWork) { setShowWork(true); addSection("work_history"); }
    setResume(prev => ({ ...prev, work_history: [...(prev.work_history || []), blankWorkHistory()] }));
    markDirty();
  }

  function updateWorkEntry(idx, field, value) {
    setResume(prev => {
      const work = [...prev.work_history];
      work[idx] = { ...work[idx], [field]: value };
      return { ...prev, work_history: work };
    });
    markDirty();
  }

  function removeWorkEntry(idx) {
    setResume(prev => {
      const work = prev.work_history.filter((_, i) => i !== idx);
      if (work.length === 0) { setShowWork(false); setSectionOrder(o => o.filter(k => k !== "work_history")); }
      return { ...prev, work_history: work };
    });
    markDirty();
  }

  function addWorkBullet(idx) {
    setResume(prev => {
      const work = [...prev.work_history];
      work[idx] = { ...work[idx], bullets: [...(work[idx].bullets || []), ""] };
      return { ...prev, work_history: work };
    });
    markDirty();
  }

  function updateWorkBullet(wIdx, bIdx, value) {
    setResume(prev => {
      const work = [...prev.work_history];
      const bullets = [...work[wIdx].bullets];
      bullets[bIdx] = value;
      work[wIdx] = { ...work[wIdx], bullets };
      return { ...prev, work_history: work };
    });
    markDirty();
  }

  function removeWorkBullet(wIdx, bIdx) {
    setResume(prev => {
      const work = [...prev.work_history];
      work[wIdx] = { ...work[wIdx], bullets: work[wIdx].bullets.filter((_, i) => i !== bIdx) };
      return { ...prev, work_history: work };
    });
    markDirty();
  }

  // ── per-project regen + remove ───────────────────────────────────────────────

  const [regenLoading, setRegenLoading] = useState(new Set());
  const [aiRegenLoading, setAiRegenLoading] = useState(new Set());

  async function aiEnhanceProjectBullets(pIdx) {
    const p = resume.projects[pIdx];
    if (!p.project_id) return;
    setAiRegenLoading(prev => new Set([...prev, pIdx]));
    try {
      const res = await fetch(`${API_BASE}/resume/projects/${p.project_id}/ai-enhance?resume_id=${activeResumeId}`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          bullets: p.bullets?.length ? p.bullets : null,
          num_bullets: numBullets,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResume(prev => {
        const projects = [...prev.projects];
        projects[pIdx] = { ...projects[pIdx], bullets: data.bullets || [], ats_score: data.ats_score };
        return { ...prev, projects };
      });
      markDirty();
      toast("Bullets enhanced!", "ok");
    } catch (e) {
      toast("AI enhance failed: " + e.message, "err");
    } finally {
      setAiRegenLoading(prev => { const next = new Set(prev); next.delete(pIdx); return next; });
    }
  }

  async function regenerateProjectBullets(pIdx) {
    const p = resume.projects[pIdx];
    if (!p.project_id) return;
    setRegenLoading(prev => new Set([...prev, pIdx]));
    try {
      const res = await fetch(`${API_BASE}/resume/projects/${p.project_id}/regenerate?resume_id=${activeResumeId}`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ num_bullets: numBullets }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResume(prev => {
        const projects = [...prev.projects];
        projects[pIdx] = { ...projects[pIdx], bullets: data.bullets || [], ats_score: data.ats_score };
        return { ...prev, projects };
      });
      markDirty();
      toast("Bullets regenerated!", "ok");
    } catch (e) {
      toast("Regenerate failed: " + e.message, "err");
    } finally {
      setRegenLoading(prev => { const next = new Set(prev); next.delete(pIdx); return next; });
    }
  }

  function removeProject(pIdx) {
    setResume(prev => ({ ...prev, projects: prev.projects.filter((_, i) => i !== pIdx) }));
    markDirty();
  }

  // ── project bullet helpers ───────────────────────────────────────────────────

  function updateProjectBullet(pIdx, bIdx, value) {
    setResume(prev => {
      const projects = [...prev.projects];
      const bullets = [...projects[pIdx].bullets];
      bullets[bIdx] = value;
      projects[pIdx] = { ...projects[pIdx], bullets };
      return { ...prev, projects };
    });
    markDirty();
  }

  function addProjectBullet(pIdx) {
    setResume(prev => {
      const projects = [...prev.projects];
      projects[pIdx] = { ...projects[pIdx], bullets: [...(projects[pIdx].bullets || []), ""] };
      return { ...prev, projects };
    });
    markDirty();
  }

  function removeProjectBullet(pIdx, bIdx) {
    setResume(prev => {
      const projects = [...prev.projects];
      projects[pIdx] = { ...projects[pIdx], bullets: projects[pIdx].bullets.filter((_, i) => i !== bIdx) };
      return { ...prev, projects };
    });
    markDirty();
  }

  // ── render ───────────────────────────────────────────────────────────────────

  if (authed === null) {
    // Still validating token against backend — show nothing yet
    return (
      <div className="page-wrap">
        <div className="resume-loader" style={{ paddingTop: 80 }}>Checking authentication...</div>
      </div>
    );
  }

  if (!authed) {
    return (
      <div className="page-wrap">
        <div className="resume-auth-wall card">
          <div className="resume-auth-icon">📄</div>
          <h2>Resume Builder</h2>
          <p className="text-muted">This feature requires an account. Sign in or create an account to build and export your resume.</p>
          <a className="btn-primary" href="/settings">Sign In / Sign Up →</a>
        </div>
      </div>
    );
  }

  const hasResume = Boolean(resume && resume.projects && resume.projects.length > 0);

  function renderSidebar() {
    return (
      <aside className="resume-sidebar">
        {/* Back button */}
        <button className="resume-back-btn" onClick={() => { setView("list"); setResume(null); setDirty(false); setEditing(false); loadResumeList(); }}>
          ← Back to Resumes
        </button>

        {/* Resume name — click to rename */}
        {renamingCardId === activeResumeId ? (
          <input
            className="resume-name-input"
            autoFocus
            value={renameCardValue}
            onChange={e => setRenameCardValue(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") saveCardRename(activeResumeId); if (e.key === "Escape") setRenamingCardId(null); }}
            onBlur={() => saveCardRename(activeResumeId)}
          />
        ) : (
          <div
            className="resume-name-display"
            onClick={() => { setRenamingCardId(activeResumeId); setRenameCardValue(activeResumeName || resume?.name || ""); }}
            title="Click to rename"
          >
            {activeResumeName || resume?.name || "Untitled Resume"}
          </div>
        )}

        <hr style={{ border: "none", borderTop: "1px solid rgba(255,255,255,0.08)", margin: "4px 0 10px" }} />

        {hasResume && (
          <div className="resume-completeness" style={{ marginBottom: 10 }}>
            <div className="resume-completeness-label">
              <span>Completeness</span>
              <span>{completeness}%</span>
            </div>
            <div className="resume-completeness-bar">
              <div
                className="resume-completeness-fill"
                style={{ width: `${completeness}%` }}
              />
            </div>
            <div className="resume-word-count">
              {wordCount} words · ~{Math.max(1, Math.ceil(wordCount / 450))} page{Math.ceil(wordCount / 450) !== 1 ? "s" : ""}
            </div>
          </div>
        )}

        {!hasResume ? (
          /* ── No resume yet: just the generate button ── */
          <div className="resume-ctrl-group">
            <button
              className="resume-btn resume-btn-primary"
              onClick={generateResume}
              disabled={loading}
            >
              {loading ? "Generating..." : "Generate Resume"}
            </button>
          </div>
        ) : (
          <>
            {/* ── View group ── */}
            <div className="resume-ctrl-group">
              <span className="resume-ctrl-label">View</span>
              <button
                className={`resume-btn ${previewMode ? "resume-btn-active" : "resume-btn-secondary"}`}
                onClick={() => {
                  const next = !previewMode;
                  setPreviewMode(next);
                  if (next) setEditing(false);
                }}
              >
                {previewMode ? "Exit Preview" : "Export Preview"}
              </button>
            </div>

            {/* ── Edit group ── */}
            <div className="resume-ctrl-group">
              <span className="resume-ctrl-label">Edit</span>
              <div className="resume-ctrl-row">
                <button
                  className={`resume-btn ${editing ? "resume-btn-active" : "resume-btn-secondary"}`}
                  onClick={() => setEditing(e => !e)}
                >
                  {editing ? "Exit Edit" : "Edit Mode"}
                </button>
                <button
                  className="resume-btn resume-btn-save"
                  onClick={saveChanges}
                  disabled={!dirty || loading || (pageCount !== null && pageCount > 1)}
                >
                  {loading ? "Saving…" : "Save Changes"}
                </button>
              </div>
            </div>

            {/* ── Generate group ── */}
            <div className="resume-ctrl-group">
              <span className="resume-ctrl-label">Generate</span>
              <div className="resume-ctrl-row-generate">
                <div className="resume-bullet-stepper" style={{ flex: 1 }}>
                  <button
                    type="button"
                    className="resume-bullet-step"
                    onClick={() => setNumBullets(n => Math.max(2, n - 1))}
                    disabled={numBullets <= 2}
                  >−</button>
                  <span className="resume-bullet-val">{numBullets}</span>
                  <button
                    type="button"
                    className="resume-bullet-step"
                    onClick={() => setNumBullets(n => Math.min(5, n + 1))}
                    disabled={numBullets >= 5}
                  >+</button>
                </div>
                <button
                  className="resume-btn resume-btn-primary"
                  onClick={generateResume}
                  disabled={loading}
                  style={{ flex: 1 }}
                >
                  {loading ? "…" : "Refresh"}
                </button>
              </div>
            </div>

            {/* ── Fit check group ── */}
            <div className="resume-ctrl-group">
              <span className="resume-ctrl-label">Fit check</span>
              <div className="resume-ctrl-row-fit">
                <button
                  className="resume-btn resume-btn-secondary"
                  onClick={checkPageCount}
                  disabled={pageCountLoading}
                  style={{ flex: 1 }}
                >
                  {pageCountLoading ? "Checking…" : "Check Fit"}
                </button>
                {pageCount !== null && (
                  <div className={`resume-page-count-badge ${pageCount === 1 ? "ok" : "over"}`} style={{ flex: "none" }}>
                    {pageCount === 1 ? "✓ 1 page" : `${pageCount} pages`}
                  </div>
                )}
              </div>
            </div>

            {/* ── Export group ── */}
            <div className="resume-ctrl-group">
              <span className="resume-ctrl-label">Export</span>
              <div className="resume-ctrl-row">
                <button
                  className="resume-btn resume-btn-secondary"
                  onClick={() => downloadFile("/resume/download/pdf", `resume_${resume?.name?.replace(/ /g, "_") || "export"}.pdf`)}
                  disabled={loading || (pageCount !== null && pageCount > 1)}
                  title={pageCount > 1 ? "Resume exceeds 1 page — trim content before exporting" : ""}
                >
                  PDF
                </button>
                <button
                  className="resume-btn resume-btn-secondary"
                  onClick={() => downloadFile("/resume/download/docx", `resume_${resume?.name?.replace(/ /g, "_") || "export"}.docx`)}
                  disabled={loading || (pageCount !== null && pageCount > 1)}
                  title={pageCount > 1 ? "Resume exceeds 1 page — trim content before exporting" : ""}
                >
                  DOCX
                </button>
              </div>
            </div>

            {/* ── Add sections group ── */}
            <div className="resume-ctrl-group">
              <span className="resume-ctrl-label">Add sections</span>
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                <button className="resume-btn resume-btn-secondary" onClick={addEduEntry}>+ Education / Awards</button>
                <button className="resume-btn resume-btn-secondary" onClick={addWorkEntry}>+ Experience</button>
                <button className="resume-btn resume-btn-secondary" onClick={addSkillsSection} disabled={showSkills}>+ Skills</button>
              </div>
            </div>

            <hr style={{ border: "none", borderTop: "1px solid rgba(255,255,255,0.08)", margin: "4px 0 10px" }} />

            {/* ── Delete ── */}
            <div className="resume-ctrl-group">
              <button
                className="resume-btn resume-btn-danger"
                onClick={deleteResume}
                disabled={loading}
              >
                Delete Resume
              </button>
            </div>
          </>
        )}

        {!aiConsent && hasResume && (
          <p className="resume-ai-hint">
            Enable AI consent in <a href="/settings">Settings</a> for AI-generated bullets.
          </p>
        )}

        {status.msg && (
          <div className={`resume-status resume-status-${status.type}`}>
            {status.msg}
          </div>
        )}
      </aside>
    );
  }

  function renderSection(key) {
    if (!resume) return null;

    switch (key) {
      case "projects": return renderProjects(key);
      case "education": return showEdu && resume.education?.length > 0 ? renderEducation(key) : null;
      case "work_history": return showWork && resume.work_history?.length > 0 ? renderWorkHistory(key) : null;
      case "skills": return showSkills ? renderSkills(key) : null;
      default: return null;
    }
  }

  function renderProjects(key) {
    if (!resume.projects?.length) return null;
    return (
      <div
        key={key}
        className={`r-section-block${dragOver === key ? " r-drag-over" : ""}`}
        draggable={editing}
        onDragStart={() => handleDragStart(key)}
        onDragOver={e => handleDragOver(e, key)}
        onDrop={e => handleDrop(e, key)}
      >
        <div className="r-section">
          {editing && <span className="r-drag-handle">⠿</span>}
          <hr className="r-rule" />
          <InlineEdit
            value={sectionLabels.projects}
            onChange={v => { setSectionLabels(l => ({ ...l, projects: v })); markDirty(); }}
            editing={editing}
            className="r-section-title"
          />
          <hr className="r-rule" />
        </div>

        {resume.projects.map((p, pIdx) => (
          <div key={pIdx} className="proj-item">
            {editing && (
              <button className="r-delete-entry" onClick={() => removeProject(pIdx)}>✕ Remove</button>
            )}
            <div className="proj-name">
              <InlineEdit
                value={p.name || p.header}
                onChange={v => {
                  setResume(prev => {
                    const projects = [...prev.projects];
                    projects[pIdx] = { ...projects[pIdx], name: v };
                    return { ...prev, projects };
                  });
                  markDirty();
                }}
                editing={editing}
                className="proj-name-text"
                placeholder="Project name"
              />
              {p.project_id && !previewMode && (
                <button
                  className={`proj-regen-btn${regenLoading.has(pIdx) ? " proj-regen-spinning" : ""}`}
                  onClick={() => regenerateProjectBullets(pIdx)}
                  disabled={regenLoading.has(pIdx)}
                  title="Regenerate bullets for this project"
                >↻</button>
              )}
              {p.project_id && !previewMode && aiConsent && (
                <button
                  className={`proj-regen-btn proj-ai-btn${aiRegenLoading.has(pIdx) ? " proj-regen-spinning" : ""}`}
                  onClick={() => aiEnhanceProjectBullets(pIdx)}
                  disabled={aiRegenLoading.has(pIdx)}
                  title={p.bullets?.length ? "Enhance existing bullets with AI" : "Generate AI-powered bullets"}
                >✦</button>
              )}
            </div>

            {p.bullets && p.bullets.length > 0 ? (
              <ul className="proj-bullets">
                {p.bullets.map((b, bIdx) => (
                  <li key={bIdx} className="proj-bullet-item">
                    {editing ? (
                      <>
                        <textarea
                          className="r-bullet-input"
                          value={b}
                          onChange={e => updateProjectBullet(pIdx, bIdx, e.target.value)}
                          rows={2}
                        />
                        <button className="r-delete-bullet" onClick={() => removeProjectBullet(pIdx, bIdx)}>✕</button>
                      </>
                    ) : b}
                  </li>
                ))}
                {editing && (
                  <li>
                    <button className="r-add-bullet" onClick={() => addProjectBullet(pIdx)}>+ Add bullet</button>
                  </li>
                )}
              </ul>
            ) : (
              <div className="proj-no-bul">
                {editing
                  ? <button className="r-add-bullet" onClick={() => addProjectBullet(pIdx)}>+ Add bullet</button>
                  : (aiConsent ? "Click Refresh Resume to generate bullets." : "No bullets yet.")}
              </div>
            )}

            {!previewMode && p.ats_score != null && (
              <div className="proj-ats">
                <span className={`proj-ats-badge ${p.ats_score >= 70 ? "high" : p.ats_score < 40 ? "low" : ""}`}>
                  ATS {Math.round(p.ats_score)}/100
                </span>
                <AtsTooltip />
              </div>
            )}
            {!previewMode && (p.lines_of_code > 0 || p.file_count > 0 || p.importance_score > 0) && (
              <div className="proj-stats">
                {p.lines_of_code > 0 && (
                  <span className="proj-stat-badge">{p.lines_of_code.toLocaleString()} LOC</span>
                )}
                {p.file_count > 0 && (
                  <span className="proj-stat-badge">{p.file_count} files</span>
                )}
                {p.importance_score > 0 && (
                  <span className="proj-stat-badge">score {p.importance_score}</span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  function renderEducation(key) {
    return (
      <div
        key={key}
        className={`r-section-block${dragOver === key ? " r-drag-over" : ""}`}
        draggable={editing}
        onDragStart={() => handleDragStart(key)}
        onDragOver={e => handleDragOver(e, key)}
        onDrop={e => handleDrop(e, key)}
      >
        <div className="r-section">
          {editing && <span className="r-drag-handle">⠿</span>}
          <hr className="r-rule" />
          <InlineEdit
            value={sectionLabels.education}
            onChange={v => { setSectionLabels(l => ({ ...l, education: v })); markDirty(); }}
            editing={editing}
            className="r-section-title"
          />
          <hr className="r-rule" />
          {editing && (
            <button className="r-delete-section" onClick={() => removeSection("education")}>✕</button>
          )}
        </div>

        {resume.education.map((edu, idx) => (
          <div key={edu._id || idx} className="edu-entry">
            {editing && (
              <button className="r-delete-entry" onClick={() => removeEduEntry(idx)}>✕ Remove</button>
            )}
            <div className="edu-row">
              <InlineEdit
                value={edu.institution}
                onChange={v => updateEduEntry(idx, "institution", v)}
                editing={editing}
                className="edu-degree"
                placeholder="Institution"
              />
              <div className="edu-dates">
                {editing ? (
                  <span className="r-date-range">
                    <MonthPicker
                      value={edu.start_date || ""}
                      onChange={v => updateEduEntry(idx, "start_date", normalizeDate(v))}
                      placeholder="Start date"
                    />
                    <span className="r-date-sep"> – </span>
                    {edu._endPresent ? (
                      <span className="r-present-badge">
                        Present
                        <label className="r-present-check">
                          <input
                            type="checkbox"
                            checked={true}
                            onChange={() => updateEduEntry(idx, "_endPresent", false)}
                          />
                        </label>
                      </span>
                    ) : (
                      <span className="r-date-range">
                        <MonthPicker
                          value={edu.end_date || ""}
                          onChange={v => updateEduEntry(idx, "end_date", normalizeDate(v))}
                          placeholder="End date"
                        />
                        <label className="r-present-check">
                          Present
                          <input
                            type="checkbox"
                            checked={false}
                            onChange={() => { updateEduEntry(idx, "_endPresent", true); updateEduEntry(idx, "end_date", null); }}
                          />
                        </label>
                      </span>
                    )}
                  </span>
                ) : (
                  `${formatDateDisplay(edu.start_date)} – ${edu._endPresent || !edu.end_date || edu.end_date === "Present" ? "Present" : formatDateDisplay(edu.end_date)}`
                )}
              </div>
            </div>
            <div className="edu-inst">
              <InlineEdit
                value={`${edu.degree_type}${edu.topic ? " in " + edu.topic : ""}`}
                onChange={v => {
                  // parse "X in Y" back into degree_type + topic
                  const parts = v.split(" in ");
                  updateEduEntry(idx, "degree_type", parts[0]);
                  if (parts[1] !== undefined) updateEduEntry(idx, "topic", parts[1]);
                }}
                editing={editing}
                placeholder="Degree type in Field of study"
              />
            </div>
            {editing && (
              <div className="r-edu-extra">
                <input
                  className="r-inline-input"
                  value={edu.location || ""}
                  onChange={e => updateEduEntry(idx, "location", e.target.value)}
                  placeholder="Location (optional)"
                />
                <input
                  className="r-inline-input"
                  value={edu.gpa || ""}
                  onChange={e => updateEduEntry(idx, "gpa", e.target.value)}
                  placeholder="GPA (optional)"
                />
              </div>
            )}
          </div>
        ))}

        {editing && (
          <button className="r-add-bullet" style={{ marginBottom: 6 }} onClick={addEduEntry}>+ Add education / awards entry</button>
        )}

        {/* ── Awards sub-section inside Education ── */}
        {(editing || (resume.awards && resume.awards.length > 0)) && (
          <div className="r-awards-subsection">
            <div className="r-awards-label">Awards {editing && <span className="r-awards-optional">(optional)</span>}</div>
            {(resume.awards || []).map((award, aIdx) => (
              <div key={aIdx} className="award-item r-award-row-edit">
                {editing ? (
                  <>
                    <input
                      className="r-inline-input"
                      value={award}
                      onChange={e => {
                        setResume(prev => {
                          const awards = [...(prev.awards || [])];
                          awards[aIdx] = e.target.value;
                          return { ...prev, awards };
                        });
                        markDirty();
                      }}
                      placeholder="Award name"
                    />
                    <button
                      className="r-delete-bullet"
                      onClick={() => {
                        setResume(prev => ({ ...prev, awards: (prev.awards || []).filter((_, i) => i !== aIdx) }));
                        markDirty();
                      }}
                    >✕</button>
                  </>
                ) : (
                  <span>{award}</span>
                )}
              </div>
            ))}
            {editing && (
              <button
                className="r-add-bullet"
                onClick={() => {
                  setResume(prev => ({ ...prev, awards: [...(prev.awards || []), ""] }));
                  markDirty();
                }}
              >+ Add award</button>
            )}
          </div>
        )}
      </div>
    );
  }

  function renderWorkHistory(key) {
    return (
      <div
        key={key}
        className={`r-section-block${dragOver === key ? " r-drag-over" : ""}`}
        draggable={editing}
        onDragStart={() => handleDragStart(key)}
        onDragOver={e => handleDragOver(e, key)}
        onDrop={e => handleDrop(e, key)}
      >
        <div className="r-section">
          {editing && <span className="r-drag-handle">⠿</span>}
          <hr className="r-rule" />
          <InlineEdit
            value={sectionLabels.work_history}
            onChange={v => { setSectionLabels(l => ({ ...l, work_history: v })); markDirty(); }}
            editing={editing}
            className="r-section-title"
          />
          <hr className="r-rule" />
          {editing && (
            <button className="r-delete-section" onClick={() => removeSection("work_history")}>✕</button>
          )}
        </div>

        {resume.work_history.map((job, idx) => (
          <div key={job._id || idx} className="work-entry">
            {editing && (
              <button className="r-delete-entry" onClick={() => removeWorkEntry(idx)}>✕ Remove</button>
            )}
            <div className="edu-row">
              <InlineEdit
                value={job.company + (job.location ? "  |  " + job.location : "")}
                onChange={v => {
                  const parts = v.split("  |  ");
                  updateWorkEntry(idx, "company", parts[0]);
                  if (parts[1] !== undefined) updateWorkEntry(idx, "location", parts[1]);
                }}
                editing={editing}
                className="edu-degree"
                placeholder="Company  |  Location"
              />
              <div className="edu-dates">
                {editing ? (
                  <span className="r-date-range">
                    <MonthPicker
                      value={job.start_date || ""}
                      onChange={v => updateWorkEntry(idx, "start_date", normalizeDate(v))}
                      placeholder="Start date"
                    />
                    <span className="r-date-sep"> – </span>
                    {job._endPresent ? (
                      <span className="r-present-badge">
                        Present
                        <label className="r-present-check">
                          <input
                            type="checkbox"
                            checked={true}
                            onChange={() => updateWorkEntry(idx, "_endPresent", false)}
                          />
                        </label>
                      </span>
                    ) : (
                      <span className="r-date-range">
                        <MonthPicker
                          value={job.end_date || ""}
                          onChange={v => updateWorkEntry(idx, "end_date", normalizeDate(v))}
                          placeholder="End date"
                        />
                        <label className="r-present-check">
                          Present
                          <input
                            type="checkbox"
                            checked={false}
                            onChange={() => { updateWorkEntry(idx, "_endPresent", true); updateWorkEntry(idx, "end_date", null); }}
                          />
                        </label>
                      </span>
                    )}
                  </span>
                ) : (
                  `${formatDateDisplay(job.start_date)} – ${job._endPresent || !job.end_date || job.end_date === "Present" ? "Present" : formatDateDisplay(job.end_date)}`
                )}
              </div>
            </div>
            <div className="edu-inst">
              <InlineEdit
                value={job.role}
                onChange={v => updateWorkEntry(idx, "role", v)}
                editing={editing}
                placeholder="Job title / role"
              />
            </div>
            <ul className="proj-bullets">
              {(job.bullets || []).map((b, bIdx) => (
                <li key={bIdx} className="proj-bullet-item">
                  {editing ? (
                    <>
                      <textarea
                        className="r-bullet-input"
                        value={b}
                        onChange={e => updateWorkBullet(idx, bIdx, e.target.value)}
                        rows={2}
                      />
                      <button className="r-delete-bullet" onClick={() => removeWorkBullet(idx, bIdx)}>✕</button>
                    </>
                  ) : b}
                </li>
              ))}
              {editing && (
                <li>
                  <button className="r-add-bullet" onClick={() => addWorkBullet(idx)}>+ Add bullet</button>
                </li>
              )}
            </ul>
          </div>
        ))}

        {editing && (
          <button className="r-add-bullet" style={{ marginBottom: 6 }} onClick={addWorkEntry}>+ Add experience entry</button>
        )}
      </div>
    );
  }

  function renderSkills(key) {
    const skillsByLevel = resume.skills_by_level || {};
    const hasSkills = Object.values(skillsByLevel).some(v => v.length > 0);
    if (!hasSkills) return null;

    return (
      <div
        key={key}
        className={`r-section-block${dragOver === key ? " r-drag-over" : ""}`}
        draggable={editing}
        onDragStart={() => handleDragStart(key)}
        onDragOver={e => handleDragOver(e, key)}
        onDrop={e => handleDrop(e, key)}
      >
        <div className="r-section">
          {editing && <span className="r-drag-handle">⠿</span>}
          <hr className="r-rule" />
          <InlineEdit
            value={sectionLabels.skills}
            onChange={v => { setSectionLabels(l => ({ ...l, skills: v })); markDirty(); }}
            editing={editing}
            className="r-section-title"
          />
          <hr className="r-rule" />
          {editing && (
            <button className="r-delete-section" onClick={() => removeSection("skills")}>✕</button>
          )}
        </div>

        {Object.entries(skillsByLevel).map(([level, skills]) =>
          skills.length > 0 || editing ? (
            <div key={level} className="skill-row">
              <strong>{level}:</strong>
              <span className="skill-sep">|</span>
              {editing ? (
                <SkillInput
                  level={level}
                  skills={skills}
                  onChange={updated => {
                    setResume(prev => ({
                      ...prev,
                      skills_by_level: { ...prev.skills_by_level, [level]: updated },
                    }));
                    markDirty();
                  }}
                />
              ) : (
                skills.join(", ")
              )}
            </div>
          ) : null
        )}
      </div>
    );
  }

  // ── List view ──────────────────────────────────────────────────────────────
  if (view === "list") {
    return (
      <div className="page-wrap">
        {renderList()}
      </div>
    );
  }

  // ── Editor view ─────────────────────────────────────────────────────────────
  return (
    <>
      <Joyride
        steps={walkthroughSteps}
        run={runWalkthrough}
        continuous
        showSkipButton
        showProgress
        styles={{
          options: {
            zIndex: 10000,
            primaryColor: 'var(--accent, #6366f1)',
            backgroundColor: 'var(--card-bg, #181a2a)',
            textColor: 'var(--text, #e0e7ff)',
            arrowColor: 'var(--card-bg, #181a2a)',
            overlayColor: 'rgba(30, 34, 54, 0.7)',
            spotlightShadow: '0 0 0 2px var(--accent, #6366f1), 0 1px 8px 0 rgba(99,102,241,0.10)',
          },
          close: {
            color: 'var(--text-muted, #a5b4fc)',
            top: 10,
            right: 10,
          },
        }}
        disableScrolling={true}
        callback={(data) => {
          if (data.status === 'finished' || data.status === 'skipped') {
            localStorage.setItem('resumes_walkthrough_seen', '1');
            setRunWalkthrough(false);
          }
        }}
      />
      <div className="page-wrap">
      <div className="resume-shell">
        {renderSidebar()}

        <main className="resume-main">
          {loading && <div className="resume-loader">Building your resume...</div>}

          {!loading && !hasResume && (
            <div className="resume-empty-state card">
              <p className="text-muted">No resume yet. Click <strong>Generate Resume</strong> to get started.</p>
            </div>
          )}

          {!loading && hasResume && resume && (
            <div className={`resume-doc card${editing ? " resume-editing" : ""}`}>

              {/* ── Name / contact header ── */}
              <div className="r-name">
                <InlineEdit
                  value={resume.name}
                  onChange={v => setResumeField("name", v)}
                  editing={editing}
                  placeholder="Your Name"
                  className="r-name-input"
                />
              </div>

              <div className="r-contact r-contact-row">
                {editing ? (
                  <>
                    <input className="r-inline-input r-contact-input" value={resume.email || ""} onChange={e => setResumeField("email", e.target.value)} placeholder="Email" />
                    <input className="r-inline-input r-contact-input" value={resume.phone || ""} onChange={e => setResumeField("phone", e.target.value)} placeholder="Phone" />
                    <input className="r-inline-input r-contact-input" value={resume.linkedin || ""} onChange={e => setResumeField("linkedin", e.target.value)} placeholder="LinkedIn URL" />
                    <input className="r-inline-input r-contact-input" value={resume.github || ""} onChange={e => setResumeField("github", e.target.value)} placeholder="GitHub URL" />
                  </>
                ) : (
                  [resume.email, resume.phone, resume.linkedin, resume.github]
                    .filter(Boolean)
                    .join(" | ")
                )}
              </div>

              <hr className="r-rule" />

              {/* ── Sections in user-defined order ── */}
              {sectionOrder.map(key => (
                <React.Fragment key={key}>
                  {renderSection(key)}
                </React.Fragment>
              ))}


            </div>
          )}
        </main>
      </div>
    </div>
  </>
  );
}