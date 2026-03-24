import React, { useEffect, useState, useRef } from "react";
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
    loadExisting();
  }, [authed]);

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

  async function loadExisting() {
    setLoading(true);
    try {
      // Fetch resume JSON + education + work history in parallel
      const [resumeRes, eduRes, workRes] = await Promise.all([
        fetch(`${API_BASE}/resume`, { headers: authHeaders() }),
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
        if (r && r.projects) {
          // Merge live education/work from DB over whatever's in stored resume
          applyResume({ ...r, education: taggedEdu, work_history: taggedWork });
          // Restore section order if previously saved
          if (r.section_order) setSectionOrder(r.section_order);
          if (r.section_labels) setSectionLabels(prev => ({ ...prev, ...r.section_labels }));
          // Determine which sections were present
          if (taggedEdu.length > 0) { setShowEdu(true); addSection("education"); }
          if (taggedWork.length > 0) { setShowWork(true); addSection("work_history"); }
          if (r.skills_by_level && Object.values(r.skills_by_level).some(v => v.length > 0)) {
            setShowSkills(true); addSection("skills");
          }
        }
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
      const res = await fetch(`${API_BASE}/resume/generate`, {
        method: "POST",
        headers: authHeaders(),
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
      applyResume({ ...r, education: taggedEdu, work_history: taggedWork });

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
      const skillNames = Array.isArray(skillList)
        ? skillList.map(s => (typeof s === "string" ? s : s.name || s.skill_name || ""))
        : [];

      // Group into a single "Familiar" bucket since we don't have level data from this endpoint
      const byLevel = { Expert: [], Proficient: [], Familiar: skillNames.filter(Boolean) };

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
        projects: resume.projects,
        section_order: sectionOrder,
        section_labels: sectionLabels,
      };

      const saveRes = await fetch(`${API_BASE}/resume/save`, {
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
      showStatus("Changes saved.");
    } catch (e) {
      showStatus("Save failed: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  async function deleteResume() {
    if (!window.confirm("Delete your resume? This will remove all resume data including sections you've added. Your projects and bullets are not affected.")) return;
    setLoading(true);
    try {
      // Save an empty resume object to clear user.resume
      await fetch(`${API_BASE}/resume/save`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setResume(null);
      setSectionOrder(["projects"]);
      setSectionLabels({ projects: "Projects", education: "Education", work_history: "Relevant Experience", skills: "Technical Skills" });
      setShowEdu(false);
      setShowWork(false);
      setShowSkills(false);
      setDirty(false);
      setEditing(false);
      showStatus("Resume deleted.");
    } catch (e) {
      showStatus("Delete failed: " + e.message, "err");
    } finally {
      setLoading(false);
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
      await fetch(`${API_BASE}/resume/save`, {
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
          projects: resume.projects,
          section_order: sectionOrder,
          section_labels: sectionLabels,
        }),
      });

      const res = await fetch(`${API_BASE}${endpoint}`, { headers: authHeaders() });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      showStatus("Download failed: " + e.message, "err");
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
        <a className="resume-back" href="/">← Dashboard</a>
        <h2>Resume Controls</h2>

        {!hasResume ? (
          <button
            className="resume-btn resume-btn-primary"
            onClick={generateResume}
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Resume"}
          </button>
        ) : (
          <>
            <button className="resume-btn resume-btn-primary" onClick={generateResume} disabled={loading}>
              Refresh Resume
            </button>

            <span className="resume-label">Add Sections</span>

            <button className="resume-btn resume-btn-secondary" onClick={addEduEntry}>
              + Add Award / Education
            </button>

            <button className="resume-btn resume-btn-secondary" onClick={addWorkEntry}>
              + Add Experience
            </button>

            <button
              className="resume-btn resume-btn-secondary"
              onClick={addSkillsSection}
              disabled={showSkills}
              title={showSkills ? "Skills section already added" : ""}
            >
              {showSkills ? "Skills Added ✓" : "+ Add Skills"}
            </button>

            <span className="resume-label">Export</span>

            <button
              className="resume-btn resume-btn-outline"
              onClick={() => downloadFile("/resume/download/pdf", `resume_${resume?.name?.replace(/ /g, "_") || "export"}.pdf`)}
              disabled={loading}
            >
              Save as PDF
            </button>

            <button
              className="resume-btn resume-btn-outline"
              onClick={() => downloadFile("/resume/download/docx", `resume_${resume?.name?.replace(/ /g, "_") || "export"}.docx`)}
              disabled={loading}
            >
              Save as DOCX
            </button>

            <span className="resume-label">Editing</span>

            <button
              className={`resume-btn ${editing ? "resume-btn-active" : "resume-btn-secondary"}`}
              onClick={() => setEditing(e => !e)}
            >
              {editing ? "Exit Edit Mode" : "Edit"}
            </button>

            <button
              className="resume-btn resume-btn-save"
              onClick={saveChanges}
              disabled={!dirty || loading}
            >
              {loading ? "Saving..." : "Save Changes"}
            </button>

            <button
              className="resume-btn resume-btn-danger"
              onClick={deleteResume}
              disabled={loading}
            >
              Delete Resume
            </button>
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

            {p.ats_score != null && (
              <div className="proj-ats">
                ATS score: {Math.round(p.ats_score)}/100
                <AtsTooltip />
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

        {/* ── Awards sub-section inside Education ── */}
        {(editing || (resume.awards && resume.awards.length > 0)) && (
          <div className="r-awards-subsection">
            <div className="r-awards-label">Awards <span className="r-awards-optional">(optional)</span></div>
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

  return (
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
  );
}