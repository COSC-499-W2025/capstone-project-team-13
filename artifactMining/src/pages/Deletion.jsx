import React, { useEffect, useState } from "react";
import { apiFetch } from "../apiClient";
import "./Deletion.css";

export default function Deletion() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sharedReport, setSharedReport] = useState(null);
  const [cacheStats, setCacheStats] = useState(null);
  const [tab, setTab] = useState("delete"); // delete | insights | cache

  useEffect(() => { loadProjects(); }, []);

  async function loadProjects() {
    try { const d = await apiFetch("/projects"); setProjects(Array.isArray(d) ? d : []); }
    catch { setProjects([]); }
  }

  function toggleSelect(id) {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }
  function selectAll() { setProjects(p => { setSelected(new Set(p.map(x => x.id))); return p; }); }
  function clearSelection() { setSelected(new Set()); }

  async function deleteSelected() {
    if (selected.size === 0) { setMsg({ type: "error", text: "Select at least one project." }); return; }
    if (!window.confirm(`Delete ${selected.size} project(s)? This cannot be undone.`)) return;
    setLoading(true); setMsg(null);
    const results = [];
    for (const id of selected) {
      try {
        await apiFetch(`/projects/${id}`, { method: "DELETE" });
        results.push({ id, ok: true });
      } catch (e) { results.push({ id, ok: false, error: e.message }); }
    }
    const ok = results.filter(r => r.ok).length;
    const fail = results.filter(r => !r.ok).length;
    setMsg({ type: ok > 0 ? "success" : "error", text: `Deleted ${ok} project(s)${fail > 0 ? `, ${fail} failed` : ""}.` });
    setSelected(new Set());
    loadProjects();
    setLoading(false);
  }

  async function deleteAiInsights(id) {
    if (!window.confirm("Delete AI insights for this project?")) return;
    try {
      await apiFetch(`/projects/${id}/ai-insights`, { method: "DELETE" });
      setMsg({ type: "success", text: "AI insights deleted." });
      loadProjects();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function deleteAllAiInsights() {
    if (!window.confirm("Delete ALL AI insights across all projects? This cannot be undone.")) return;
    const confirmed = window.prompt('Type "DELETE ALL" to confirm');
    if (confirmed !== "DELETE ALL") { setMsg({ type: "info", text: "Cancelled." }); return; }
    setLoading(true);
    try {
      await apiFetch("/projects/ai-insights/all", { method: "DELETE" });
      setMsg({ type: "success", text: "All AI insights deleted." });
      loadProjects();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function loadSharedReport() {
    setLoading(true);
    try { const d = await apiFetch("/projects/shared-files"); setSharedReport(d); }
    catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function loadCacheStats() {
    setLoading(true);
    try { const d = await apiFetch("/projects/cache-stats"); setCacheStats(d); }
    catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function clearCache() {
    if (!window.confirm("Clear all AI analysis cache?")) return;
    try {
      await apiFetch("/projects/cache", { method: "DELETE" });
      setMsg({ type: "success", text: "Cache cleared." });
      setCacheStats(null);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  const projName = p => p.custom_description || p.name || `Project ${p.id}`;

  return (
    <div className="page-wrap">
      <h1 style={{ marginBottom: 8 }}>Deletion Manager</h1>
      <p className="text-muted" style={{ marginBottom: 24 }}>Safely delete projects, AI insights, and cache</p>

      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="del-tabs">
        {[["delete", "🗑 Delete Projects"], ["insights", "🤖 AI Insights"], ["cache", "📦 Cache"]].map(([t, l]) => (
          <button key={t} className={`del-tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>{l}</button>
        ))}
      </div>

      {tab === "delete" && (
        <div className="del-layout">
          <div className="card del-list-panel">
            <div className="del-list-header">
              <h3>Projects ({projects.length})</h3>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn-secondary" style={{ padding: "5px 10px", fontSize: "0.78rem" }} onClick={selectAll}>All</button>
                <button className="btn-secondary" style={{ padding: "5px 10px", fontSize: "0.78rem" }} onClick={clearSelection}>None</button>
              </div>
            </div>
            {projects.map(p => (
              <div key={p.id} className={`del-proj-row ${selected.has(p.id) ? "selected" : ""}`} onClick={() => toggleSelect(p.id)}>
                <input type="checkbox" checked={selected.has(p.id)} onChange={() => {}} onClick={e => e.stopPropagation()} />
                <div className="del-proj-info">
                  <span className="del-proj-name">{projName(p)}</span>
                  <span className="tag">{p.project_type || "?"}</span>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="card">
              <h3 style={{ marginBottom: 8 }}>Delete Selected ({selected.size})</h3>
              <p className="text-muted" style={{ marginBottom: 14, fontSize: "0.88rem" }}>
                Projects will be safely removed. Files shared across multiple projects are protected.
              </p>
              <button className="btn-danger" onClick={deleteSelected} disabled={loading || selected.size === 0}>
                {loading ? "Deleting…" : `Delete ${selected.size} Project${selected.size !== 1 ? "s" : ""}`}
              </button>
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 8 }}>Shared Files Report</h3>
              <p className="text-muted" style={{ marginBottom: 12, fontSize: "0.88rem" }}>View which files are used by multiple projects.</p>
              <button className="btn-secondary" onClick={loadSharedReport} disabled={loading}>Load Report</button>
              {sharedReport && (
                <div style={{ marginTop: 14 }}>
                  {sharedReport.length === 0
                    ? <p className="text-muted">No shared files detected.</p>
                    : sharedReport.map((item, i) => (
                      <div key={i} style={{ marginBottom: 12 }}>
                        <p style={{ fontWeight: 600, fontSize: "0.88rem", color: "#eef1ff" }}>{item.project_name}</p>
                        {(item.shared_files || []).slice(0, 5).map((f, j) => (
                          <p key={j} style={{ fontSize: "0.78rem", color: "#9aa6de", paddingLeft: 12 }}>• {f}</p>
                        ))}
                      </div>
                    ))
                  }
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === "insights" && (
        <div className="del-layout">
          <div className="card del-list-panel">
            <h3 style={{ marginBottom: 12 }}>Projects</h3>
            {projects.map(p => (
              <div key={p.id} className="del-proj-row" style={{ cursor: "default" }}>
                <div className="del-proj-info">
                  <span className="del-proj-name">{projName(p)}</span>
                  <div style={{ display: "flex", gap: 6 }}>
                    {p.ai_description && <span className="tag accent">has AI</span>}
                    <span className="tag">{p.project_type || "?"}</span>
                  </div>
                </div>
                <button className="btn-danger" style={{ padding: "4px 10px", fontSize: "0.78rem" }} onClick={() => deleteAiInsights(p.id)}>
                  Delete AI
                </button>
              </div>
            ))}
          </div>

          <div className="card" style={{ height: "fit-content" }}>
            <h3 style={{ marginBottom: 8 }}>Delete ALL AI Insights</h3>
            <p className="text-muted" style={{ marginBottom: 14, fontSize: "0.88rem" }}>
              Removes AI descriptions and cached analysis files for every project. Requires double confirmation.
            </p>
            <button className="btn-danger" onClick={deleteAllAiInsights} disabled={loading}>Delete All AI Insights</button>
          </div>
        </div>
      )}

      {tab === "cache" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div className="card">
            <h3 style={{ marginBottom: 8 }}>Cache Statistics</h3>
            <p className="text-muted" style={{ marginBottom: 12, fontSize: "0.88rem" }}>View current AI analysis cache usage.</p>
            <button className="btn-secondary" onClick={loadCacheStats} disabled={loading}>Load Stats</button>
            {cacheStats && (
              <div style={{ marginTop: 16 }}>
                {[
                  ["Total Files", cacheStats.total_cache_files],
                  ["Total Size", cacheStats.total_cache_size_bytes != null ? `${(cacheStats.total_cache_size_bytes / 1024).toFixed(1)} KB` : null],
                  ["Oldest Entry", cacheStats.oldest_cache],
                  ["Newest Entry", cacheStats.newest_cache],
                ].filter(([, v]) => v != null).map(([k, v]) => (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid rgba(107,114,244,0.12)", fontSize: "0.88rem" }}>
                    <span className="text-muted">{k}</span>
                    <span style={{ color: "#c4cbf5" }}>{v}</span>
                  </div>
                ))}
                {cacheStats.cache_by_type && Object.entries(cacheStats.cache_by_type).length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <p style={{ fontSize: "0.82rem", color: "#9aa6de", marginBottom: 8 }}>By type:</p>
                    {Object.entries(cacheStats.cache_by_type).map(([k, v]) => (
                      <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", padding: "3px 0", color: "#c4cbf5" }}>
                        <span>{k}</span><span>{v}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="card" style={{ height: "fit-content" }}>
            <h3 style={{ marginBottom: 8 }}>Clear Cache</h3>
            <p className="text-muted" style={{ marginBottom: 14, fontSize: "0.88rem" }}>
              Deletes all cached AI analysis files. Projects are not affected — only the cached results are removed.
            </p>
            <button className="btn-danger" onClick={clearCache}>Clear All Cache</button>
          </div>
        </div>
      )}
    </div>
  );
}
