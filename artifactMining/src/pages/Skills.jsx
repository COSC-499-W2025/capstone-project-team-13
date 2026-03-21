import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Skills.css";

export default function Skills() {
  const [skills, setSkills] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    Promise.all([
      apiFetch("/skills/").catch(() => null),
      apiFetch("/analytics/skills").catch(() => null),
    ]).then(([s, a]) => {
      // Endpoint returns {skills: [{name, count, projects}]}
      const list = s?.skills || (Array.isArray(s) ? s : []);
      setSkills(list);
      setAnalytics(a);
      setLoading(false);
      if (list.length === 0) {
        setError("No skills found. Upload projects and run AI Analysis to extract skills.");
      }
    });
  }, []);

  async function loadDetail(name) {
    if (selected === name) { setSelected(null); setDetail(null); return; }
    setSelected(name); setDetailLoading(true);
    try {
      const d = await apiFetch(`/skills/${encodeURIComponent(name)}`);
      setDetail(d);
    } catch { setDetail(null); }
    finally { setDetailLoading(false); }
  }

  // Skills already have {name, count, projects} shape
  const filtered = skills.filter(s => (s.name || "").toLowerCase().includes(filter.toLowerCase()));

  const topSkills = analytics?.insights?.top_skills || skills.slice(0, 12);
  const cooccurrence = analytics?.raw?.co_occurrence || [];
  const totalSkills = analytics?.insights ? skills.length : skills.length;
  const totalProjects = analytics?.insights
    ? new Set(skills.flatMap(s => (s.projects || []).map(p => p.project_id))).size
    : null;

  return (
    <div className="page-wrap">
      <h1 style={{ marginBottom: 8 }}>Skills</h1>
      <p className="text-muted" style={{ marginBottom: 24 }}>All skills detected across your projects</p>

      {error && skills.length === 0 && (
        <div className="alert info">{error}</div>
      )}

      <div className="skills-stats-row">
        <div className="card skills-stat">
          <div className="stat-val">{totalSkills}</div>
          <div className="stat-label">Total Skills</div>
        </div>
        <div className="card skills-stat">
          <div className="stat-val">{totalProjects ?? "—"}</div>
          <div className="stat-label">Projects</div>
        </div>
        <div className="card skills-stat">
          <div className="stat-val">{analytics?.insights?.skill_diversity?.toFixed(2) ?? "—"}</div>
          <div className="stat-label">Diversity Score</div>
        </div>
      </div>

      {topSkills.length > 0 && (
        <div className="card skills-top-section">
          <h2>Top Skills</h2>
          <div className="skills-top-chips">
            {topSkills.slice(0, 12).map((s, i) => {
              const name = s.name || s.skill || (typeof s === "string" ? s : "");
              return name ? (
                <span key={i} className="top-skill-chip" onClick={() => loadDetail(name)} style={{ cursor: "pointer" }}>
                  {name}
                </span>
              ) : null;
            })}
          </div>
        </div>
      )}

      <div className="skills-layout">
        <div className="skills-list-panel">
          <div style={{ marginBottom: 16 }}>
            <input placeholder="Filter skills…" value={filter} onChange={e => setFilter(e.target.value)} />
          </div>

          {loading
            ? <div className="spinner" />
            : filtered.length === 0
              ? <div className="empty-state">
                  <p>No skills found.</p>
                  <p style={{ fontSize: "0.82rem", marginTop: 8 }}>
                    Skills are extracted when scanning projects. Try uploading a code project or running AI Analysis from the Analysis page.
                  </p>
                </div>
              : <div className="skills-list">
                  {filtered.map((s, i) => {
                    const name = s.name || "";
                    const count = s.count ?? 0;
                    const isActive = selected === name;
                    return (
                      <div key={i} className={`skill-row ${isActive ? "active" : ""}`} onClick={() => loadDetail(name)}>
                        <span className="skill-name">{name.replace(/_/g, " ")}</span>
                        <span className="skill-count">{count} project{count !== 1 ? "s" : ""}</span>
                        <span className="skill-chevron">{isActive ? "▲" : "▼"}</span>
                      </div>
                    );
                  })}
                </div>
          }
        </div>

        <div className="skills-detail-panel">
          {!selected ? (
            <>
              {cooccurrence.length > 0 && (
                <div className="card">
                  <h2 style={{ marginBottom: 14 }}>Skill Co-occurrence</h2>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {cooccurrence.slice(0, 8).map((pair, i) => {
                      const a = pair.skill_1 || pair.skill_a || "";
                      const b = pair.skill_2 || pair.skill_b || "";
                      return (
                        <div key={i} className="cooc-row">
                          <span className="tag accent">{a}</span>
                          <span className="cooc-plus">+</span>
                          <span className="tag accent">{b}</span>
                          {pair.count != null && <span className="text-muted" style={{ fontSize: "0.75rem" }}>{pair.count}×</span>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {cooccurrence.length === 0 && !loading && (
                <div className="card" style={{ height: 120, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <p className="text-muted">Click a skill to see which projects use it</p>
                </div>
              )}
            </>
          ) : (
            <div className="card">
              <h2 style={{ marginBottom: 16 }}>{selected.replace(/_/g, " ")}</h2>
              {detailLoading
                ? <div className="spinner" />
                : !detail || detail.project_count === 0
                  ? <p className="text-muted">No projects found with this skill.</p>
                  : <>
                      <p className="text-muted" style={{ marginBottom: 12 }}>
                        Used in {detail.project_count} project{detail.project_count !== 1 ? "s" : ""}
                      </p>
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {(detail.projects || []).map(p => (
                          <div key={p.project_id || p.id} className="skill-project-row"
                            onClick={() => nav(`/projects/${p.project_id || p.id}`)}>
                            <span>{p.custom_description || p.project_name || projectName(p)}</span>
                            <span className="tag">{p.project_type || "?"}</span>
                          </div>
                        ))}
                      </div>
                    </>
              }
            </div>
          )}
        </div>
      </div>
    </div>
  );
}