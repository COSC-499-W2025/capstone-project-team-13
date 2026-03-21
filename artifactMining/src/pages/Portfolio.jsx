import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Portfolio.css";

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState(null);
  const [includeHidden, setIncludeHidden] = useState(false);
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [rankInput, setRankInput] = useState({});
  const [sortBy, setSortBy] = useState("importance"); // importance | date | rank | name
  const nav = useNavigate();

  useEffect(() => { load(); }, [includeHidden]);

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
    if (sortBy === "rank") return (a.user_rank ?? 999) - (b.user_rank ?? 999);
    if (sortBy === "name") return (a.name || "").localeCompare(b.name || "");
    if (sortBy === "date") return new Date(b.date || 0) - new Date(a.date || 0);
    return 0;
  });

  const featured = sorted.filter(p => p.is_featured);
  const rest = sorted.filter(p => !p.is_featured);

  const stats = portfolio?.stats || {};
  const summaryText = portfolio?.summary_text || portfolio?.summary?.text || "";

  return (
    <div className="page-wrap">
      <div className="port-header">
        <div>
          <h1>Master Portfolio</h1>
          <p className="text-muted">All projects · evidences · ranked</p>
        </div>
        <div className="port-header-actions">
          <label className="toggle-label">
            <input type="checkbox" checked={includeHidden} onChange={e => setIncludeHidden(e.target.checked)} />
            Show hidden
          </label>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{ width: "auto", padding: "8px 12px" }}>
            <option value="importance">Sort: Importance</option>
            <option value="rank">Sort: User Rank</option>
            <option value="date">Sort: Date</option>
            <option value="name">Sort: Name</option>
          </select>
          <button className="btn-primary" onClick={generate} disabled={generating}>
            {generating ? "Generating…" : "↻ Regenerate"}
          </button>
        </div>
      </div>

      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {loading ? <div className="spinner" style={{ marginTop: 40 }} /> : <>
        {(summaryText || Object.keys(stats).length > 0) && (
          <div className="card port-summary">
            {summaryText && <p style={{ lineHeight: 1.7, color: "#b8c0e8" }}>{summaryText}</p>}
            {Object.keys(stats).length > 0 && (
              <div className="port-stat-row" style={{ marginTop: summaryText ? 16 : 0, marginBottom: 0 }}>
                {[
                  ["Projects", stats.total_projects ?? projects.length],
                  ["LOC", stats.total_lines_of_code?.toLocaleString()],
                  ["Files", stats.total_files?.toLocaleString()],
                  ["Skills", stats.unique_skills_count ?? portfolio?.unique_skills_count],
                ].filter(([, v]) => v != null).map(([label, val]) => (
                  <div key={label} className="port-stat card" style={{ padding: 14 }}>
                    <div className="stat-val">{val}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
              </div>
            )}
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
                <h2 style={{ marginBottom: 16 }}>⭐ Featured Projects</h2>
                <div className="port-top-grid">
                  {featured.map((p, i) => <ProjectCard key={p.id} p={p} rank={i + 1} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} />)}
                </div>
              </div>
            )}
            <div className="port-section">
              <h2 style={{ marginBottom: 16 }}>{featured.length > 0 ? "All Other Projects" : "All Projects"}</h2>
              <div className="port-all-list">
                {rest.map(p => <ProjectRow key={p.id} p={p} editId={editId} editForm={editForm} setEditForm={setEditForm} startEdit={startEdit} saveEdit={saveEdit} setEditId={setEditId} rankInput={rankInput} setRankInput={setRankInput} saveRank={saveRank} nav={nav} />)}
              </div>
            </div>
          </>
        )}
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
  return (
    <div className="port-top-card card">
      <div className="port-rank">#{rank}</div>
      <div className="port-card-tags">
        <span className="tag">{p.type || p.project_type}</span>
        {p.is_featured && <span className="tag success">⭐</span>}
        {p.is_hidden && <span className="tag warning">hidden</span>}
      </div>
      <h3 className="port-proj-name">{projectName(p)}</h3>
      <p className="port-proj-desc text-muted">{p.description || "No description"}</p>
      {p.user_role && <p style={{ fontSize: "0.8rem", color: "#a5b4fc", marginTop: 4 }}>Role: {p.user_role}</p>}
      <EvidenceSection p={p} />
      <div className="chip-group" style={{ marginTop: 8 }}>
        {(p.tech_stack || p.languages || []).slice(0, 4).map((t, i) => <span key={i} className="tag accent">{t}</span>)}
      </div>
      {p.metrics && (
        <div className="port-metrics">
          {p.metrics.lines_of_code > 0 && <span>{p.metrics.lines_of_code?.toLocaleString()} LOC</span>}
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
  return (
    <div className="port-list-row card">
      <div className="port-list-main">
        <div className="port-list-top">
          <strong className="port-list-name">{projectName(p)}</strong>
          <div style={{ display: "flex", gap: 6 }}>
            <span className="tag">{p.type || p.project_type}</span>
            {p.is_featured && <span className="tag success">⭐</span>}
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