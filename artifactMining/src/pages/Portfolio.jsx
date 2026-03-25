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

const SORT_OPTIONS = [
  { value: "importance", label: "Importance" },
  { value: "rank",       label: "User Rank" },
  { value: "date",       label: "Date" },
  { value: "name",       label: "Name" },
];

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
  const nav = useNavigate();

  useEffect(() => {
    const sync = () => setShowEmojis(localStorage.getItem("dash_show_emojis") !== "false");
    window.addEventListener("dash-emojis-updated", sync);
    return () => window.removeEventListener("dash-emojis-updated", sync);
  }, []);

  const e = (emoji) => showEmojis ? emoji : null;

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setAuthed(false); return; }
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (r.ok) setAuthed(true); else { localStorage.removeItem("token"); setAuthed(false); } })
      .catch(() => { localStorage.removeItem("token"); setAuthed(false); });
  }, []);

  useEffect(() => { if (authed === true) load(); }, [authed, includeHidden]);

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

  const projects = portfolio?.projects || [];
  const sorted = [...projects].sort((a, b) => {
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
    <div className="page-wrap">

      {/* ── Hero header ── */}
      <div className="port-hero card">
        <div className="port-hero-text">
          <h1 className="port-hero-title">Master Portfolio</h1>
          <p className="port-hero-sub">All projects · evidences · ranked</p>
          {summaryText && <p className="port-hero-summary">{summaryText}</p>}
        </div>
        <div className="port-hero-actions">
          <Link to="/showcase" className="btn-primary" style={{ display: "inline-block", textDecoration: "none", padding: "0.6em 1.2em", borderRadius: 8, fontSize: "0.95em", fontWeight: 500, transition: "opacity 0.25s, border-color 0.25s", color: "#fff" }}>
            Web Showcase
          </Link>
          <label className="toggle-label">
            <input type="checkbox" checked={includeHidden} onChange={e => setIncludeHidden(e.target.checked)} />
            Show hidden
          </label>
          <button className="btn-primary" onClick={generate} disabled={generating}>
            {generating ? "Generating…" : "↻ Regenerate"}
          </button>
        </div>
      </div>

      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {loading ? <div className="spinner" style={{ marginTop: 40 }} /> : <>

        {/* ── Stats row ── */}
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

        {/* ── Sort pills ── */}
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
          </div>
        )}

        {projects.length === 0 ? (
          <div className="empty-state">
            <p>No portfolio data yet.</p>
            <p style={{ marginTop: 8, fontSize: "0.9rem" }}>Click <strong>Regenerate</strong> to build from your projects.</p>
          </div>
        ) : (
          <>
            {featured.length > 0 && (
              <div className="port-section">
                <div className="port-section-header">
                  <span>{e("⭐ ")}Featured Projects</span>
                </div>
                <div className="port-top-grid">
                  {featured.map((p, i) => <ProjectCard key={p.id} p={p} rank={i + 1} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} />)}
                </div>
              </div>
            )}
            <div className="port-section">
              <div className="port-section-header">
                <span>{featured.length > 0 ? "All Other Projects" : "All Projects"}</span>
              </div>
              <div className="port-all-list">
                {rest.map(p => <ProjectRow key={p.id} p={p} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} />)}
              </div>
            </div>
          </>
        )}

        {/* ── Skills Timeline ── */}
        <div className="port-viz-card card">
          <div className="port-section-header"><span>📈 Skills Timeline</span></div>
          <SkillsTimeline />
        </div>

        {/* ── Activity Heatmap ── */}
        <div className="port-viz-card card" style={{ marginTop: 16 }}>
          <div className="port-section-header"><span>🗓️ Project Activity</span></div>
          <ActivityHeatmap />
        </div>

      </>}
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

function ProjectCard({ p, rank, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav }) {
  const accent = typeColor(p.type || p.project_type);
  return (
    <div className="port-top-card card" style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="port-rank">#{rank}</div>
      <div className="port-card-tags">
        <span className="tag">{p.type || p.project_type}</span>
        {p.is_featured && showEmojis && <span className="tag success">⭐</span>}
        {p.is_hidden && <span className="tag warning">hidden</span>}
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
      <div className="port-rank-row">
        <input type="number" min="0" max="1" step="0.01" placeholder="Score 0–1"
          value={rankInput[p.id] ?? p.importance_score ?? ""}
          onChange={e => setRankInput({ ...rankInput, [p.id]: e.target.value })}
          style={{ width: 100, padding: "5px 8px" }} />
        <button className="btn-secondary" style={{ padding: "5px 10px", fontSize: "0.8rem" }} onClick={() => saveRank(p.id)}>Set</button>
      </div>
      <div className="port-card-actions">
        <button className="btn-secondary" onClick={() => nav(`/projects/${p.id}`)}>View</button>
        <button className="btn-secondary" onClick={() => editId === p.id ? setEditId(null) : startEdit(p)}>{editId === p.id ? "Cancel" : "Edit"}</button>
      </div>
      {editId === p.id && <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />}
    </div>
  );
}

function ProjectRow({ p, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav }) {
  const accent = typeColor(p.type || p.project_type);
  const score = p.importance_score ?? 0;
  return (
    <div className="port-list-row card" style={{ borderLeft: `3px solid ${accent}` }}>
      {/* Importance bar on left */}
      <div className="port-score-bar" style={{ background: accent, height: `${Math.round(score * 100)}%` }} />
      <div className="port-list-main">
        <div className="port-list-top">
          <strong className="port-list-name">{projectName(p)}</strong>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <span className="tag">{p.type || p.project_type}</span>
            {p.is_featured && showEmojis && <span className="tag success">⭐</span>}
            {p.is_hidden && <span className="tag warning">hidden</span>}
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
        <div className="port-rank-row">
          <input type="number" min="0" max="1" step="0.01" placeholder="0–1"
            value={rankInput[p.id] ?? p.importance_score ?? ""}
            onChange={e => setRankInput({ ...rankInput, [p.id]: e.target.value })}
            style={{ width: 70, padding: "5px 6px", fontSize: "0.8rem" }} />
          <button className="btn-secondary" style={{ padding: "5px 8px", fontSize: "0.75rem" }} onClick={() => saveRank(p.id)}>Set</button>
        </div>
        <button className="btn-secondary" style={{ padding: "6px 12px" }} onClick={() => nav(`/projects/${p.id}`)}>View</button>
        <button className="btn-secondary" style={{ padding: "6px 12px" }} onClick={() => editId === p.id ? setEditId(null) : startEdit(p)}>{editId === p.id ? "Cancel" : "Edit"}</button>
      </div>
      {editId === p.id && (
        <div style={{ width: "100%", marginTop: 12 }}>
          <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />
        </div>
      )}
    </div>
  );
}
