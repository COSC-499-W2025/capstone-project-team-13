import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  typeColor, educationEntryTypeOf, experienceTypeOf,
  ContactField, CustomPresenceField,
  ProjectCard, ProjectRow,
} from "./PortfolioShared";
import "./Portfolio.css";
import "./PublicPortfolios.css";

const API_BASE = "http://127.0.0.1:8000";

const STAT_ICONS = { Projects: "📁", "Lines of Code": "💻", Files: "🗂️", "Word Count": "📝", Skills: "⚡" };

const NAV_ITEMS = [
  { id: "about",      label: "About Me" },
  { id: "projects",   label: "Projects" },
  { id: "skills",     label: "Skills & Stats" },
  { id: "experience", label: "Experience" },
  { id: "education",  label: "Education" },
  { id: "contact",    label: "Contact" },
];

const SORT_OPTIONS = [
  { value: "importance", label: "Importance" },
  { value: "date",       label: "Date" },
  { value: "name",       label: "Name" },
];

const EXP_LEGEND = [
  ["work", "Work"],
  ["internship", "Internship"],
  ["volunteering", "Volunteering"],
  ["freelance", "Freelance / Contract"],
];

// ── List of all public portfolios ───────────────────────────────────────────

export function PublicPortfoliosList() {
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    fetch(`${API_BASE}/public/portfolios`)
      .then(r => r.ok ? r.json() : Promise.reject("Failed to load"))
      .then(d => setPortfolios(d.portfolios || []))
      .catch(() => setError("Could not load public portfolios."))
      .finally(() => setLoading(false));
  }, []);

  const filtered = portfolios.filter(p => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      p.display_name.toLowerCase().includes(q) ||
      (p.top_skills || []).some(s => s.toLowerCase().includes(q)) ||
      (p.summary || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="page-wrap">
      {/* Hero */}
      <div className="pp-list-hero card">
        <div className="pp-list-hero-text">
          <h1 className="pp-list-title">Public Portfolios</h1>
          <p className="pp-list-sub">Browse portfolios shared by the community</p>
        </div>
        <div className="pp-list-hero-actions">
          {!localStorage.getItem("token") && (
            <a href="/" className="btn-primary pp-list-cta" style={{ textDecoration: "none" }}>
              Sign In to Share Yours →
            </a>
          )}
          <button className="btn-secondary pp-back-btn" onClick={() => nav(-1)}>
            ← Back
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="pp-search-bar-wrap">
        <svg className="pp-search-bar-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          className="pp-search-bar-input"
          type="text"
          placeholder="Search by name, skills, or keywords…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button className="pp-search-bar-clear" onClick={() => setSearch("")} title="Clear">✕</button>
        )}
      </div>

      {loading && (
        <div className="pp-state-wrap">
          <div className="pp-state-spinner" />
          <p className="pp-state-text">Loading portfolios…</p>
        </div>
      )}
      {error && <div className="alert error">{error}</div>}

      {!loading && !error && portfolios.length === 0 && (
        <div className="card pp-state-wrap">
          <div className="pp-state-icon">🌐</div>
          <p className="pp-state-title">No public portfolios yet</p>
          <p className="pp-state-sub">Be the first to make your portfolio public!</p>
        </div>
      )}

      {!loading && !error && portfolios.length > 0 && filtered.length === 0 && (
        <div className="card pp-state-wrap">
          <div className="pp-state-icon">🔍</div>
          <p className="pp-state-title">No results for "{search}"</p>
          <button className="btn-secondary" style={{ marginTop: 12 }} onClick={() => setSearch("")}>Clear search</button>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <>
          <p className="pp-result-count">{filtered.length} portfolio{filtered.length !== 1 ? "s" : ""}</p>
          <div className="pp-list-grid">
            {filtered.map(p => {
              const initials = p.display_name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
              return (
                <div
                  key={p.user_id}
                  className="card pp-list-card"
                  onClick={() => nav(`/public-portfolios/${p.user_id}`)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === "Enter" && nav(`/public-portfolios/${p.user_id}`)}
                >
                  <div className="pp-list-card-top">
                    <div className="pp-list-avatar">{initials}</div>
                    <div className="pp-list-card-info">
                      <h3 className="pp-list-card-name">{p.display_name}</h3>
                      {p.about_subtitle && <p className="pp-list-card-role">{p.about_subtitle}</p>}
                      <span className="pp-list-project-count">
                        {p.project_count} project{p.project_count !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <span className="pp-public-badge">Public</span>
                  </div>

                  {p.summary && <p className="pp-list-card-summary">{p.summary}</p>}

                  {p.top_skills.length > 0 && (
                    <div className="pp-list-skills">
                      {p.top_skills.map(s => {
                        const tc = typeColor(s);
                        return (
                          <span key={s} className="pp-skill-chip" style={{ color: tc, borderColor: `${tc}55`, background: `${tc}15` }}>
                            {s}
                          </span>
                        );
                      })}
                    </div>
                  )}

                  <div className="pp-list-card-footer">
                    <span className="pp-list-view-link">View Portfolio →</span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ── Single public portfolio view ─────────────────────────────────────────────

export function PublicPortfolioView() {
  const { userId } = useParams();
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState("about");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortBy, setSortBy] = useState("importance");
  const [layout, setLayout] = useState("list");

  useEffect(() => {
    fetch(`${API_BASE}/public/portfolios/${userId}`)
      .then(r => r.ok ? r.json() : Promise.reject("Not found"))
      .then(setData)
      .catch(() => setError("This portfolio is not available or is not public."))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return (
    <div className="port-sidebar-layout" style={{ justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
      <div style={{ textAlign: "center", color: "#818cf8" }}>Loading…</div>
    </div>
  );

  if (error) return (
    <div className="page-wrap">
      <div className="card pp-empty" style={{ maxWidth: 480, margin: "80px auto", textAlign: "center", padding: 48 }}>
        <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🔒</div>
        <h2 style={{ margin: "0 0 8px" }}>Portfolio Not Available</h2>
        <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>{error}</p>
        <button className="btn-primary" onClick={() => nav("/public-portfolios")}>← Browse Portfolios</button>
      </div>
    </div>
  );

  const projects = data.projects || [];
  const education = data.education || [];
  const workHistory = data.work_history || [];
  const contact = data.contact_info || {};
  const stats = data.stats || {};
  const summaryText = data.summary_text || "";

  const projectTypes = ["all", ...Array.from(new Set(projects.map(p => p.type || p.project_type).filter(Boolean)))];

  const sorted = [...projects]
    .filter(p => {
      const q = search.toLowerCase();
      const matchSearch = !q ||
        (p.name || "").toLowerCase().includes(q) ||
        (p.description || "").toLowerCase().includes(q) ||
        (p.user_role || "").toLowerCase().includes(q) ||
        (p.skills || []).some(s => s.toLowerCase().includes(q)) ||
        (p.languages || p.tech_stack || []).some(t => t.toLowerCase().includes(q));
      const matchType = typeFilter === "all" || (p.type || p.project_type) === typeFilter;
      return matchSearch && matchType;
    })
    .sort((a, b) => {
      if (sortBy === "importance") return (b.importance_score || 0) - (a.importance_score || 0);
      if (sortBy === "name") return (a.name || "").localeCompare(b.name || "");
      if (sortBy === "date") return new Date(b.date || 0) - new Date(a.date || 0);
      return 0;
    });

  const featured = sorted.filter(p => p.is_featured);
  const rest = sorted.filter(p => !p.is_featured);

  // Derive skill cloud from projects
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

  // Experience helpers
  const sortedExp = [...workHistory].sort((a, b) => {
    const da = a.start_date ? new Date(a.start_date) : new Date(0);
    const db = b.start_date ? new Date(b.start_date) : new Date(0);
    return db - da;
  });
  const activeRoles = sortedExp.filter(e => !e.end_date || e.end_date === "Present").length;

  // Education helpers
  const sortedEdu = [...education].sort((a, b) => {
    const da = a.start_date ? new Date(a.start_date) : new Date(0);
    const db = b.start_date ? new Date(b.start_date) : new Date(0);
    return db - da;
  });
  const degreeCount = sortedEdu.filter(e => e.degree_type !== "Certification" && e.degree_type !== "Extra Curricular").length;
  const certCount = sortedEdu.filter(e => e.degree_type === "Certification").length;
  const extraCount = sortedEdu.filter(e => e.degree_type === "Extra Curricular").length;

  const hasContact = contact.email || contact.phone || contact.location ||
    contact.website || contact.linkedin || contact.github ||
    (contact.customPresences || []).some(p => p.url);

  const noop = () => {};

  return (
    <div className="port-sidebar-layout">

      {/* ── Sidebar ── */}
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
          <button
            className="btn-secondary port-sidebar-link-btn"
            onClick={() => nav("/public-portfolios")}
          >
            ← All Portfolios
          </button>
          {localStorage.getItem("token") && (
            <button className="btn-secondary port-sidebar-link-btn" onClick={() => nav("/portfolio")}>
              My Portfolio
            </button>
          )}
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="port-main">

        {/* About */}
        {activeSection === "about" && (
          <div className="port-about-wrapper">
            <div className="port-about-hero">
              <div className="port-about-left">
                <div className="port-about-avatar">
                  {(data.about_name || data.display_name || "?").charAt(0).toUpperCase()}
                </div>
                <div className="port-about-identity">
                  <p className="port-about-name-text">{data.about_name || data.display_name}</p>
                  {data.about_subtitle && <p className="port-about-sub-text">{data.about_subtitle}</p>}
                </div>
              </div>

              {data.about_bio && (
                <div className="port-about-right">
                  <div className="port-about-bio-section">
                    <span className="port-about-bio-label">About</span>
                    <p className="port-about-bio-text">{data.about_bio}</p>
                  </div>
                </div>
              )}
            </div>

            {summaryText && (
              <p className="port-hero-summary" style={{ marginTop: 32 }}>{summaryText}</p>
            )}
          </div>
        )}

        {/* Projects */}
        {activeSection === "projects" && (
          <div className="port-section-page">
            {summaryText && <p className="port-hero-summary" style={{ marginBottom: 24 }}>{summaryText}</p>}

            <div className="port-public-toolbar">
              <div className="port-search-wrap">
                <svg className="port-search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"
                  viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input
                  className="port-search-input"
                  type="text"
                  placeholder="Search projects, skills, technologies…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
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
                  <button className={`port-layout-btn ${layout === "list" ? "active" : ""}`} onClick={() => setLayout("list")} title="List view">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                  </button>
                  <button className={`port-layout-btn ${layout === "grid" ? "active" : ""}`} onClick={() => setLayout("grid")} title="Grid view">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                  </button>
                </div>
              </div>
            )}

            {projects.length === 0 ? (
              <div className="empty-state port-empty-illustrated">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "#6366f1", opacity: 0.6, marginBottom: 16 }}>
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                <p style={{ fontWeight: 700, fontSize: "1.05rem", color: "#c4cbf5", margin: 0 }}>No projects shared yet</p>
              </div>
            ) : sorted.length === 0 ? (
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
                    <div className="port-section-header port-section-header-featured">
                      <span>⭐ Featured Projects</span>
                    </div>
                    <div className="port-top-grid">
                      {featured.map((p, i) => (
                        <ProjectCard key={p.id} p={p} rank={i + 1}
                          editId={null} editForm={{}} setEditForm={noop} startEdit={noop}
                          saveEdit={noop} setEditId={noop} rankInput={{}} setRankInput={noop}
                          saveRank={noop} nav={nav} isPublic={true} toggleHidden={noop} />
                      ))}
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
                      {rest.map((p, i) => (
                        <ProjectCard key={p.id} p={p} rank={featured.length + i + 1}
                          editId={null} editForm={{}} setEditForm={noop} startEdit={noop}
                          saveEdit={noop} setEditId={noop} rankInput={{}} setRankInput={noop}
                          saveRank={noop} nav={nav} isPublic={true} toggleHidden={noop} />
                      ))}
                    </div>
                  ) : (
                    <div className="port-all-list">
                      {rest.map(p => (
                        <ProjectRow key={p.id} p={p}
                          editId={null} editForm={{}} setEditForm={noop} startEdit={noop}
                          saveEdit={noop} setEditId={noop} rankInput={{}} setRankInput={noop}
                          saveRank={noop} nav={nav} isPublic={true} toggleHidden={noop} />
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Skills & Stats */}
        {activeSection === "skills" && (
          <div className="port-section-page">
            {allSkills.length > 0 && (
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
            )}

            {Object.keys(stats).length > 0 && (
              <div className="port-stat-row">
                {[
                  ["Projects", stats.total_projects ?? projects.length],
                  ["Lines of Code", stats.total_lines_of_code > 0 ? stats.total_lines_of_code?.toLocaleString() : null],
                  ["Files", stats.total_files?.toLocaleString()],
                  ["Word Count", stats.total_word_count > 0 ? stats.total_word_count?.toLocaleString() : null],
                  ["Skills", stats.unique_skills_count],
                ].filter(([, v]) => v != null).map(([label, val]) => (
                  <div key={label} className="port-stat card">
                    <div className="port-stat-icon">{STAT_ICONS[label]}</div>
                    <div className="stat-val">{val}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>
            )}

            {allSkills.length === 0 && Object.keys(stats).length === 0 && (
              <div className="port-placeholder">
                <p style={{ color: "var(--text-muted)" }}>No skills data available.</p>
              </div>
            )}
          </div>
        )}

        {/* Experience */}
        {activeSection === "experience" && (
          <div className="port-section-page edu-page">
            <div className="edu-top-bar">
              <div className="edu-top-titles">
                <h1 className="edu-split-title">Experience</h1>
                <div className="edu-top-stats">
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{sortedExp.length}</span>
                    <span className="edu-top-stat-label">{sortedExp.length === 1 ? "Position" : "Positions"}</span>
                  </div>
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{activeRoles}</span>
                    <span className="edu-top-stat-label">{activeRoles === 1 ? "Current Role" : "Current Roles"}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="edu-body">
              <div className="edu-body-left" />
              <div className="edu-body-right">
                {sortedExp.length === 0 ? (
                  <div className="edu-empty-state">
                    <span className="edu-empty-icon">💼</span>
                    <p className="edu-empty-title">No experience listed</p>
                    <p className="edu-empty-sub">This user hasn't added work history yet.</p>
                  </div>
                ) : (
                  <>
                    <div className="edu-legend edu-legend-inline">
                      {EXP_LEGEND.map(([value, label]) => (
                        <span key={value} className="edu-legend-item">
                          <span className={`edu-legend-dot exp-legend-${value}`} />
                          {label}
                        </span>
                      ))}
                    </div>
                    <div className="edu-timeline-list">
                      <div className="edu-timeline-line" />
                      {sortedExp.map(entry => {
                        const startDate = entry.start_date ? new Date(entry.start_date) : null;
                        const endDate = entry.end_date && entry.end_date !== "Present" ? new Date(entry.end_date) : null;
                        const isPresent = !entry.end_date || entry.end_date === "Present";
                        const start = startDate ? startDate.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "?";
                        const end = endDate ? endDate.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "Present";
                        const expType = experienceTypeOf(entry);
                        return (
                          <div key={entry.id} className="edu-timeline-item">
                            <div className={`edu-timeline-dot exp-dot-${expType}`} />
                            <div className={`edu-timeline-content card edu-card-wrap exp-card-${expType}`}>
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
            <div className="edu-top-bar">
              <div className="edu-top-titles">
                <h1 className="edu-split-title">Education</h1>
                <div className="edu-top-stats">
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{degreeCount}</span>
                    <span className="edu-top-stat-label">{degreeCount === 1 ? "Degree" : "Degrees"}</span>
                  </div>
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{certCount}</span>
                    <span className="edu-top-stat-label">{certCount === 1 ? "Certification" : "Certifications"}</span>
                  </div>
                  <div className="edu-top-stat">
                    <span className="edu-top-stat-num">{extraCount}</span>
                    <span className="edu-top-stat-label">Extra Curricular</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="edu-body">
              <div className="edu-body-left" />
              <div className="edu-body-right">
                {sortedEdu.length === 0 ? (
                  <div className="edu-empty-state">
                    <span className="edu-empty-icon">🎓</span>
                    <p className="edu-empty-title">No education listed</p>
                    <p className="edu-empty-sub">This user hasn't added education history yet.</p>
                  </div>
                ) : (
                  <>
                    <div className="edu-legend edu-legend-inline">
                      <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-degree" />Post Secondary</span>
                      <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-secondary" />Secondary</span>
                      <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-cert" />Certification</span>
                      <span className="edu-legend-item"><span className="edu-legend-dot edu-legend-extra" />Extra Curricular</span>
                    </div>
                    <div className="edu-timeline-list">
                      <div className="edu-timeline-line" />
                      {sortedEdu.map((entry, i) => {
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

        {/* Contact */}
        {activeSection === "contact" && (
          <div className="port-section-page">
            <div className="port-contact-shell">
              <div className="port-contact-hero card">
                <div className="port-contact-copy">
                  <span className="port-contact-kicker">Contact</span>
                  <h2 className="port-contact-title">Contact Information</h2>
                  {contact.intro ? (
                    <p className="port-contact-intro">{contact.intro}</p>
                  ) : (
                    <p className="port-contact-empty">No contact summary added.</p>
                  )}
                </div>
                {contact.availability && (
                  <div className="port-contact-status">
                    <span className="port-contact-status-label">Job Search Status</span>
                    <p className="port-contact-status-text">{contact.availability}</p>
                  </div>
                )}
              </div>

              {!hasContact ? (
                <div className="card" style={{ padding: 32, textAlign: "center", color: "var(--text-muted)" }}>
                  No contact details have been added yet.
                </div>
              ) : (
                <div className="port-contact-grid">
                  <div className="port-contact-card card">
                    <div className="port-section-header"><span>Personal Details</span></div>
                    <div className="port-contact-fields">
                      <ContactField label="Email" value={contact.email} isPublic={true}
                        href={contact.email ? `mailto:${contact.email}` : ""} />
                      <ContactField label="Phone" value={contact.phone} isPublic={true}
                        href={contact.phone ? `tel:${contact.phone.replace(/\s+/g, "")}` : ""} />
                      <ContactField label="Location" value={contact.location} isPublic={true} />
                    </div>
                  </div>

                  <div className="port-contact-card card">
                    <div className="port-section-header"><span>Online Presence</span></div>
                    <div className="port-contact-fields">
                      <ContactField label="Website" value={contact.website} isPublic={true} href={contact.website} />
                      <ContactField label="LinkedIn" value={contact.linkedin} isPublic={true} href={contact.linkedin} />
                      <ContactField label="GitHub" value={contact.github} isPublic={true} href={contact.github} />
                      {(contact.customPresences || []).map(item => (
                        <CustomPresenceField key={item.id} item={item} isPublic={true} onChange={noop} onRemove={noop} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
