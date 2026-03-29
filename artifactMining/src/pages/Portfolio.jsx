import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import SkillsTimeline from "./SkillsTimeline";
import ActivityHeatmap from "./ActivityHeatmap";
import "./Portfolio.css";

const API_BASE = "http://127.0.0.1:8000";

const STAT_ICONS = { Projects: "📁", "Lines of Code": "💻", Files: "🗂️", "Word Count": "📝", Skills: "⚡" };

const TYPE_COLORS = {
  python:     "#3b82f6", javascript: "#f59e0b", typescript: "#6366f1",
  java:       "#ef4444", web:        "#10b981", mobile:     "#8b5cf6",
  ml:         "#ec4899", data:       "#14b8a6", default:    "#6366f1",
};
function typeColor(type) {
  const t = (type || "").toLowerCase();
  for (const [key, col] of Object.entries(TYPE_COLORS)) if (t.includes(key)) return col;
  return TYPE_COLORS.default;
}

function thumbUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  const filename = path.split(/[/\\]/).pop();
  return `${API_BASE}/uploads/${filename}`;
}

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
  const [visibilityLoading, setVisibilityLoading] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    const sync = () => setShowEmojis(localStorage.getItem("dash_show_emojis") !== "false");
    window.addEventListener("dash-emojis-updated", sync);
    return () => window.removeEventListener("dash-emojis-updated", sync);
  }, []);

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

  if (authed === null) return <div className="page-wrap" style={{ paddingTop: 80, textAlign: "center", color: "#818cf8" }}>Checking authentication...</div>;

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
    try {
      await apiFetch(`/portfolio/${id}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
      setMsg({ type: "success", text: "Saved!" });
      setEditId(null);
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
    setEditForm({
      custom_description: p.description || "",
      is_featured: p.is_featured || false,
      is_hidden: p.is_hidden || false,
      importance_score: p.importance_score ?? "",
      user_role: p.user_role || "",
      success_evidence: p.success_evidence || "",
      languages: (p.languages || []).join(", "),
      frameworks: (p.frameworks || []).join(", "),
      skills: (p.skills || []).join(", "),
      tags: (p.tags || []).join(", "),
    });
  }

  const isPublic = viewMode === "public";
  const projects = portfolio?.projects || [];

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
              <label className="toggle-label">
                <input type="checkbox" checked={includeHidden} onChange={e => setIncludeHidden(e.target.checked)} />
                Show hidden
              </label>
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
            {/* Banner — contains identity */}
            <div className="port-about-banner">
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
                    placeholder="Title or role — e.g. Full-Stack Developer · UBC"
                    value={heroSub}
                    onChange={ev => { setHeroSub(ev.target.value); localStorage.setItem("portfolio_hero_sub", ev.target.value); saveAbout("about_subtitle", ev.target.value); }}
                    maxLength={80}
                  />
                )}
              </div>
            </div>

            <div className="port-about-divider" />

            {/* Bio — hidden in public mode if empty */}
            {(!isPublic || aboutBio) && (
              <div className="port-about-bio-section">
                <span className="port-about-bio-label">About Me</span>
                {isPublic ? (
                  <p className="port-about-bio-text">{aboutBio}</p>
                ) : (
                  <div className="port-about-bio-wrap">
                    <textarea
                      className="port-about-bio-input"
                      placeholder="Write a short bio — your background, what you're building, and what drives you…"
                      value={aboutBio}
                      onChange={ev => { setAboutBio(ev.target.value); saveAbout("about_bio", ev.target.value); }}
                      rows={6}
                      maxLength={800}
                    />
                    <span className="port-about-char-count">{aboutBio.length} / 800</span>
                  </div>
                )}
                <span className="port-about-saved" style={{ opacity: saveStatus === "saved" ? undefined : 0, animation: saveStatus === "saved" ? undefined : "none" }}>Saved ✓</span>
              </div>
            )}

            <div className="port-about-bottom-row">
              <Link to="/showcase" className="btn-primary port-about-showcase-btn" style={{ textDecoration: "none", color: "#fff" }}>
                Web Showcase
              </Link>
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
                  <select className="port-type-select" value={typeFilter} onChange={ev => setTypeFilter(ev.target.value)}>
                    {projectTypes.map(t => (
                      <option key={t} value={t}>{t === "all" ? "All Types" : t}</option>
                    ))}
                  </select>
                  {(search || typeFilter !== "all") && (
                    <span className="port-result-count">{sorted.length} result{sorted.length !== 1 ? "s" : ""}</span>
                  )}
                </div>
              )}

              {projects.length > 0 && (
                <div className="port-sort-row">
                  <span className="port-sort-label">Sort by</span>
                  {SORT_OPTIONS.map(o => (
                    <button key={o.value}
                      className={`port-sort-pill ${sortBy === o.value ? "active" : ""}`}
                      onClick={() => setSortBy(o.value)}>
                      {o.label}
                    </button>
                  ))}
                  <div className="port-layout-toggle">
                    <button className={`port-layout-btn ${layout === "list" ? "active" : ""}`} onClick={() => setLayoutPersist("list")} title="List view">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                    </button>
                    <button className={`port-layout-btn ${layout === "grid" ? "active" : ""}`} onClick={() => setLayoutPersist("grid")} title="Grid view">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                    </button>
                  </div>
                </div>
              )}

              {projects.length === 0 ? (
                <div className="empty-state">
                  <p>No portfolio data yet.</p>
                  <p style={{ marginTop: 8, fontSize: "0.9rem" }}>Click <strong>Regenerate</strong> to build from your projects.</p>
                </div>
              ) : sorted.length === 0 && isPublic ? (
                <div className="port-no-results">
                  <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: "#6b7a99", marginBottom: 12 }}>
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <p>No projects match <strong style={{ color: "#a5b4fc" }}>{search || typeFilter}</strong></p>
                  <button className="btn-secondary" style={{ marginTop: 12, fontSize: "0.82rem" }} onClick={() => { setSearch(""); setTypeFilter("all"); }}>Clear filters</button>
                </div>
              ) : (
                <>
                  {featured.length > 0 && (
                    <div className="port-section">
                      <div className="port-section-header">
                        <span>{e("⭐ ")}Featured Projects</span>
                      </div>
                      <div className="port-top-grid">
                        {featured.map((p, i) => <ProjectCard key={p.id} p={p} rank={i + 1} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} isPublic={isPublic} />)}
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
                        {rest.map((p, i) => <ProjectCard key={p.id} p={p} rank={featured.length + i + 1} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} isPublic={isPublic} />)}
                      </div>
                    ) : (
                      <div className="port-all-list">
                        {rest.map(p => <ProjectRow key={p.id} p={p} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} isPublic={isPublic} />)}
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
          <div className="port-section-page">
            <div className="port-placeholder">
              <h2>Experience</h2>
              <p className="text-muted">Coming soon — add your work experience here.</p>
            </div>
          </div>
        )}

        {/* Education */}
        {activeSection === "education" && (
          <div className="port-section-page">
            <div className="port-placeholder">
              <h2>Education</h2>
              <p className="text-muted">Coming soon — add your education history here.</p>
            </div>
          </div>
        )}

        {/* Contact */}
        {activeSection === "contact" && (
          <div className="port-section-page">
            <div className="port-placeholder">
              <h2>Contact</h2>
              <p className="text-muted">Coming soon — add your contact details here.</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function EvidenceSection({ p }) {
  const ev = p.success_evidence;
  if (!ev) return null;
  return (
    <div className="port-evidence">
      <span className="port-evidence-label">Evidence:</span>
      <span>{ev}</span>
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

function ProjectCard({ p, rank, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav, isPublic }) {
  const accent = typeColor(p.type || p.project_type);
  const thumb = thumbUrl(p.thumbnail_path);
  return (
    <div className="port-top-card card" style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="port-rank">#{rank}</div>
      <div className="port-card-tags">
        <span className="tag">{p.type || p.project_type}</span>
        {p.is_hidden && !isPublic && <span className="tag warning">hidden</span>}
      </div>
      {thumb ? (
        <img src={thumb} alt="thumbnail" className="port-card-thumb" onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }} />
      ) : null}
      <div className="port-card-thumb-placeholder" style={{ display: thumb ? "none" : "flex" }}>
        {(projectName(p) || "?")[0].toUpperCase()}
      </div>
      <h3 className="port-proj-name">{projectName(p)}</h3>
      <p className="port-proj-desc text-muted">{p.description || "No description"}</p>
      {p.user_role && <p style={{ fontSize: "0.8rem", color: "#a5b4fc", marginTop: 4 }}>Role: {p.user_role}</p>}
      <EvidenceSection p={p} />
      <div className="chip-group" style={{ marginTop: 8 }}>
        {[...(p.tech_stack || p.languages || []), ...(p.skills || [])].slice(0, 6).map((t, i) => <span key={i} className="tag accent">{t}</span>)}
      </div>
      {p.metrics && (
        <div className="port-metrics">
          {p.metrics.lines_of_code > 0 && <span>{p.metrics.lines_of_code?.toLocaleString()} lines</span>}
          {p.metrics.file_count > 0 && <span>{p.metrics.file_count} files</span>}
          {p.importance_score != null && <span>Score: {Number(p.importance_score).toFixed(2)}</span>}
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
      </div>
      {!isPublic && editId === p.id && <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />}
    </div>
  );
}

function ProjectRow({ p, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav, isPublic }) {
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
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <span className="tag">{p.type || p.project_type}</span>
            {p.is_hidden && !isPublic && <span className="tag warning">hidden</span>}
            {p.importance_score != null && <span className="tag accent">{Number(p.importance_score).toFixed(2)}</span>}
          </div>
        </div>
        <p className="port-list-desc text-muted">{p.description?.slice(0, 120) || "No description"}</p>
        {p.user_role && <p style={{ fontSize: "0.78rem", color: "#a5b4fc", marginTop: 2 }}>Role: {p.user_role}</p>}
        <EvidenceSection p={p} />
        <div className="chip-group" style={{ marginTop: 6 }}>
          {(p.languages || p.tech_stack || []).slice(0, 5).map((t, i) => <span key={i} className="tag accent">{t}</span>)}
          {(p.skills || []).slice(0, 3).map((s, i) => <span key={i} className="tag">{s}</span>)}
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
      </div>
      {!isPublic && editId === p.id && (
        <div style={{ width: "100%", marginTop: 12 }}>
          <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />
        </div>
      )}
    </div>
  );
}
