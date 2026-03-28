import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

const API_BASE = "http://127.0.0.1:8000";

const TYPE_COLORS = {
  python: "#3b82f6", javascript: "#f59e0b", typescript: "#6366f1",
  java: "#ef4444", web: "#10b981", mobile: "#8b5cf6",
  ml: "#ec4899", data: "#14b8a6", default: "#6366f1",
};
function typeColor(type) {
  const t = (type || "").toLowerCase();
  for (const [key, col] of Object.entries(TYPE_COLORS)) if (t.includes(key)) return col;
  return TYPE_COLORS.default;
}

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
      <div className="card" style={{
        background: "linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(163,73,255,0.14) 100%)",
        borderColor: "rgba(163,73,255,0.3)",
        marginBottom: 24,
        display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16,
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.9rem", fontWeight: 800, color: "#eef1ff" }}>
            Public Portfolios
          </h1>
          <p style={{ margin: "4px 0 0", color: "#9aa6de", fontSize: "0.88rem" }}>
            Browse portfolios shared by other users
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {!localStorage.getItem("token") && (
            <a href="/" className="btn-primary" style={{ textDecoration: "none" }}>
              ← Back to Login
            </a>
          )}
          <button className="btn-secondary" onClick={() => nav(-1)}>
            ← Back
          </button>
        </div>
      </div>

      {/* Search */}
      <div style={{ position: "relative", marginBottom: 20 }}>
        <svg style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", opacity: 0.5 }}
          xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          style={{ width: "100%", paddingLeft: 40, boxSizing: "border-box" }}
          type="text"
          placeholder="Search by name, skills, or keywords…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {loading && <div style={{ textAlign: "center", color: "#818cf8", padding: 40 }}>Loading…</div>}
      {error && <div className="alert error">{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 48, color: "#9aa6de" }}>
          {search ? "No portfolios match your search." : "No public portfolios available yet."}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {filtered.map(p => (
          <div
            key={p.user_id}
            className="card"
            style={{ cursor: "pointer", transition: "border-color 0.2s, transform 0.15s, box-shadow 0.2s" }}
            onClick={() => nav(`/public-portfolios/${p.user_id}`)}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(163,73,255,0.6)"; e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 12px 22px rgba(115,67,255,0.28)"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = ""; e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = ""; }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#eef1ff" }}>
                  {p.display_name}
                </h3>
                <span style={{ fontSize: "0.78rem", color: "#9aa6de" }}>
                  {p.project_count} project{p.project_count !== 1 ? "s" : ""}
                </span>
              </div>
              <span style={{
                fontSize: "0.72rem", padding: "3px 8px", borderRadius: 20,
                background: "rgba(99,102,241,0.18)", color: "#a5b4fc", border: "1px solid rgba(99,102,241,0.3)",
              }}>
                Public
              </span>
            </div>

            {p.summary && (
              <p style={{ fontSize: "0.83rem", color: "#c4cbf5", lineHeight: 1.6, margin: "0 0 12px", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {p.summary}
              </p>
            )}

            {p.top_skills.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {p.top_skills.map(s => (
                  <span key={s} style={{
                    fontSize: "0.72rem", padding: "2px 8px", borderRadius: 12,
                    background: "rgba(99,102,241,0.12)", color: "#c4b5fd",
                    border: "1px solid rgba(99,102,241,0.25)",
                  }}>
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
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
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    fetch(`${API_BASE}/public/portfolios/${userId}`)
      .then(r => r.ok ? r.json() : Promise.reject("Not found"))
      .then(setData)
      .catch(() => setError("This portfolio is not available or is not public."))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <div className="page-wrap" style={{ textAlign: "center", color: "#818cf8", paddingTop: 80 }}>Loading…</div>;
  if (error) return (
    <div className="page-wrap">
      <div className="card" style={{ textAlign: "center", padding: 48 }}>
        <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🔒</div>
        <h2 style={{ margin: "0 0 8px" }}>Portfolio Not Available</h2>
        <p style={{ color: "#9aa6de", marginBottom: 24 }}>{error}</p>
        <button className="btn-primary" onClick={() => nav("/public-portfolios")}>← Browse Portfolios</button>
      </div>
    </div>
  );

  const projects = data.projects || [];
  const projectTypes = ["all", ...Array.from(new Set(projects.map(p => p.type || p.project_type).filter(Boolean)))];

  const filtered = projects.filter(p => {
    const q = search.toLowerCase();
    const matchSearch = !q ||
      (p.name || "").toLowerCase().includes(q) ||
      (p.description || "").toLowerCase().includes(q) ||
      (p.skills || []).some(s => s.toLowerCase().includes(q)) ||
      (p.languages || p.tech_stack || []).some(t => t.toLowerCase().includes(q));
    const matchType = typeFilter === "all" || (p.type || p.project_type) === typeFilter;
    return matchSearch && matchType;
  });

  const stats = data.stats || {};

  return (
    <div className="page-wrap">
      {/* Hero */}
      <div className="card" style={{
        background: "linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(163,73,255,0.14) 100%)",
        borderColor: "rgba(163,73,255,0.3)",
        marginBottom: 24,
        display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16,
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.9rem", fontWeight: 800, color: "#eef1ff" }}>
            {data.display_name}'s Portfolio
          </h1>
          {data.summary_text && (
            <p style={{
              margin: "8px 0 0", color: "#c4cbf5", fontSize: "0.9rem", lineHeight: 1.7, maxWidth: 600,
              borderLeft: "3px solid rgba(163,73,255,0.5)", paddingLeft: 12,
            }}>
              {data.summary_text}
            </p>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {!localStorage.getItem("token") && (
            <a href="/" className="btn-primary" style={{ textDecoration: "none" }}>
              ← Back to Login
            </a>
          )}
          <button className="btn-secondary" onClick={() => nav("/public-portfolios")}>
            ← All Portfolios
          </button>
        </div>
      </div>

      {/* Stats */}
      {Object.keys(stats).length > 0 && (
        <div className="port-stat-row" style={{ marginBottom: 24 }}>
          {stats.total_projects != null && (
            <div className="card port-stat">
              <div className="port-stat-icon">📁</div>
              <div className="stat-val">{stats.total_projects}</div>
              <div className="stat-label">Projects</div>
            </div>
          )}
          {stats.total_lines_of_code != null && (
            <div className="card port-stat">
              <div className="port-stat-icon">💻</div>
              <div className="stat-val">{stats.total_lines_of_code?.toLocaleString()}</div>
              <div className="stat-label">Lines of Code</div>
            </div>
          )}
          {stats.total_skills != null && (
            <div className="card port-stat">
              <div className="port-stat-icon">⚡</div>
              <div className="stat-val">{stats.total_skills}</div>
              <div className="stat-label">Skills</div>
            </div>
          )}
          {stats.total_files != null && (
            <div className="card port-stat">
              <div className="port-stat-icon">🗂️</div>
              <div className="stat-val">{stats.total_files}</div>
              <div className="stat-label">Files</div>
            </div>
          )}
        </div>
      )}

      {/* Search + filter toolbar */}
      <div className="port-public-toolbar" style={{ marginBottom: 20 }}>
        <div className="port-search-wrap">
          <svg className="port-search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
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
        <select className="port-type-select" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
          {projectTypes.map(t => <option key={t} value={t}>{t === "all" ? "All Types" : t}</option>)}
        </select>
        {(search || typeFilter !== "all") && (
          <span className="port-result-count">{filtered.length} result{filtered.length !== 1 ? "s" : ""}</span>
        )}
      </div>

      {/* Project cards */}
      {filtered.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 40, color: "#9aa6de" }}>
          No projects match your search.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {filtered.map(p => {
          const color = typeColor(p.type || p.project_type);
          const langs = p.languages || p.tech_stack || [];
          const skills = p.skills || [];
          return (
            <div key={p.id} className="card" style={{ borderLeft: `3px solid ${color}`, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 6 }}>
                    <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "#eef1ff" }}>
                      {p.name}
                    </h3>
                    {p.is_featured && (
                      <span style={{ fontSize: "0.7rem", padding: "2px 8px", borderRadius: 12, background: "rgba(245,158,11,0.15)", color: "#fbbf24", border: "1px solid rgba(245,158,11,0.3)" }}>
                        Featured
                      </span>
                    )}
                    {(p.type || p.project_type) && (
                      <span style={{ fontSize: "0.7rem", padding: "2px 8px", borderRadius: 12, background: `${color}22`, color, border: `1px solid ${color}44` }}>
                        {p.type || p.project_type}
                      </span>
                    )}
                  </div>
                  {p.description && (
                    <p style={{ margin: "0 0 10px", fontSize: "0.85rem", color: "#c4cbf5", lineHeight: 1.6 }}>
                      {p.description}
                    </p>
                  )}
                  {p.user_role && (
                    <p style={{ margin: "0 0 8px", fontSize: "0.78rem", color: "#9aa6de" }}>
                      Role: <span style={{ color: "#c4b5fd" }}>{p.user_role}</span>
                    </p>
                  )}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                    {langs.slice(0, 5).map(l => (
                      <span key={l} style={{ fontSize: "0.7rem", padding: "2px 7px", borderRadius: 10, background: "rgba(59,130,246,0.12)", color: "#93c5fd", border: "1px solid rgba(59,130,246,0.25)" }}>
                        {l}
                      </span>
                    ))}
                    {skills.slice(0, 5).map(s => (
                      <span key={s} style={{ fontSize: "0.7rem", padding: "2px 7px", borderRadius: 10, background: "rgba(99,102,241,0.12)", color: "#c4b5fd", border: "1px solid rgba(99,102,241,0.25)" }}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                {p.importance_score != null && (
                  <div style={{ textAlign: "center", minWidth: 52 }}>
                    <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "#c4b5fd" }}>
                      {Math.round(p.importance_score)}
                    </div>
                    <div style={{ fontSize: "0.65rem", color: "#9aa6de", textTransform: "uppercase", letterSpacing: "0.05em" }}>Score</div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
