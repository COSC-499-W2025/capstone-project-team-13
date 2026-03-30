import { Joyride } from 'react-joyride';
// Joyride walkthrough steps for Portfolio page
const walkthroughSteps = [
  {
    target: 'body',
    placement: 'center',
    title: 'Welcome to Your Portfolio!',
    content: 'This page showcases all your projects, skills, and evidence. Let’s take a quick tour!',
    disableBeacon: true,
  },
  {
    target: '.port-hero',
    title: 'Portfolio Header',
    content: 'Here you can edit your portfolio\s title, change portfolio visibility, and access your web showcase. To generate a portfolio, simply upload projects and click "Regenerate".',
    spotlightPadding: 6,
  },
  {
    target: '.port-stat-row',
    title: 'Portfolio Stats',
    content: 'See a summary of your projects, code, files, and skills.',
    spotlightPadding: 6,
  },
  {
    target: '.port-sort-row',
    title: 'Sort & Layout',
    content: 'Sort your projects and switch between list or grid layouts.',
    spotlightPadding: 6,
  },
  {
    target: '.port-viz-card-sec',
    title: 'Skills Timeline & Activity Heatmap',
    content: 'See when you used different skills and view your project activity over time.',
    spotlightPadding: 6,
  },
];
import React, { useEffect, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import SkillsTimeline from "./SkillsTimeline";
import ActivityHeatmap from "./ActivityHeatmap";
import {
  typeColor, thumbUrl, educationEntryTypeOf, experienceTypeOf,
} from "./PortfolioShared";
import "./Portfolio.css";

const API_BASE = "http://127.0.0.1:8000";

const STAT_ICONS = { Projects: "📁", "Lines of Code": "💻", Files: "🗂️", "Word Count": "📝", Skills: "⚡" };

const SORT_OPTIONS = [
  { value: "importance", label: "Importance" },
  { value: "rank",       label: "User Rank" },
  { value: "date",       label: "Date" },
  { value: "name",       label: "Name" },
];

const NAV_ITEMS = [
  { id: "about",      label: "About Me" },
  { id: "projects",   label: "Projects" },
  { id: "skills",     label: "Skills & Stats" },
  { id: "experience", label: "Experience" },
  { id: "education",  label: "Education" },
  { id: "contact",    label: "Contact" },
];

const DEFAULT_HERO_TITLE = "Master Portfolio";
const DEFAULT_HERO_SUB   = "All projects · evidences · ranked";
const DEFAULT_CONTACT = {
  email: "",
  phone: "",
  location: "",
  website: "",
  linkedin: "",
  github: "",
  availability: "",
  intro: "",
  customPresences: [],
};

function normalizeContactInfo(raw) {
  const contact = { ...DEFAULT_CONTACT, ...(raw || {}) };
  contact.customPresences = Array.isArray(contact.customPresences)
    ? contact.customPresences.map((item, idx) => ({
        id: item?.id || `presence-${Date.now()}-${idx}`,
        label: item?.label || "",
        url: item?.url || "",
      }))
    : [];
  return contact;
}


export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState(null);
  const [includeHidden, setIncludeHidden] = useState(false);
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [rankInput, setRankInput] = useState({});
  const [sortBy, setSortBy] = useState("importance");
  const [authed, setAuthed] = useState(null);
  const [showEmojis, setShowEmojis] = useState(() => localStorage.getItem("dash_show_emojis") !== "false");
  const [viewMode, setViewMode] = useState(() => localStorage.getItem("portfolio_mode") || "private");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [layout, setLayout] = useState(() => localStorage.getItem("portfolio_layout") || "list");
  const [heroTitle, setHeroTitle] = useState(() => localStorage.getItem("portfolio_hero_title") || "");
  const [heroSub, setHeroSub] = useState(() => localStorage.getItem("portfolio_hero_sub") || "");
  const [editingHero, setEditingHero] = useState(null); // "title" | "sub" | null
  const [heroDraft, setHeroDraft] = useState("");
  const [showTimeline, setShowTimeline] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [portfolioPublic, setPortfolioPublic] = useState(false);
  const [activeSection, setActiveSection] = useState("about");
  const [aboutBio, setAboutBio] = useState("");
  const [profileAvatar, setProfileAvatar] = useState(() => localStorage.getItem("profile_avatar") || null);
  const [visibilityLoading, setVisibilityLoading] = useState(false);
  const [educationEntries, setEducationEntries] = useState([]);
  const [showEduForm, setShowEduForm] = useState(false);
  const [eduFormType, setEduFormType] = useState("postsecondary"); // "postsecondary" | "graduate" | "secondary"
  const [eduForm, setEduForm] = useState({ institution: "", degree_type: "", topic: "", start_date: "", end_date: "", location: "", gpa: "", awards: "" });
  const [eduError, setEduError] = useState(null);
  const [eduTitle, setEduTitle] = useState(() => localStorage.getItem("edu_title") || "Education");
  const [eduSubtitle, setEduSubtitle] = useState(() => localStorage.getItem("edu_subtitle") || "Academic Background");
  const [eduDesc, setEduDesc] = useState(() => localStorage.getItem("edu_desc") || "");
  const [editEduId, setEditEduId] = useState(null);
  const [editEduForm, setEditEduForm] = useState({});
  const [editEduError, setEditEduError] = useState(null);
  const [expEntries, setExpEntries] = useState([]);
  const [showExpForm, setShowExpForm] = useState(false);
  const [expFormType, setExpFormType] = useState("work");
  const [expForm, setExpForm] = useState({ company: "", role: "", start_date: "", end_date: "", location: "" });
  const [expError, setExpError] = useState(null);
  const [editExpId, setEditExpId] = useState(null);
  const [editExpForm, setEditExpForm] = useState({});
  const [editExpError, setEditExpError] = useState(null);
  const [expTitle, setExpTitle] = useState(() => localStorage.getItem("exp_title") || "Experience");
  const [expSubtitle, setExpSubtitle] = useState(() => localStorage.getItem("exp_subtitle") || "Work & Volunteering");
  const [expDesc, setExpDesc] = useState(() => localStorage.getItem("exp_desc") || "");
  const [contactInfo, setContactInfo] = useState(DEFAULT_CONTACT);
  const nav = useNavigate();

  // Joyride walkthrough state
  const [runWalkthrough, setRunWalkthrough] = useState(() => localStorage.getItem('portfolio_walkthrough_seen') !== '1');

  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('portfolio_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);

  useEffect(() => {
    const sync = () => setShowEmojis(localStorage.getItem("dash_show_emojis") !== "false");
    window.addEventListener("dash-emojis-updated", sync);
    return () => window.removeEventListener("dash-emojis-updated", sync);
  }, []);

  const contactSaveTimer = React.useRef(null);
  function saveContact(info) {
    clearTimeout(contactSaveTimer.current);
    contactSaveTimer.current = setTimeout(() => {
      apiFetch("/portfolio/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(info),
      }).catch(() => {});
    }, 800);
  }

  function setContactInfoAndSave(updater) {
    setContactInfo(prev => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      saveContact(next);
      return next;
    });
  }

  function addCustomPresence() {
    setContactInfoAndSave(info => ({
      ...info,
      customPresences: [
        ...(info.customPresences || []),
        { id: `presence-${Date.now()}`, label: "Social Media", url: "" },
      ],
    }));
  }

  function updateCustomPresence(id, field, value) {
    setContactInfoAndSave(info => ({
      ...info,
      customPresences: (info.customPresences || []).map(item =>
        item.id === id ? { ...item, [field]: value } : item
      ),
    }));
  }

  function removeCustomPresence(id) {
    setContactInfoAndSave(info => ({
      ...info,
      customPresences: (info.customPresences || []).filter(item => item.id !== id),
    }));
  }

  function switchMode(mode) {
    setViewMode(mode);
    localStorage.setItem("portfolio_mode", mode);
    if (mode === "public") { setEditId(null); setEditingHero(null); }
  }

  function setLayoutPersist(l) {
    setLayout(l);
    localStorage.setItem("portfolio_layout", l);
  }

  function startHeroEdit(field) {
    setHeroDraft(field === "title" ? (heroTitle || DEFAULT_HERO_TITLE) : (heroSub || DEFAULT_HERO_SUB));
    setEditingHero(field);
  }

  function saveHeroEdit() {
    if (editingHero === "title") {
      setHeroTitle(heroDraft);
      localStorage.setItem("portfolio_hero_title", heroDraft);
    } else {
      setHeroSub(heroDraft);
      localStorage.setItem("portfolio_hero_sub", heroDraft);
    }
    setEditingHero(null);
  }

  function cancelHeroEdit() { setEditingHero(null); }

  const e = (emoji) => showEmojis ? emoji : null;

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setAuthed(false); return; }
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (r.ok) setAuthed(true); else { localStorage.removeItem("token"); setAuthed(false); } })
      .catch(() => { localStorage.removeItem("token"); setAuthed(false); });
  }, []);

  useEffect(() => {
    if (authed === true) {
      load();
      apiFetch("/portfolio/visibility")
        .then(d => setPortfolioPublic(d.portfolio_public))
        .catch(() => {});
      apiFetch("/portfolio/about")
        .then(d => {
          if (d.about_name)     { setHeroTitle(d.about_name);    localStorage.setItem("portfolio_hero_title", d.about_name); }
          if (d.about_subtitle) { setHeroSub(d.about_subtitle);  localStorage.setItem("portfolio_hero_sub",   d.about_subtitle); }
          if (d.about_bio)      setAboutBio(d.about_bio);
        })
        .catch(() => {});
      apiFetch("/education")
        .then(d => setEducationEntries(sortEdu(d.education || [])))
        .catch(() => {});
      apiFetch("/work-history")
        .then(d => setExpEntries(sortExp(d.work_history || [])))
        .catch(() => {});
      apiFetch("/portfolio/contact")
        .then(d => setContactInfo(normalizeContactInfo(d.contact_info || {})))
        .catch(() => {});
    }
  }, [authed, includeHidden]);

  async function togglePortfolioPublic() {
    setVisibilityLoading(true);
    try {
      const d = await apiFetch("/portfolio/visibility", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ portfolio_public: !portfolioPublic }),
      });
      setPortfolioPublic(d.portfolio_public);
      setMsg({ type: "success", text: d.portfolio_public ? "Portfolio is now public!" : "Portfolio is now private." });
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setVisibilityLoading(false); }
  }

  const [saveStatus, setSaveStatus] = useState("idle");
  const aboutSaveTimer = React.useRef(null);
  const savedTimer = React.useRef(null);
  function saveAbout(field, value) {
    clearTimeout(aboutSaveTimer.current);
    aboutSaveTimer.current = setTimeout(() => {
      apiFetch("/portfolio/about", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [field]: value }),
      })
        .then(() => {
          setSaveStatus("saved");
          clearTimeout(savedTimer.current);
          savedTimer.current = setTimeout(() => setSaveStatus("idle"), 2000);
        })
        .catch(() => {});
    }, 800);
  }

  function sortEdu(entries) {
    return [...entries].sort((a, b) => {
      const da = a.start_date ? new Date(a.start_date) : new Date(0);
      const db = b.start_date ? new Date(b.start_date) : new Date(0);
      return db - da; // most recent first
    });
  }

  async function addEducation() {
    setEduError(null);
    const f = eduForm;
    // Validation per type
    if (eduFormType === "secondary") {
      if (!f.institution || !f.end_date) { setEduError("School name and graduation year are required."); return; }
    } else if (eduFormType === "certifications") {
      if (!f.institution || !f.topic || !f.start_date) { setEduError("Issuing organization, certification name and issue date are required."); return; }
    } else if (eduFormType === "extracurricular") {
      if (!f.institution || !f.topic || !f.start_date) { setEduError("Club/team, role and start date are required."); return; }
    } else {
      if (!f.institution || !f.degree_type || !f.topic || !f.start_date) {
        setEduError("Institution, degree type, field of study and start date are required."); return;
      }
    }
    // Build payload
    let degree_type, topic, start_date, end_date;
    const details = f.awards ? f.awards.split("\n").map(s => s.trim()).filter(Boolean) : [];
    if (eduFormType === "secondary") {
      degree_type = f.degree_type || "Secondary School Diploma";
      topic       = "General Studies";
      const gradYear = parseInt(f.end_date);
      end_date   = `${f.end_date}-06-01`;
      start_date = `${gradYear - 3}-09-01`;
    } else if (eduFormType === "certifications") {
      degree_type = "Certification";
      topic       = f.topic;
      start_date  = f.start_date ? `${f.start_date}-01` : f.start_date;
      end_date    = f.end_date   ? `${f.end_date}-01`   : null;
    } else if (eduFormType === "extracurricular") {
      degree_type = "Extra Curricular";
      topic       = f.topic;
      start_date  = f.start_date ? `${f.start_date}-01` : f.start_date;
      end_date    = f.end_date   ? `${f.end_date}-01`   : null;
    } else {
      degree_type = f.degree_type;
      topic       = f.topic;
      start_date  = f.start_date ? `${f.start_date}-01` : f.start_date;
      end_date    = f.end_date   ? `${f.end_date}-01`   : null;
    }
    try {
      const d = await apiFetch("/education", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          institution: f.institution,
          degree_type,
          topic,
          start_date,
          end_date,
          location: f.location || null,
          gpa: f.gpa || null,
          details: details.length ? details : null,
        }),
      });
      setEducationEntries(prev => sortEdu([...prev, d.education]));
      setEduForm({ institution: "", degree_type: "", topic: "", start_date: "", end_date: "", location: "", gpa: "", awards: "" });
      setShowEduForm(false);
    } catch (e) { setEduError(e.message); }
  }

  async function deleteEducation(id) {
    try {
      await apiFetch(`/education/${id}`, { method: "DELETE" });
      setEducationEntries(prev => prev.filter(e => e.id !== id));
    } catch (e) { setEduError(e.message); }
  }

  function startEditEdu(entry) {
    const toYM = (s) => s ? s.substring(0, 7) : "";
    const entryType = educationEntryTypeOf(entry);
    setEditEduId(entry.id);
    setEditEduError(null);
    setEditEduForm({
      entryType,
      institution: entry.institution || "",
      degree_type: entry.degree_type || "",
      topic: entry.topic || "",
      start_date: toYM(entry.start_date),
      end_date: toYM(entry.end_date),
      location: entry.location || "",
      gpa: entry.gpa || "",
      awards: (entry.details || []).join("\n"),
    });
  }

  async function saveEditEdu(id) {
    setEditEduError(null);
    const f = editEduForm;
    const details = f.awards ? f.awards.split("\n").map(s => s.trim()).filter(Boolean) : [];
    const cleanStart = (f.start_date || "").trim();
    const cleanEnd = (f.end_date || "").trim();
    let degree_type, topic, start_date, end_date;
    if (f.entryType === "secondary") {
      degree_type = f.degree_type || "Secondary School Diploma";
      topic = "General Studies";
      const gradYear = parseInt(cleanEnd);
      end_date = cleanEnd ? `${cleanEnd}-01-01` : null;
      start_date = `${gradYear - 3}-09-01`;
    } else if (f.entryType === "certifications") {
      degree_type = "Certification";
      topic = f.topic;
      start_date = cleanStart ? `${cleanStart}-01` : null;
      end_date = cleanEnd ? `${cleanEnd}-01` : null;
    } else if (f.entryType === "extracurricular") {
      degree_type = "Extra Curricular";
      topic = f.topic;
      start_date = cleanStart ? `${cleanStart}-01` : null;
      end_date = cleanEnd ? `${cleanEnd}-01` : null;
    } else {
      degree_type = f.degree_type;
      topic = f.topic;
      start_date = cleanStart ? `${cleanStart}-01` : null;
      end_date = cleanEnd ? `${cleanEnd}-01` : null;
    }
    try {
      const d = await apiFetch("/education", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          institution: f.institution, degree_type, topic, start_date, end_date,
          location: f.location || null, gpa: f.gpa || null,
          details: details.length ? details : null,
        }),
      });
      await apiFetch(`/education/${id}`, { method: "DELETE" });
      setEducationEntries(prev => sortEdu([...prev.filter(e => e.id !== id), d.education]));
      setEditEduId(null);
    } catch (e) { setEditEduError(e.message); }
  }

  function sortExp(entries) {
    return [...entries].sort((a, b) => {
      const da = a.start_date ? new Date(a.start_date) : new Date(0);
      const db = b.start_date ? new Date(b.start_date) : new Date(0);
      return db - da;
    });
  }

  async function addExperience() {
    setExpError(null);
    const f = expForm;
    const orgLabel = expFormType === "volunteering" ? "Organization" : "Company";
    const roleLabel = expFormType === "volunteering" ? "role" : "job title";
    if (!f.company || !f.role || !f.start_date) {
      setExpError(`${orgLabel}, ${roleLabel} and start date are required.`); return;
    }
    const start_date = `${f.start_date}-01`;
    const end_date   = f.end_date ? `${f.end_date}-01` : null;
    try {
      const d = await apiFetch("/work-history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company: f.company, role: f.role, experience_type: expFormType, start_date, end_date, location: f.location || null }),
      });
      setExpEntries(prev => sortExp([...prev, d.work_history]));
      setExpForm({ company: "", role: "", start_date: "", end_date: "", location: "" });
      setShowExpForm(false);
    } catch (e) { setExpError(e.message); }
  }

  async function deleteExperience(id) {
    try {
      await apiFetch(`/work-history/${id}`, { method: "DELETE" });
      setExpEntries(prev => prev.filter(e => e.id !== id));
    } catch (e) { setExpError(e.message); }
  }

  function startEditExp(entry) {
    const toYM = (s) => s ? s.substring(0, 7) : "";
    const expType = experienceTypeOf(entry);
    setEditExpId(entry.id);
    setEditExpError(null);
    setEditExpForm({
      experience_type: expType,
      company: entry.company || "",
      role: entry.role || "",
      start_date: toYM(entry.start_date),
      end_date: entry.end_date === "Present" ? "" : toYM(entry.end_date),
      location: entry.location || "",
    });
  }

  async function saveEditExp(id) {
    setEditExpError(null);
    const f = editExpForm;
    if (!f.company || !f.role || !f.start_date) {
      setEditExpError("Company/organization, role/title, and start date are required.");
      return;
    }
    const start_date = `${(f.start_date || "").trim()}-01`;
    const end_date = (f.end_date || "").trim() ? `${f.end_date.trim()}-01` : null;
    try {
      const d = await apiFetch("/work-history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: f.company,
          role: f.role,
          experience_type: f.experience_type || "work",
          start_date,
          end_date,
          location: f.location || null,
        }),
      });
      await apiFetch(`/work-history/${id}`, { method: "DELETE" });
      setExpEntries(prev => sortExp([...prev.filter(e => e.id !== id), d.work_history]));
      setEditExpId(null);
    } catch (e) { setEditExpError(e.message); }
  }

  if (authed === null) return <div className="page-wrap port-loading-text" style={{ paddingTop: 80, textAlign: "center" }}>Checking authentication...</div>;

  if (authed === false) return (
    <div className="page-wrap">
      <div className="resume-auth-wall card">
        <div className="resume-auth-icon">🎨</div>
        <h2>Portfolio</h2>
        <p className="text-muted">This feature requires an account. Sign in or create an account to generate and share your portfolio.</p>
        <a className="btn-primary" href="/settings">Sign In / Sign Up →</a>
      </div>
    </div>
  );

  async function load() {
    setLoading(true);
    try {
      const d = await apiFetch(`/portfolio?include_hidden=${includeHidden}`);
      setPortfolio(d);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function generate() {
    setGenerating(true); setMsg(null);
    try {
      await apiFetch(`/portfolio/generate?include_hidden=${includeHidden}`, { method: "POST" });
      setMsg({ type: "success", text: "Portfolio regenerated!" });
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setGenerating(false); }
  }

  async function saveEdit(id) {
    const toArr = s => (s || "").split(",").map(t => t.trim()).filter(Boolean);
    const payload = {
      ...editForm,
      languages:  toArr(editForm.languages),
      frameworks: toArr(editForm.frameworks),
      skills:     toArr(editForm.skills),
      tags:       toArr(editForm.tags),
    };
    if (payload.importance_score === "" || payload.importance_score == null) {
      delete payload.importance_score;
    } else {
      payload.importance_score = parseFloat(payload.importance_score);
    }
    try {
      await apiFetch(`/portfolio/${id}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setMsg({ type: "success", text: "Saved!" });
      setEditId(null);
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function toggleHidden(p) {
    try {
      await apiFetch(`/portfolio/${p.id}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_hidden: !p.is_hidden }),
      });
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function saveRank(id) {
    const rank = parseFloat(rankInput[id]);
    if (isNaN(rank)) return;
    try {
      await apiFetch(`/portfolio/${id}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ importance_score: rank }),
      });
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  function startEdit(p) {
    setEditId(p.id);
    const techSet = new Set([
      ...(p.languages || []).map(s => s.toLowerCase()),
      ...(p.frameworks || []).map(s => s.toLowerCase()),
    ]);
    const pureSkills = (p.skills || []).filter(s => !techSet.has(s.toLowerCase()));
    setEditForm({
      custom_description: p.description || "",
      is_featured: p.is_featured || false,
      is_hidden: p.is_hidden || false,
      importance_score: p.importance_score ?? "",
      user_role: p.user_role || "",
      success_evidence: p.success_evidence || "",
      languages: (p.languages || []).join(", "),
      frameworks: (p.frameworks || []).join(", "),
      skills: pureSkills.join(", "),
      tags: (p.tags || []).join(", "),
    });
  }

  const isPublic = viewMode === "public";
  const projects = portfolio?.projects || [];
  const expLegendItems = [
    ["work", "Work"],
    ["internship", "Internship"],
    ["volunteering", "Volunteering"],
    ["freelance", "Freelance / Contract"],
  ];

  const projectTypes = ["all", ...Array.from(new Set(projects.map(p => p.type || p.project_type).filter(Boolean)))];

  const sorted = [...projects]
    .filter(p => {
      if (isPublic) {
        const q = search.toLowerCase();
        const matchesSearch = !q ||
          (p.name || "").toLowerCase().includes(q) ||
          (p.description || "").toLowerCase().includes(q) ||
          (p.user_role || "").toLowerCase().includes(q) ||
          (p.skills || []).some(s => s.toLowerCase().includes(q)) ||
          (p.languages || p.tech_stack || []).some(t => t.toLowerCase().includes(q));
        const matchesType = typeFilter === "all" || (p.type || p.project_type) === typeFilter;
        return matchesSearch && matchesType;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "importance") return (b.importance_score || 0) - (a.importance_score || 0);
      if (sortBy === "rank")       return (a.user_rank ?? 999) - (b.user_rank ?? 999);
      if (sortBy === "name")       return (a.name || "").localeCompare(b.name || "");
      if (sortBy === "date")       return new Date(b.date || 0) - new Date(a.date || 0);
      return 0;
    });

  const featured = sorted.filter(p => p.is_featured);
  const rest     = sorted.filter(p => !p.is_featured);
  const stats    = portfolio?.stats || {};
  const summaryText = portfolio?.summary_text || portfolio?.summary?.text || "";

  return (
    <div className="port-sidebar-layout">

      {/* ── Side Navbar ── */}
      <aside className="port-sidebar">
        <nav className="port-nav-list">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`port-nav-item ${activeSection === item.id ? "active" : ""}`}
              onClick={() => setActiveSection(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="port-sidebar-controls">
          <span className="port-sidebar-controls-label">View Mode</span>
          <div className="port-mode-switcher port-mode-switcher-vert">
            <button
              className={`port-mode-btn ${!isPublic ? "active private" : ""}`}
              onClick={() => switchMode("private")}
              title="Edit and rearrange your portfolio"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              Private
            </button>
            <button
              className={`port-mode-btn ${isPublic ? "active public" : ""}`}
              onClick={() => switchMode("public")}
              title="View public portfolio"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
              Public
            </button>
          </div>
          <Link to="/public-portfolios" className="btn-secondary port-sidebar-link-btn" style={{ textDecoration: "none", textAlign: "center" }}>
            Browse Others
          </Link>
          {isPublic && (
            <button
              className={`${portfolioPublic ? "btn-primary" : "btn-secondary"} port-sidebar-link-btn`}
              onClick={togglePortfolioPublic}
              disabled={visibilityLoading}
              title={portfolioPublic ? "Your portfolio is publicly listed — click to make private" : "Make your portfolio publicly visible to others"}
            >
              {visibilityLoading ? "…" : portfolioPublic ? "Listed Public ✓" : "Make Public"}
            </button>
          )}
          {!isPublic && (
            <>
              <button className="btn-primary port-sidebar-link-btn" onClick={generate} disabled={generating}>
                {generating ? "Generating…" : "↻ Regenerate"}
              </button>
            </>
          )}
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="port-main">
        {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

        {/* About Me */}
        {activeSection === "about" && (
          <div className="port-about-wrapper">
            <div className="port-about-hero">

              {/* Left: avatar + identity + cta */}
              <div className="port-about-left">
                <div className="port-about-avatar" style={profileAvatar ? { backgroundImage: `url(${profileAvatar})`, backgroundSize: "cover", backgroundPosition: "center", fontSize: 0 } : {}}>
                  {!profileAvatar && (heroTitle || "?").charAt(0).toUpperCase()}
                </div>
                <div className="port-about-identity">
                  {isPublic ? (
                    <p className="port-about-name-text">{heroTitle || "—"}</p>
                  ) : (
                    <input
                      className="port-about-name-input"
                      placeholder="Your name"
                      value={heroTitle}
                      onChange={ev => { setHeroTitle(ev.target.value); localStorage.setItem("portfolio_hero_title", ev.target.value); saveAbout("about_name", ev.target.value); }}
                      maxLength={60}
                    />
                  )}
                  {isPublic ? (
                    heroSub && <p className="port-about-sub-text">{heroSub}</p>
                  ) : (
                    <input
                      className="port-about-sub-input"
                      placeholder="Title or role"
                      value={heroSub}
                      onChange={ev => { setHeroSub(ev.target.value); localStorage.setItem("portfolio_hero_sub", ev.target.value); saveAbout("about_subtitle", ev.target.value); }}
                      maxLength={80}
                    />
                  )}
                </div>
                <Link to="/showcase" className="btn-primary port-about-showcase-btn" style={{ textDecoration: "none", color: "#fff" }}>
                  Web Showcase →
                </Link>
              </div>

              {/* Right: bio */}
              {(!isPublic || aboutBio) && (
                <div className="port-about-right">
                  <div className="port-about-bio-section">
                    <span className="port-about-bio-label">About</span>
                    {isPublic ? (
                      <p className="port-about-bio-text">{aboutBio}</p>
                    ) : (
                      <div className="port-about-bio-wrap">
                        <textarea
                          className="port-about-bio-input"
                          placeholder="Write a short bio — your background, what you're building, and what drives you…"
                          value={aboutBio}
                          onChange={ev => { setAboutBio(ev.target.value); saveAbout("about_bio", ev.target.value); }}
                          rows={7}
                          maxLength={800}
                        />
                        <span className="port-about-char-count">{aboutBio.length} / 800</span>
                      </div>
                    )}
                    <span className="port-about-saved" style={{ opacity: saveStatus === "saved" ? undefined : 0, animation: saveStatus === "saved" ? undefined : "none" }}>Saved ✓</span>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

        {/* Projects */}
        {activeSection === "projects" && (
          <div className="port-section-page">
            {loading ? <div className="spinner" style={{ marginTop: 40 }} /> : <>
              {summaryText && <p className="port-hero-summary" style={{ marginBottom: 24 }}>{summaryText}</p>}

              {isPublic && (
                <div className="port-public-toolbar">
                  <div className="port-search-wrap">
                    <svg className="port-search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    <input
                      className="port-search-input"
                      type="text"
                      placeholder="Search projects, skills, technologies…"
                      value={search}
                      onChange={ev => setSearch(ev.target.value)}
                    />
                    {search && <button className="port-search-clear" onClick={() => setSearch("")} title="Clear">✕</button>}
                  </div>
                  <div className="port-type-chips">
                    {projectTypes.map(t => (
                      <button key={t} className={`port-type-chip ${typeFilter === t ? "active" : ""}`} onClick={() => setTypeFilter(t)}>
                        {t === "all" ? "All" : t}
                      </button>
                    ))}
                  </div>
                  {(search || typeFilter !== "all") && (
                    <span className="port-result-count">{sorted.length} result{sorted.length !== 1 ? "s" : ""}</span>
                  )}
                </div>
              )}

              {projects.length > 0 && (
                <div className="port-sort-row">
                  <span className="port-sort-label">Sort by</span>
                  <div className="port-sort-group">
                    {SORT_OPTIONS.map(o => (
                      <button key={o.value}
                        className={`port-sort-pill ${sortBy === o.value ? "active" : ""}`}
                        onClick={() => setSortBy(o.value)}>
                        {o.label}
                      </button>
                    ))}
                  </div>
                  <div className="port-layout-toggle">
                    <button className={`port-layout-btn ${layout === "list" ? "active" : ""}`} onClick={() => setLayoutPersist("list")} title="List view">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                    </button>
                    <button className={`port-layout-btn ${layout === "grid" ? "active" : ""}`} onClick={() => setLayoutPersist("grid")} title="Grid view">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                    </button>
                  </div>
                  {!isPublic && (
                    <label className="toggle-label" style={{ marginLeft: 8 }}>
                      <input type="checkbox" checked={includeHidden} onChange={e => setIncludeHidden(e.target.checked)} />
                      Show hidden
                    </label>
                  )}
                </div>
              )}

              {projects.length === 0 ? (
                <div className="empty-state port-empty-illustrated">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "#6366f1", opacity: 0.6, marginBottom: 16 }}>
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                  </svg>
                  <p className="port-empty-heading" style={{ fontWeight: 700, fontSize: "1.05rem", margin: 0 }}>No portfolio data yet</p>
                  <p className="port-empty-body" style={{ marginTop: 8, fontSize: "0.88rem", maxWidth: 280, margin: "8px auto 0" }}>Hit <strong className="port-accent-text">Regenerate</strong> to mine your projects and build your portfolio automatically.</p>
                </div>
              ) : sorted.length === 0 && isPublic ? (
                <div className="port-no-results">
                  <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: "#6b7a99", marginBottom: 12 }}>
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <p>No projects match <strong className="port-accent-text">{search || typeFilter}</strong></p>
                  <button className="btn-secondary" style={{ marginTop: 12, fontSize: "0.82rem" }} onClick={() => { setSearch(""); setTypeFilter("all"); }}>Clear filters</button>
                </div>
              ) : (
                <>
                  {featured.length > 0 && (
                    <div className="port-section">
                      <div className="port-section-header port-section-header-featured">
                        <span>{e("⭐ ")}Featured Projects</span>
                      </div>
                      <div className="port-top-grid">
                        {featured.map((p, i) => <ProjectCard key={p.id} p={p} rank={i + 1} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} isPublic={isPublic} toggleHidden={toggleHidden} />)}
                      </div>
                    </div>
                  )}
                  <div className="port-section">
                    <div className="port-section-header">
                      <span>{featured.length > 0 ? "All Other Projects" : "All Projects"}</span>
                      <span className="port-section-count">{rest.length}</span>
                    </div>
                    {layout === "grid" ? (
                      <div className="port-top-grid">
                        {rest.map((p, i) => <ProjectCard key={p.id} p={p} rank={featured.length + i + 1} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} isPublic={isPublic} toggleHidden={toggleHidden} />)}
                      </div>
                    ) : (
                      <div className="port-all-list">
                        {rest.map(p => <ProjectRow key={p.id} p={p} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} isPublic={isPublic} toggleHidden={toggleHidden} />)}
                      </div>
                    )}
                  </div>
                </>
              )}
            </>}
          </div>
        )}

        {/* Skills & Stats */}
        {activeSection === "skills" && (
          <div className="port-section-page">
            {projects.length > 0 && (() => {
              const skillMap = {};
              projects.forEach(p => {
                [...new Set([...(p.skills || []), ...(p.languages || []), ...(p.frameworks || [])])].forEach(s => {
                  const key = s.toLowerCase().trim();
                  if (!key) return;
                  if (!skillMap[key]) skillMap[key] = { name: s, count: 0 };
                  skillMap[key].count++;
                });
              });
              const allSkills = Object.values(skillMap).sort((a, b) => b.count - a.count);
              return (
                <div className="port-viz-card card" style={{ marginBottom: 16 }}>
                  <div className="port-section-header">
                    <span>All Skills</span>
                    <span className="port-section-count">{allSkills.length}</span>
                  </div>
                  <div className="port-skills-cloud">
                    {allSkills.map(({ name, count }) => {
                      const tc = typeColor(name);
                      return (
                        <span key={name} className="port-skill-chip" style={{ color: tc, borderColor: `${tc}55`, background: `${tc}15` }}>
                          {name}
                          {count > 1 && <span className="port-skill-chip-count" style={{ background: `${tc}30`, color: tc }}>{count}</span>}
                        </span>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
            {Object.keys(stats).length > 0 && (
              <div className="port-stat-row" style={{ marginBottom: 24 }}>
                {[
                  ["Projects", stats.total_projects ?? projects.length],
                  ["Lines of Code", stats.total_lines_of_code > 0 ? stats.total_lines_of_code?.toLocaleString() : null],
                  ["Files",      stats.total_files?.toLocaleString()],
                  ["Word Count", stats.total_word_count > 0 ? stats.total_word_count?.toLocaleString() : null],
                  ["Skills",     stats.unique_skills_count ?? portfolio?.unique_skills_count],
                ].filter(([, v]) => v != null).map(([label, val]) => (
                  <div key={label} className="port-stat card">
                    {e(<div className="port-stat-icon">{STAT_ICONS[label]}</div>)}
                    <div className="stat-val">{val}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>
            )}
            <div className="port-viz-card card">
              <div className="port-section-header port-section-header-btn" onClick={() => setShowTimeline(v => !v)} style={{ cursor: "pointer", userSelect: "none" }}>
                <span>📈 Skills Timeline</span>
                <span className="port-viz-chevron" style={{ transform: showTimeline ? "rotate(0deg)" : "rotate(-90deg)" }}>▾</span>
              </div>
              {showTimeline && <SkillsTimeline />}
            </div>
            <div className="port-viz-card card" style={{ marginTop: 16 }}>
              <div className="port-section-header port-section-header-btn" onClick={() => setShowHeatmap(v => !v)} style={{ cursor: "pointer", userSelect: "none" }}>
                <span>🗓️ Project Activity</span>
                <span className="port-viz-chevron" style={{ transform: showHeatmap ? "rotate(0deg)" : "rotate(-90deg)" }}>▾</span>
              </div>
              {showHeatmap && <ActivityHeatmap />}
            </div>
          </div>
        )}

        {/* Experience */}
        {activeSection === "experience" && (
          <div className="port-section-page edu-page">
            {/* Top bar */}
            {(() => {
              const activeRoles = expEntries.filter(entry => !entry.end_date || entry.end_date === "Present").length;
              return (
                <div className="edu-top-bar">
                  <div className="edu-top-titles">
                    {isPublic
                      ? <h1 className="edu-split-title">{expTitle || "Experience"}</h1>
                      : <input className="edu-split-title-input" value={expTitle} onChange={e => { setExpTitle(e.target.value); localStorage.setItem("exp_title", e.target.value); }} placeholder="Section Title" />}
                    {isPublic
                      ? expSubtitle && <p className="edu-split-subtitle">{expSubtitle}</p>
                      : <input className="edu-split-subtitle-input" value={expSubtitle} onChange={e => { setExpSubtitle(e.target.value); localStorage.setItem("exp_subtitle", e.target.value); }} placeholder="Subtitle" />}
                    <div className="edu-top-stats">
                      <div className="edu-top-stat">
                        <span className="edu-top-stat-num">{expEntries.length}</span>
                        <span className="edu-top-stat-label">{expEntries.length === 1 ? "Position" : "Positions"}</span>
                      </div>
                      <div className="edu-top-stat">
                        <span className="edu-top-stat-num">{activeRoles}</span>
                        <span className="edu-top-stat-label">{activeRoles === 1 ? "Current Role" : "Current Roles"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Split body */}
            <div className="edu-body">
              {/* Left: description + form */}
              <div className="edu-body-left">
                {(!isPublic || expDesc) && (
                  isPublic
                    ? <p className="edu-split-desc">{expDesc}</p>
                    : <div className="port-about-bio-wrap">
                        <textarea
                          className="port-about-bio-input"
                          placeholder="Describe your work history, volunteering, or anything you'd like visitors to know…"
                          value={expDesc}
                          onChange={e => { setExpDesc(e.target.value); localStorage.setItem("exp_desc", e.target.value); }}
                          rows={6}
                          maxLength={600}
                        />
                        <span className="port-about-char-count">{expDesc.length} / 600</span>
                      </div>
                )}
                {!isPublic && (
                  <div style={{ marginTop: 20 }}>
                    {!showExpForm ? (
                      <button className="btn-primary edu-add-btn" onClick={() => setShowExpForm(true)}>+ Add to Timeline</button>
                    ) : (
                      <div className="edu-form card">
                        {/* Type tabs */}
                        <div className="edu-form-tabs">
                          {[["work","Work"],["internship","Internship"],["volunteering","Volunteering"],["freelance","Freelance / Contract"]].map(([val, label]) => (
                            <button key={val} className={`edu-form-tab ${expFormType === val ? "active" : ""}`}
                              onClick={() => { setExpFormType(val); setExpForm({ company: "", role: "", start_date: "", end_date: "", location: "" }); setExpError(null); }}>
                              {label}
                            </button>
                          ))}
                        </div>

                        {expError && <div className="alert error" style={{ marginBottom: 12 }}>{expError}</div>}

                        <div className="edu-form-grid">
                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                            {expFormType === "volunteering" ? "Organization *" : expFormType === "freelance" ? "Client / Company" : "Company *"}
                            <input className="edu-form-input"
                              placeholder={
                                expFormType === "volunteering" ? "e.g. Red Cross, Local Food Bank"
                                : expFormType === "freelance" ? "e.g. Self-employed, Acme Corp"
                                : "e.g. Google, Startup Inc."}
                              value={expForm.company} onChange={e => setExpForm(f => ({ ...f, company: e.target.value }))} />
                          </label>
                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                            {expFormType === "volunteering" ? "Role / Position *" : expFormType === "freelance" ? "Project / Role *" : "Job Title *"}
                            <input className="edu-form-input"
                              placeholder={
                                expFormType === "volunteering" ? "e.g. Event Coordinator"
                                : expFormType === "freelance" ? "e.g. Full-stack Developer"
                                : expFormType === "internship" ? "e.g. Software Engineering Intern"
                                : "e.g. Software Engineer"}
                              value={expForm.role} onChange={e => setExpForm(f => ({ ...f, role: e.target.value }))} />
                          </label>
                          <label className="edu-form-label">
                            <span className="edu-date-field-head">
                              <span>Start Date *</span>
                            </span>
                            <MonthPicker value={expForm.start_date} onChange={v => setExpForm(f => ({ ...f, start_date: v }))} />
                          </label>
                          <DateToggleField
                            label="End Date"
                            value={expForm.end_date}
                            onChange={v => setExpForm(f => ({ ...f, end_date: v }))}
                            toggleLabel="Present"
                          />
                          <label className="edu-form-label">
                            Location
                            <input className="edu-form-input" placeholder="e.g. Vancouver, BC"
                              value={expForm.location} onChange={e => setExpForm(f => ({ ...f, location: e.target.value }))} />
                          </label>
                        </div>

                        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                          <button className="btn-primary" onClick={addExperience}>Add Entry</button>
                          <button className="btn-secondary" onClick={() => { setShowExpForm(false); setExpError(null); }}>Cancel</button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Right: timeline */}
              <div className="edu-body-right">
                {expEntries.length === 0 ? (
                  <div className="edu-empty-state">
                    <span className="edu-empty-icon">💼</span>
                    <p className="edu-empty-title">No experience yet</p>
                    <p className="edu-empty-sub">Add your work history, internships, or volunteering to get started.</p>
                  </div>
                ) : (
                  <>
                    <div className="edu-legend edu-legend-inline">
                      {expLegendItems.map(([value, label]) => (
                        <span key={value} className="edu-legend-item">
                          <span className={`edu-legend-dot exp-legend-${value}`} />
                          {label}
                        </span>
                      ))}
                    </div>
                    <div className="edu-timeline-list">
                      <div className="edu-timeline-line" />
                      {expEntries.map((entry, i) => {
                        const startDate = entry.start_date ? new Date(entry.start_date) : null;
                        const endDate = entry.end_date && entry.end_date !== "Present" ? new Date(entry.end_date) : null;
                        const isPresent = !entry.end_date || entry.end_date === "Present";
                        const start = startDate ? startDate.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "?";
                        const end = endDate ? endDate.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "Present";
                        const expType = experienceTypeOf(entry);
                        const companyLabel = expType === "volunteering" ? "Organization *" : expType === "freelance" ? "Client / Company" : "Company *";
                        const roleLabel = expType === "volunteering" ? "Role / Position *" : expType === "freelance" ? "Project / Role *" : "Job Title *";
                        return (
                          <div key={entry.id} className="edu-timeline-item">
                            <div className={`edu-timeline-dot exp-dot-${expType}`} />
                            <div className={`edu-timeline-content card edu-card-wrap exp-card-${expType}`}>
                              {!isPublic && editExpId !== entry.id && (
                                <div className="edu-card-actions">
                                  <button className="edu-edit-btn" onClick={() => startEditExp(entry)} title="Edit entry">✎</button>
                                  <button className="edu-delete-btn" onClick={() => deleteExperience(entry.id)} title="Remove entry">✕</button>
                                </div>
                              )}
                              {editExpId === entry.id ? (
                                <div className="edu-inline-edit">
                                  <div className="edu-inline-edit-grid">
                                    <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                      {companyLabel}
                                      <input className="edu-form-input" value={editExpForm.company || ""} onChange={e => setEditExpForm(f => ({ ...f, company: e.target.value }))} />
                                    </label>
                                    <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                      {roleLabel}
                                      <input className="edu-form-input" value={editExpForm.role || ""} onChange={e => setEditExpForm(f => ({ ...f, role: e.target.value }))} />
                                    </label>
                                    <label className="edu-form-label">
                                      <span className="edu-date-field-head">
                                        <span>Start Date *</span>
                                      </span>
                                      <MonthPicker value={editExpForm.start_date || ""} onChange={v => setEditExpForm(f => ({ ...f, start_date: v }))} />
                                    </label>
                                    <DateToggleField
                                      label="End Date"
                                      value={editExpForm.end_date || ""}
                                      onChange={v => setEditExpForm(f => ({ ...f, end_date: v }))}
                                      toggleLabel="Present"
                                    />
                                    <label className="edu-form-label">
                                      Location
                                      <input className="edu-form-input" value={editExpForm.location || ""} onChange={e => setEditExpForm(f => ({ ...f, location: e.target.value }))} />
                                    </label>
                                  </div>
                                  {editExpError && <p style={{ color: "#f87171", fontSize: "0.8rem", marginTop: 8 }}>{editExpError}</p>}
                                  <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                                    <button className="btn-primary" style={{ fontSize: "0.8rem", padding: "6px 16px" }} onClick={() => saveEditExp(entry.id)}>Save</button>
                                    <button className="btn-secondary" style={{ fontSize: "0.8rem", padding: "6px 16px" }} onClick={() => { setEditExpId(null); setEditExpError(null); }}>Cancel</button>
                                  </div>
                                </div>
                              ) : (
                                <div className="edu-timeline-top">
                                  <div>
                                    <p className="edu-institution">{entry.company}</p>
                                    <p className="edu-degree">{entry.role}</p>
                                  </div>
                                  <div style={{ textAlign: "right", flexShrink: 0 }}>
                                    <p className="edu-dates">
                                      {start} — {isPresent ? <span className="edu-present-pill"><span className="edu-present-dot" />Present</span> : end}
                                    </p>
                                    {entry.location && <p className="text-muted" style={{ fontSize: "0.78rem" }}>{entry.location}</p>}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Education */}
        {activeSection === "education" && (
          <div className="port-section-page edu-page">
            {/* Top bar: stat card + title + subtitle */}
            {(() => {
              const degreeCount = educationEntries.filter(entry => (
                entry.degree_type !== "Certification" && entry.degree_type !== "Extra Curricular"
              )).length;
              const certificationCount = educationEntries.filter(entry => entry.degree_type === "Certification").length;
              const extracurricularCount = educationEntries.filter(entry => entry.degree_type === "Extra Curricular").length;
              return (
            <div className="edu-top-bar">
              <div className="edu-top-titles">
                {isPublic
                  ? <h1 className="edu-split-title">{eduTitle || "Education"}</h1>
                  : <input className="edu-split-title-input" value={eduTitle} onChange={e => { setEduTitle(e.target.value); localStorage.setItem("edu_title", e.target.value); }} placeholder="Section Title" />}
                {isPublic
                  ? eduSubtitle && <p className="edu-split-subtitle">{eduSubtitle}</p>
                  : <input className="edu-split-subtitle-input" value={eduSubtitle} onChange={e => { setEduSubtitle(e.target.value); localStorage.setItem("edu_subtitle", e.target.value); }} placeholder="Subtitle" />}
                  <div className="edu-top-stats">
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{degreeCount}</span>
                    <span className="edu-top-stat-label">{degreeCount === 1 ? "Degree" : "Degrees"}</span>
                  </div>
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{certificationCount}</span>
                    <span className="edu-top-stat-label">{certificationCount === 1 ? "Certification" : "Certifications"}</span>
                  </div>
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{extracurricularCount}</span>
                    <span className="edu-top-stat-label">Extra Curricular</span>
                  </div>
                </div>
              </div>
            </div>
              );
            })()}

            {/* Split body */}
            <div className="edu-body">
              {/* Left: description */}
              <div className="edu-body-left">
                {(!isPublic || eduDesc) && (
                  isPublic
                    ? <p className="edu-split-desc">{eduDesc}</p>
                    : <div className="port-about-bio-wrap">
                        <textarea
                          className="port-about-bio-input"
                          placeholder="Describe your academic background, goals, or anything you'd like visitors to know…"
                          value={eduDesc}
                          onChange={e => { setEduDesc(e.target.value); localStorage.setItem("edu_desc", e.target.value); }}
                          rows={6}
                          maxLength={600}
                        />
                        <span className="port-about-char-count">{eduDesc.length} / 600</span>
                      </div>
                )}
                {!isPublic && (
                  <div style={{ marginTop: 20 }}>
                    {!showEduForm ? (
                      <button className="btn-primary edu-add-btn" onClick={() => setShowEduForm(true)}>+ Add to Timeline</button>
                    ) : (
                      <div className="edu-form card">
                        {/* Type tabs */}
                        <div className="edu-form-tabs">
                          {[["postsecondary","Post Secondary"],["secondary","Secondary"],["certifications","Certifications"],["extracurricular","Extra Curricular"]].map(([val, label]) => (
                            <button key={val} className={`edu-form-tab ${eduFormType === val ? "active" : ""}`}
                              onClick={() => { setEduFormType(val); setEduForm({ institution: "", degree_type: "", topic: "", start_date: "", end_date: "", location: "", gpa: "", awards: "" }); setEduError(null); }}>
                              {label}
                            </button>
                          ))}
                        </div>

                        {eduError && <div className="alert error" style={{ marginBottom: 12 }}>{eduError}</div>}

                        <div className="edu-form-grid">
                          {/* Row 1: institution / org label varies */}
                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                            { eduFormType === "secondary" ? "School Name *"
                            : eduFormType === "extracurricular" ? "Club / Team / Organization *"
                            : eduFormType === "certifications" ? "Issuing Organization *"
                            : "Institution *" }
                            <input className="edu-form-input"
                              placeholder={
                                eduFormType === "secondary" ? "e.g. Kelowna Secondary School"
                                : eduFormType === "extracurricular" ? "e.g. Debate Club, Student Union"
                                : eduFormType === "certifications" ? "e.g. AWS, Google, Microsoft, Coursera"
                                : "e.g. University of British Columbia"}
                              value={eduForm.institution} onChange={e => setEduForm(f => ({ ...f, institution: e.target.value }))} />
                          </label>

                          {/* Post Secondary */}
                          {eduFormType === "postsecondary" && (<>
                            <label className="edu-form-label">
                              Degree Type *
                              <input className="edu-form-input" placeholder="e.g. Bachelor of Science"
                                value={eduForm.degree_type} onChange={e => setEduForm(f => ({ ...f, degree_type: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              Field of Study *
                              <input className="edu-form-input" placeholder="e.g. Computer Science"
                                value={eduForm.topic} onChange={e => setEduForm(f => ({ ...f, topic: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              <span className="edu-date-field-head">
                                <span>Start Date *</span>
                              </span>
                              <MonthPicker value={eduForm.start_date} onChange={v => setEduForm(f => ({ ...f, start_date: v }))} />
                            </label>
                            <DateToggleField
                              label="End Date"
                              value={eduForm.end_date}
                              onChange={v => setEduForm(f => ({ ...f, end_date: v }))}
                              toggleLabel="Present"
                            />
                            <label className="edu-form-label">
                              Location
                              <input className="edu-form-input" placeholder="e.g. Vancouver, BC"
                                value={eduForm.location} onChange={e => setEduForm(f => ({ ...f, location: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              GPA
                              <input className="edu-form-input" placeholder="e.g. 3.8/4.0"
                                value={eduForm.gpa} onChange={e => setEduForm(f => ({ ...f, gpa: e.target.value }))} />
                            </label>
                            <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                              <span className="edu-label-inline">Awards &amp; Scholarships <span className="text-muted">(one per line)</span></span>
                              <textarea className="edu-form-input" rows={3}
                                placeholder={"Dean's List\nEntrance Scholarship\nPresidential Award"}
                                value={eduForm.awards} onChange={e => setEduForm(f => ({ ...f, awards: e.target.value }))} />
                            </label>
                          </>)}

                          {/* Secondary School */}
                          {eduFormType === "secondary" && (<>
                            <label className="edu-form-label">
                              Diploma / Certificate
                              <input className="edu-form-input" placeholder="e.g. IB Diploma (optional)"
                                value={eduForm.degree_type} onChange={e => setEduForm(f => ({ ...f, degree_type: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              Graduation Year *
                              <input className="edu-form-input" type="number" min="1950" max="2099" placeholder="e.g. 2020"
                                value={eduForm.end_date} onChange={e => setEduForm(f => ({ ...f, end_date: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              Location
                              <input className="edu-form-input" placeholder="e.g. Kelowna, BC"
                                value={eduForm.location} onChange={e => setEduForm(f => ({ ...f, location: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              Grade Average
                              <input className="edu-form-input" placeholder="e.g. 92%"
                                value={eduForm.gpa} onChange={e => setEduForm(f => ({ ...f, gpa: e.target.value }))} />
                            </label>
                            <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                              <span className="edu-label-inline">Awards &amp; Scholarships <span className="text-muted">(one per line)</span></span>
                              <textarea className="edu-form-input" rows={2}
                                placeholder={"Honour Roll\nPrincipal's Award"}
                                value={eduForm.awards} onChange={e => setEduForm(f => ({ ...f, awards: e.target.value }))} />
                            </label>
                          </>)}

                          {/* Certifications */}
                          {eduFormType === "certifications" && (<>
                            <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                              Certification Name *
                              <input className="edu-form-input" placeholder="e.g. AWS Solutions Architect, PMP, Google Analytics"
                                value={eduForm.topic} onChange={e => setEduForm(f => ({ ...f, topic: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              <span className="edu-date-field-head">
                                <span>Issue Date *</span>
                              </span>
                              <MonthPicker value={eduForm.start_date} onChange={v => setEduForm(f => ({ ...f, start_date: v }))} />
                            </label>
                            <DateToggleField
                              label="Expiry Date"
                              value={eduForm.end_date}
                              onChange={v => setEduForm(f => ({ ...f, end_date: v }))}
                              toggleLabel="No Expiry"
                            />
                            <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                              <span className="edu-label-inline">Credential ID <span className="text-muted">(optional)</span></span>
                              <input className="edu-form-input" placeholder="e.g. ABC-12345"
                                value={eduForm.gpa} onChange={e => setEduForm(f => ({ ...f, gpa: e.target.value }))} />
                            </label>
                          </>)}

                          {/* Extra Curricular */}
                          {eduFormType === "extracurricular" && (<>
                            <label className="edu-form-label">
                              Role / Title *
                              <input className="edu-form-input" placeholder="e.g. Student Body President, Team Captain"
                                value={eduForm.topic} onChange={e => setEduForm(f => ({ ...f, topic: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              Location
                              <input className="edu-form-input" placeholder="e.g. Vancouver, BC"
                                value={eduForm.location} onChange={e => setEduForm(f => ({ ...f, location: e.target.value }))} />
                            </label>
                            <label className="edu-form-label">
                              <span className="edu-date-field-head">
                                <span>Start Date *</span>
                              </span>
                              <MonthPicker value={eduForm.start_date} onChange={v => setEduForm(f => ({ ...f, start_date: v }))} />
                            </label>
                            <DateToggleField
                              label="End Date"
                              value={eduForm.end_date}
                              onChange={v => setEduForm(f => ({ ...f, end_date: v }))}
                              toggleLabel="Present"
                            />
                          </>)}
                        </div>

                        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                          <button className="btn-primary" onClick={addEducation}>Add Entry</button>
                          <button className="btn-secondary" onClick={() => { setShowEduForm(false); setEduError(null); }}>Cancel</button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Right: timeline */}
              <div className="edu-body-right">
                {educationEntries.length === 0 ? (
                  <div className="edu-empty-state">
                    <span className="edu-empty-icon">🎓</span>
                    <p className="edu-empty-title">No education yet</p>
                    <p className="edu-empty-sub">Add degrees, certifications, or extracurriculars to get started.</p>
                  </div>
                ) : (<>
                  <div className="edu-legend edu-legend-inline">
                    <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-degree" />Post Secondary</span>
                    <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-secondary" />Secondary</span>
                    <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-cert" />Certification</span>
                    <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-extra" />Extra Curricular</span>
                  </div>
                  <div className="edu-timeline-list">
                    <div className="edu-timeline-line" />
                    {educationEntries.map((entry, i) => {
                      const startDate = entry.start_date ? new Date(entry.start_date) : null;
                      const endDate = entry.end_date && entry.end_date !== "Present" ? new Date(entry.end_date) : null;
                      const isPresent = !entry.end_date || entry.end_date === "Present";
                      const start = startDate ? startDate.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "?";
                      const end = endDate ? endDate.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "Present";
                      const certHasExpiry = entry.degree_type === "Certification" && endDate;
                      const entryType = educationEntryTypeOf(entry);
                      const entryTypeClass = entryType === "certifications" ? "cert"
                        : entryType === "extracurricular" ? "extra"
                        : entryType === "secondary" ? "secondary"
                        : "degree";
                      return (
                        <div key={entry.id} className="edu-timeline-item">
                          <div className={`edu-timeline-dot ${i === 0 ? "first" : ""} edu-dot-${entryTypeClass}`} />
                          <div className={`edu-timeline-content card edu-card-wrap edu-card-${entryTypeClass}`}>
                            {!isPublic && editEduId !== entry.id && (
                              <div className="edu-card-actions">
                                <button className="edu-edit-btn" onClick={() => startEditEdu(entry)} title="Edit entry">✎</button>
                                <button className="edu-delete-btn" onClick={() => deleteEducation(entry.id)} title="Remove entry">✕</button>
                              </div>
                            )}
                            {editEduId === entry.id ? (
                              <div className="edu-inline-edit">
                                {(() => {
                                  const editType = editEduForm.entryType || "postsecondary";
                                  return (
                                    <div className="edu-inline-edit-grid">
                                      <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                        {editType === "secondary" ? "School Name *"
                                          : editType === "extracurricular" ? "Club / Team / Organization *"
                                          : editType === "certifications" ? "Issuing Organization *"
                                          : "Institution *"}
                                        <input
                                          className="edu-form-input"
                                          placeholder={
                                            editType === "secondary" ? "e.g. Kelowna Secondary School"
                                            : editType === "extracurricular" ? "e.g. Debate Club, Student Union"
                                            : editType === "certifications" ? "e.g. AWS, Google, Microsoft, Coursera"
                                            : "e.g. University of British Columbia"
                                          }
                                          value={editEduForm.institution}
                                          onChange={e => setEditEduForm(f => ({ ...f, institution: e.target.value }))}
                                        />
                                      </label>

                                      {editType === "postsecondary" && (
                                        <>
                                          <label className="edu-form-label">Degree Type *
                                            <input className="edu-form-input" placeholder="e.g. Bachelor of Science" value={editEduForm.degree_type} onChange={e => setEditEduForm(f => ({ ...f, degree_type: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            Field of Study *
                                            <input className="edu-form-input" placeholder="e.g. Computer Science" value={editEduForm.topic} onChange={e => setEditEduForm(f => ({ ...f, topic: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            <span className="edu-date-field-head">
                                              <span>Start Date *</span>
                                            </span>
                                            <MonthPicker value={editEduForm.start_date} onChange={v => setEditEduForm(f => ({ ...f, start_date: v }))} />
                                          </label>
                                          <DateToggleField
                                            label="End Date"
                                            value={editEduForm.end_date}
                                            onChange={v => setEditEduForm(f => ({ ...f, end_date: v }))}
                                            toggleLabel="Present"
                                          />
                                          <label className="edu-form-label">
                                            Location
                                            <input className="edu-form-input" placeholder="e.g. Vancouver, BC" value={editEduForm.location} onChange={e => setEditEduForm(f => ({ ...f, location: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            GPA
                                            <input className="edu-form-input" placeholder="e.g. 3.8/4.0" value={editEduForm.gpa} onChange={e => setEditEduForm(f => ({ ...f, gpa: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                            <span className="edu-label-inline">Awards &amp; Scholarships <span className="text-muted">(one per line)</span></span>
                                            <textarea className="edu-form-input" rows={3} placeholder={"Dean's List\nEntrance Scholarship\nPresidential Award"} value={editEduForm.awards} onChange={e => setEditEduForm(f => ({ ...f, awards: e.target.value }))} />
                                          </label>
                                        </>
                                      )}

                                      {editType === "secondary" && (
                                        <>
                                          <label className="edu-form-label">
                                            Diploma / Certificate
                                            <input className="edu-form-input" placeholder="e.g. IB Diploma (optional)" value={editEduForm.degree_type} onChange={e => setEditEduForm(f => ({ ...f, degree_type: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">Graduation Year *
                                            <input className="edu-form-input" type="number" placeholder="e.g. 2022" value={editEduForm.end_date ? editEduForm.end_date.substring(0, 4) : ""} onChange={e => setEditEduForm(f => ({ ...f, end_date: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            Location
                                            <input className="edu-form-input" placeholder="e.g. Kelowna, BC" value={editEduForm.location} onChange={e => setEditEduForm(f => ({ ...f, location: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            Grade Average
                                            <input className="edu-form-input" placeholder="e.g. 92%" value={editEduForm.gpa} onChange={e => setEditEduForm(f => ({ ...f, gpa: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                            <span className="edu-label-inline">Awards &amp; Scholarships <span className="text-muted">(one per line)</span></span>
                                            <textarea className="edu-form-input" rows={2} placeholder={"Honour Roll\nPrincipal's Award"} value={editEduForm.awards} onChange={e => setEditEduForm(f => ({ ...f, awards: e.target.value }))} />
                                          </label>
                                        </>
                                      )}

                                      {editType === "certifications" && (
                                        <>
                                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                            Certification Name *
                                            <input className="edu-form-input" placeholder="e.g. AWS Solutions Architect, PMP, Google Analytics" value={editEduForm.topic} onChange={e => setEditEduForm(f => ({ ...f, topic: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            <span className="edu-date-field-head">
                                              <span>Issue Date *</span>
                                            </span>
                                            <MonthPicker value={editEduForm.start_date} onChange={v => setEditEduForm(f => ({ ...f, start_date: v }))} />
                                          </label>
                                          <DateToggleField
                                            label="Expiry Date"
                                            value={editEduForm.end_date}
                                            onChange={v => setEditEduForm(f => ({ ...f, end_date: v }))}
                                            toggleLabel="No Expiry"
                                          />
                                          <label className="edu-form-label" style={{ gridColumn: "1 / -1" }}>
                                            <span className="edu-label-inline">Credential ID <span className="text-muted">(optional)</span></span>
                                            <input className="edu-form-input" placeholder="e.g. ABC-12345" value={editEduForm.gpa} onChange={e => setEditEduForm(f => ({ ...f, gpa: e.target.value }))} />
                                          </label>
                                        </>
                                      )}

                                      {editType === "extracurricular" && (
                                        <>
                                          <label className="edu-form-label">
                                            Role / Title *
                                            <input className="edu-form-input" placeholder="e.g. Student Body President, Team Captain" value={editEduForm.topic} onChange={e => setEditEduForm(f => ({ ...f, topic: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            Location
                                            <input className="edu-form-input" placeholder="e.g. Vancouver, BC" value={editEduForm.location} onChange={e => setEditEduForm(f => ({ ...f, location: e.target.value }))} />
                                          </label>
                                          <label className="edu-form-label">
                                            <span className="edu-date-field-head">
                                              <span>Start Date *</span>
                                            </span>
                                            <MonthPicker value={editEduForm.start_date} onChange={v => setEditEduForm(f => ({ ...f, start_date: v }))} />
                                          </label>
                                          <DateToggleField
                                            label="End Date"
                                            value={editEduForm.end_date}
                                            onChange={v => setEditEduForm(f => ({ ...f, end_date: v }))}
                                            toggleLabel="Present"
                                          />
                                        </>
                                      )}
                                    </div>
                                  );
                                })()}
                                {editEduError && <p style={{ color: "#f87171", fontSize: "0.8rem", marginTop: 8 }}>{editEduError}</p>}
                                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                                  <button className="btn-primary" style={{ fontSize: "0.8rem", padding: "6px 16px" }} onClick={() => saveEditEdu(entry.id)}>Save</button>
                                  <button className="btn-secondary" style={{ fontSize: "0.8rem", padding: "6px 16px" }} onClick={() => { setEditEduId(null); setEditEduError(null); }}>Cancel</button>
                                </div>
                              </div>
                            ) : (<>
                              <div className="edu-timeline-top">
                                <div>
                                  <p className="edu-institution">{entry.institution}</p>
                                  <p className="edu-degree">
                                    {entry.degree_type === "Certification" ? entry.topic : `${entry.degree_type} · ${entry.topic}`}
                                  </p>
                                </div>
                                <div style={{ textAlign: "right", flexShrink: 0 }}>
                                  <p className="edu-dates">
                                    {entry.degree_type === "Certification"
                                      ? `Issued ${start}${certHasExpiry ? ` · Expires ${end}` : ""}`
                                      : <>{start} — {isPresent ? <span className="edu-present-pill"><span className="edu-present-dot" />Present</span> : end}</>}
                                  </p>
                                  {entry.location && <p className="text-muted" style={{ fontSize: "0.78rem" }}>{entry.location}</p>}
                                  {entry.gpa && (
                                    <p className="edu-gpa">
                                      {entry.degree_type === "Certification" ? `ID: ${entry.gpa}` : `GPA: ${entry.gpa}`}
                                    </p>
                                  )}
                                </div>
                              </div>
                              {entry.details && entry.details.length > 0 && (
                                <div className="edu-awards-list">
                                  {entry.details.map((award, idx) => (
                                    <div key={idx} className={`edu-award-card edu-award-${entryTypeClass}`}>{award}</div>
                                  ))}
                                </div>
                              )}
                            </>)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>)}
              </div>
            </div>
          </div>
        )}

        {/* Contact */}
        {activeSection === "contact" && (
          <div className="port-section-page">
            <div className="port-contact-shell">
              <div className="port-contact-hero card">
                <div className="port-contact-copy">
                  <span className="port-contact-kicker">Contact</span>
                  <h2 className="port-contact-title">Contact Information</h2>
                  {!isPublic && (
                    <p className="port-contact-subtitle">
                      Display your contact details and online profiles in one place.
                    </p>
                  )}
                  {isPublic ? (
                    contactInfo.intro ? (
                      <p className="port-contact-intro">{contactInfo.intro}</p>
                    ) : (
                      <p className="port-contact-empty">No contact summary has been added yet.</p>
                    )
                  ) : (
                    <textarea
                      className="port-contact-intro-input"
                      placeholder="Add a short summary about who you are, what you do, and what these contact details are for..."
                      value={contactInfo.intro}
                      onChange={e => setContactInfoAndSave(info => ({ ...info, intro: e.target.value }))}
                      rows={4}
                      maxLength={320}
                    />
                  )}
                </div>
                <div className="port-contact-status">
                  <span className="port-contact-status-label">Job Search Status</span>
                  {isPublic ? (
                    <p className="port-contact-status-text">
                      {contactInfo.availability || "No job search status added"}
                    </p>
                  ) : (
                    <input
                      className="port-contact-input"
                      type="text"
                      placeholder="e.g. Open to Work"
                      value={contactInfo.availability}
                      onChange={e => setContactInfoAndSave(info => ({ ...info, availability: e.target.value }))}
                      maxLength={120}
                    />
                  )}
                </div>
              </div>

              <div className="port-contact-grid">
                <div className="port-contact-card card">
                  <div className="port-section-header">
                    <span>Personal Details</span>
                  </div>
                  <div className="port-contact-fields">
                    <ContactField
                      label="Email"
                      value={contactInfo.email}
                      isPublic={isPublic}
                      type="email"
                      placeholder="name@example.com"
                      href={contactInfo.email ? `mailto:${contactInfo.email}` : ""}
                      onChange={value => setContactInfoAndSave(info => ({ ...info, email: value }))}
                    />
                    <ContactField
                      label="Phone"
                      value={contactInfo.phone}
                      isPublic={isPublic}
                      type="text"
                      placeholder="(555) 123-4567"
                      href={contactInfo.phone ? `tel:${contactInfo.phone.replace(/\s+/g, "")}` : ""}
                      onChange={value => setContactInfoAndSave(info => ({ ...info, phone: value }))}
                    />
                    <ContactField
                      label="Location"
                      value={contactInfo.location}
                      isPublic={isPublic}
                      type="text"
                      placeholder="Vancouver, BC"
                      onChange={value => setContactInfoAndSave(info => ({ ...info, location: value }))}
                    />
                  </div>
                </div>

                <div className="port-contact-card card">
                  <div className="port-section-header port-contact-card-header">
                    <span>Online Presence</span>
                    {!isPublic && (
                      <button className="port-contact-add-btn" type="button" onClick={addCustomPresence} title="Add another online presence">
                        +
                      </button>
                    )}
                  </div>
                  <div className="port-contact-fields">
                    <ContactField
                      label="Website"
                      value={contactInfo.website}
                      isPublic={isPublic}
                      type="url"
                      placeholder="https://your-site.com"
                      href={contactInfo.website}
                      onChange={value => setContactInfoAndSave(info => ({ ...info, website: value }))}
                    />
                    <ContactField
                      label="LinkedIn"
                      value={contactInfo.linkedin}
                      isPublic={isPublic}
                      type="url"
                      placeholder="https://linkedin.com/in/username"
                      href={contactInfo.linkedin}
                      onChange={value => setContactInfoAndSave(info => ({ ...info, linkedin: value }))}
                    />
                    <ContactField
                      label="GitHub"
                      value={contactInfo.github}
                      isPublic={isPublic}
                      type="url"
                      placeholder="https://github.com/username"
                      href={contactInfo.github}
                      onChange={value => setContactInfoAndSave(info => ({ ...info, github: value }))}
                    />
                    {(contactInfo.customPresences || []).map(item => (
                      <CustomPresenceField
                        key={item.id}
                        item={item}
                        isPublic={isPublic}
                        onChange={(field, value) => updateCustomPresence(item.id, field, value)}
                        onRemove={() => removeCustomPresence(item.id)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

const _MP_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function MonthPicker({ value, onChange, placeholder = "Select date" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 60 }, (_, i) => currentYear - i);
  const parsed = value ? value.slice(0, 7).split("-") : [];
  const selYear  = parsed[0] ? parseInt(parsed[0]) : null;
  const selMonth = parsed[1] ? parseInt(parsed[1]) : null;
  const [viewYear, setViewYear] = useState(selYear || currentYear);

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
    ? (() => { const [y, m] = value.slice(0,7).split("-").map(Number); return `${_MP_MONTHS[m-1] || ""} ${y}`; })()
    : placeholder;

  return (
    <span className="port-mp-wrap" ref={ref}>
      <button type="button" className="edu-form-input port-mp-trigger"
        onClick={() => { setViewYear(selYear || currentYear); setOpen(o => !o); }}>
        {displayVal}
        <span className="port-mp-caret">▾</span>
      </button>
      {open && (
        <div className="port-mp-popup">
          <div className="port-mp-year-row">
            <button type="button" className="port-mp-nav" onClick={() => setViewYear(y => y - 1)}>‹</button>
            <select className="port-mp-year-sel" value={viewYear} onChange={e => setViewYear(parseInt(e.target.value))}>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
            <button type="button" className="port-mp-nav" onClick={() => setViewYear(y => y + 1)}>›</button>
          </div>
          <div className="port-mp-grid">
            {_MP_MONTHS.map((m, i) => (
              <button key={m} type="button"
                className={`port-mp-month${selYear === viewYear && selMonth === i + 1 ? " selected" : ""}`}
                onClick={() => selectMonth(i + 1)}>
                {m}
              </button>
            ))}
          </div>
        </div>
      )}
    </span>
  );
}

function currentMonthValue() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function DateToggleField({ label, value, onChange, toggleLabel }) {
  const toggledOn = !value;

  return (
    <div className="edu-form-label">
      <div className="edu-date-field-head">
        <span>{label}</span>
        <label className="edu-date-checkbox">
          <input
            type="checkbox"
            checked={toggledOn}
            onChange={e => onChange(e.target.checked ? "" : currentMonthValue())}
          />
          <span>{toggleLabel}</span>
        </label>
      </div>
      {toggledOn ? (
        <div className="edu-date-toggle-empty text-muted">{toggleLabel} selected</div>
      ) : (
        <MonthPicker value={value} onChange={onChange} />
      )}
    </div>
  );
}

function EvidenceSection({ p }) {
  const ev = p.success_evidence;
  if (!ev) return null;

  let data = null;
  try { data = JSON.parse(ev); } catch (_) {}

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return <p className="port-evidence">{ev}</p>;
  }

  const chips = [];
  if (data.manual_metrics && typeof data.manual_metrics === "object") {
    Object.entries(data.manual_metrics).forEach(([k, v]) =>
      chips.push({ label: k.replace(/_/g, " "), value: v.value ?? v })
    );
  }
  if (data.test_coverage != null) chips.push({ label: "coverage", value: `${data.test_coverage}%` });
  if (Array.isArray(data.achievements) && data.achievements.length > 0)
    chips.push({ label: "achievements", value: data.achievements.length });
  if (Array.isArray(data.feedback) && data.feedback.length > 0)
    chips.push({ label: "feedback", value: data.feedback.length });
  if (Array.isArray(data.readme_badges) && data.readme_badges.length > 0)
    chips.push({ label: "badges", value: data.readme_badges.length });

  const skip = new Set(["manual_metrics", "test_coverage", "achievements", "feedback", "readme_badges"]);
  Object.entries(data).forEach(([k, v]) => {
    if (skip.has(k) || typeof v === "object") return;
    chips.push({ label: k.replace(/_/g, " "), value: v });
  });

  if (chips.length === 0) return null;

  return (
    <div className="port-evidence-chips">
      {chips.map((c, i) => (
        <span key={i} className="port-evidence-chip">
          <span className="port-evidence-chip-label">{c.label}</span>
          <span className="port-evidence-chip-val">{c.value}</span>
        </span>
      ))}
    </div>
  );
}

function ContactField({ label, value, isPublic, type = "text", placeholder, href, onChange }) {
  if (isPublic) {
    if (!value) return null;
    return (
      <div className="port-contact-field">
        <span className="port-contact-field-label">{label}</span>
        {href ? (
          <a
            className="port-contact-link"
            href={href}
            target={href.startsWith("mailto:") || href.startsWith("tel:") ? undefined : "_blank"}
            rel={href.startsWith("mailto:") || href.startsWith("tel:") ? undefined : "noreferrer"}
          >
            {value}
          </a>
        ) : (
          <p className="port-contact-value">{value}</p>
        )}
      </div>
    );
  }

  return (
    <label className="port-contact-field">
      <span className="port-contact-field-label">{label}</span>
      <input
        className="port-contact-input"
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
    </label>
  );
}

function CustomPresenceField({ item, isPublic, onChange, onRemove }) {
  if (isPublic) {
    if (!item.url) return null;
    return (
      <div className="port-contact-field">
        <span className="port-contact-field-label">{item.label || "Online Presence"}</span>
        <a className="port-contact-link" href={item.url} target="_blank" rel="noreferrer">
          {item.url}
        </a>
      </div>
    );
  }

  return (
    <div className="port-contact-custom-row">
      <div className="port-contact-custom-inputs">
        <label className="port-contact-field">
          <span className="port-contact-field-label">Title</span>
          <input
            className="port-contact-input"
            type="text"
            placeholder="e.g. Behance"
            value={item.label}
            onChange={e => onChange("label", e.target.value)}
          />
        </label>
        <label className="port-contact-field">
          <span className="port-contact-field-label">Link</span>
          <input
            className="port-contact-input"
            type="url"
            placeholder="https://example.com/profile"
            value={item.url}
            onChange={e => onChange("url", e.target.value)}
          />
        </label>
      </div>
      <button className="port-contact-remove-btn" type="button" onClick={onRemove} title="Remove online presence">
        Remove
      </button>
    </div>
  );
}

function EditForm({ p, editForm, setEditForm, saveEdit, setEditId }) {
  return (
    <div className="port-inline-edit">
      <div className="port-edit-grid">
        <label>Description<textarea rows={3} value={editForm.custom_description} onChange={e => setEditForm({ ...editForm, custom_description: e.target.value })} /></label>
        <label>Your Role<input value={editForm.user_role} onChange={e => setEditForm({ ...editForm, user_role: e.target.value })} placeholder="Lead Developer, Designer…" /></label>
        <label>Success Evidence<textarea rows={2} value={editForm.success_evidence} onChange={e => setEditForm({ ...editForm, success_evidence: e.target.value })} placeholder="Metrics, feedback, grades…" /></label>
        <label>Importance Score (0–1)<input type="number" min="0" max="1" step="0.01" value={editForm.importance_score} onChange={e => setEditForm({ ...editForm, importance_score: e.target.value })} /></label>
        <label>Languages (comma-sep)<input value={editForm.languages} onChange={e => setEditForm({ ...editForm, languages: e.target.value })} /></label>
        <label>Frameworks (comma-sep)<input value={editForm.frameworks} onChange={e => setEditForm({ ...editForm, frameworks: e.target.value })} /></label>
        <label>Skills (comma-sep)<input value={editForm.skills} onChange={e => setEditForm({ ...editForm, skills: e.target.value })} /></label>
        <label>Tags (comma-sep)<input value={editForm.tags} onChange={e => setEditForm({ ...editForm, tags: e.target.value })} /></label>
      </div>
      <div className="port-edit-checks">
        <label><input type="checkbox" checked={editForm.is_featured} onChange={e => setEditForm({ ...editForm, is_featured: e.target.checked })} /> Featured</label>
        <label><input type="checkbox" checked={editForm.is_hidden} onChange={e => setEditForm({ ...editForm, is_hidden: e.target.checked })} /> Hidden</label>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button className="btn-primary" onClick={() => saveEdit(p.id)}>Save</button>
        <button className="btn-secondary" onClick={() => setEditId(null)}>Cancel</button>
      </div>
    </div>
  );
}

function ProjectCard({ p, rank, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav, isPublic, toggleHidden }) {
  const accent = typeColor(p.type || p.project_type);
  const thumb = thumbUrl(p.thumbnail_path);
  return (
    <div className={`port-top-card card${p.is_featured ? " port-featured-card" : ""}`} style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="port-rank">#{rank}</div>
      <div className="port-card-tags">
        <span className="tag">{p.type || p.project_type}</span>
        {p.is_featured && <span className="port-featured-badge">★ Featured</span>}
        {p.is_hidden && !isPublic && <span className="tag warning">hidden</span>}
      </div>
      <div className="port-card-thumb-wrapper">
        <img
          src={thumb}
          alt="thumbnail"
          className="port-card-thumb"
          style={{ display: thumb ? "block" : "none" }}
          onError={e => { e.target.style.display = "none"; e.target.parentNode.querySelector(".port-card-thumb-placeholder").style.display = "flex"; }}
        />
        <div className="port-card-thumb-placeholder" style={{ display: thumb ? "none" : "flex", background: `linear-gradient(135deg, ${accent}22 0%, ${accent}44 100%)`, borderColor: `${accent}44` }}>
          {(projectName(p) || "?")[0].toUpperCase()}
        </div>
        {thumb && <div className="port-card-thumb-overlay" />}
      </div>
      <h3 className="port-proj-name">{projectName(p)}</h3>
      <p className="port-proj-desc text-muted">{p.description || "No description"}</p>
      {p.user_role && <p className="port-role-badge" style={{ fontSize: "0.8rem", marginTop: 4 }}>Role: {p.user_role}</p>}
      <EvidenceSection p={p} />
      <div className="chip-group" style={{ marginTop: 8 }}>
        {[...new Set([...(p.skills || []), ...(p.tech_stack || p.languages || [])])].slice(0, 6).map((t, i) => {
          const tc = typeColor(t);
          return <span key={i} className="tag accent" style={{ color: tc, borderColor: `${tc}55`, background: `${tc}18` }}>{t}</span>;
        })}
      </div>
      {p.importance_score != null && (
        <div className="port-score-track">
          <div className="port-score-track-inner">
            <div className="port-score-fill" style={{ width: `${Math.round((p.importance_score || 0) * 100)}%`, background: accent }} />
          </div>
          <span className="port-score-label">{Number(p.importance_score).toFixed(2)}</span>
        </div>
      )}
      {p.metrics && (
        <div className="port-metrics">
          {p.metrics.lines_of_code > 0 && <span>{p.metrics.lines_of_code?.toLocaleString()} lines</span>}
          {p.metrics.file_count > 0 && <span>{p.metrics.file_count} files</span>}
        </div>
      )}
      {!isPublic && (
        <div className="port-rank-row">
          <input type="number" min="0" max="1" step="0.01" placeholder="Score 0–1"
            value={rankInput[p.id] ?? p.importance_score ?? ""}
            onChange={e => setRankInput({ ...rankInput, [p.id]: e.target.value })}
            style={{ width: 100, padding: "5px 8px" }} />
          <button className="btn-secondary" style={{ padding: "5px 10px", fontSize: "0.8rem" }} onClick={() => saveRank(p.id)}>Set</button>
        </div>
      )}
      <div className="port-card-actions">
        <button className="btn-secondary" onClick={() => nav(`/projects/${p.id}`)}>View</button>
        {!isPublic && (
          <button className="btn-secondary" onClick={() => editId === p.id ? setEditId(null) : startEdit(p)}>{editId === p.id ? "Cancel" : "Edit"}</button>
        )}
        {!isPublic && (
          <button className={`btn-secondary port-hide-btn${p.is_hidden ? " hidden-active" : ""}`} onClick={() => toggleHidden(p)} title={p.is_hidden ? "Show in portfolio" : "Hide from portfolio"}>
            {p.is_hidden ? "Unhide" : "Hide"}
          </button>
        )}
      </div>
      {!isPublic && editId === p.id && <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />}
    </div>
  );
}

function ProjectRow({ p, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav, isPublic, toggleHidden }) {
  const accent = typeColor(p.type || p.project_type);
  const score = p.importance_score ?? 0;
  const thumb = thumbUrl(p.thumbnail_path);
  return (
    <div className="port-list-row card" style={{ borderLeft: `3px solid ${accent}` }}>
      {/* Importance bar on left */}
      <div className="port-score-bar" style={{ background: accent, height: `${Math.round(score * 100)}%` }} />
      {thumb ? (
        <img src={thumb} alt="thumbnail" className="port-row-thumb" onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }} />
      ) : null}
      <div className="port-row-thumb-placeholder" style={{ display: thumb ? "none" : "flex" }}>
        {(projectName(p) || "?")[0].toUpperCase()}
      </div>
      <div className="port-list-main">
        <div className="port-list-top">
          <strong className="port-list-name">{projectName(p)}</strong>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            <span className="tag">{p.type || p.project_type}</span>
            {p.is_hidden && !isPublic && <span className="tag warning">hidden</span>}
            {p.importance_score != null && (
              <div className="port-row-score-wrap" title={`Score: ${Number(p.importance_score).toFixed(2)}`}>
                <div className="port-row-score-bar" style={{ width: `${Math.round((p.importance_score || 0) * 100)}%`, background: accent }} />
              </div>
            )}
          </div>
        </div>
        <div className="port-list-desc-fade">
          <p className="port-list-desc text-muted">{p.description || "No description"}</p>
        </div>
        {p.user_role && <p className="port-role-badge" style={{ fontSize: "0.78rem", marginTop: 2 }}>Role: {p.user_role}</p>}
        <EvidenceSection p={p} />
        <div className="chip-group" style={{ marginTop: 6 }}>
          {[...new Set([...(p.skills || []), ...(p.languages || p.tech_stack || [])])].slice(0, 8).map((t, i) => {
            const tc = typeColor(t);
            return <span key={i} className="tag accent" style={{ color: tc, borderColor: `${tc}55`, background: `${tc}18` }}>{t}</span>;
          })}
        </div>
      </div>
      <div className="port-list-actions">
        {!isPublic && (
          <div className="port-rank-row">
            <input type="number" min="0" max="1" step="0.01" placeholder="0–1"
              value={rankInput[p.id] ?? p.importance_score ?? ""}
              onChange={e => setRankInput({ ...rankInput, [p.id]: e.target.value })}
              style={{ width: 70, padding: "5px 6px", fontSize: "0.8rem" }} />
            <button className="btn-secondary" style={{ padding: "5px 8px", fontSize: "0.75rem" }} onClick={() => saveRank(p.id)}>Set</button>
          </div>
        )}
        <button className="btn-secondary" style={{ padding: "6px 12px" }} onClick={() => nav(`/projects/${p.id}`)}>View</button>
        {!isPublic && (
          <button className="btn-secondary" style={{ padding: "6px 12px" }} onClick={() => editId === p.id ? setEditId(null) : startEdit(p)}>{editId === p.id ? "Cancel" : "Edit"}</button>
        )}
        {!isPublic && (
          <button className={`btn-secondary port-hide-btn${p.is_hidden ? " hidden-active" : ""}`} style={{ padding: "6px 12px" }} onClick={() => toggleHidden(p)} title={p.is_hidden ? "Show in portfolio" : "Hide from portfolio"}>
            {p.is_hidden ? "Unhide" : "Hide"}
          </button>
        )}
      </div>
      {!isPublic && editId === p.id && (
        <div style={{ width: "100%", marginTop: 12 }}>
          <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />
        </div>
      )}
    </div>
  );
}
