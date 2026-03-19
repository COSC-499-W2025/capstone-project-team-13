import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Projects.css";

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const nav = useNavigate();

  useEffect(() => {
    apiFetch("/projects")
      .then(d => { setProjects(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const types = ["all", ...new Set(projects.map(p => p.project_type).filter(Boolean))];

  const filtered = projects.filter(p => {
    const name = projectName(p).toLowerCase();
    const matchText = name.includes(filter.toLowerCase());
    const matchType = typeFilter === "all" || p.project_type === typeFilter;
    return matchText && matchType;
  });

  const sorted = [...filtered].sort((a, b) => (b.importance_score || 0) - (a.importance_score || 0));

  function formatBytes(b) {
    if (!b) return "—";
    const k = 1024, sz = ["B","KB","MB","GB"], i = Math.floor(Math.log(b) / Math.log(k));
    return (b / Math.pow(k, i)).toFixed(1) + " " + sz[i];
  }

  return (
    <div className="page-wrap">
      <div className="proj-header">
        <h1>Projects</h1>
        <button className="btn-primary" onClick={() => nav("/upload")}>+ Upload</button>
      </div>

      <div className="proj-filters">
        <input placeholder="Search projects…" value={filter} onChange={e => setFilter(e.target.value)} style={{ maxWidth: 260 }} />
        <div className="type-tabs">
          {types.map(t => (
            <button key={t} className={`tab-btn ${typeFilter === t ? "active" : ""}`} onClick={() => setTypeFilter(t)}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {loading
        ? <div className="spinner" style={{ marginTop: 40 }} />
        : sorted.length === 0
          ? <div className="empty-state"><p>No projects found. Upload one to get started.</p></div>
          : <div className="proj-grid">
              {sorted.map(p => (
                <div key={p.id} className="proj-card card" onClick={() => nav(`/projects/${p.id}`)}>
                  <div className="proj-card-top">
                    <span className="tag">{p.project_type || "unknown"}</span>
                    {p.is_featured && <span className="tag success">⭐ featured</span>}
                    {p.importance_score != null && <span className="tag accent">{Number(p.importance_score).toFixed(1)}</span>}
                  </div>
                  <h3 className="proj-name">{projectName(p)}</h3>
                  <p className="proj-desc text-muted">{
                    p.ai_description || p.description ||
                    (p.languages?.length > 0 ? `${p.project_type || "Project"} using ${p.languages.slice(0,3).join(", ")}` : null) ||
                    (p.file_count ? `${p.project_type || "Project"} with ${p.file_count} file${p.file_count !== 1 ? "s" : ""}` : null) ||
                    `${p.project_type || "Unknown"} project`
                  }</p>
                  <div className="proj-meta">
                    {p.languages?.length > 0 && <span>{p.languages.slice(0,3).join(", ")}</span>}
                    <span>{formatBytes(p.total_size_bytes)}</span>
                    {p.file_count != null && <span>{p.file_count} files</span>}
                  </div>
                </div>
              ))}
            </div>
      }
    </div>
  );
}