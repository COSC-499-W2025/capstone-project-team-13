import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Dashboard.css";

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [skills, setSkills] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  useEffect(() => {
    Promise.all([
      apiFetch("/projects").catch(() => []),
      apiFetch("/skills/").catch(() => null),
      apiFetch("/portfolio").catch(() => null),
    ]).then(([p, s, pf]) => {
      setProjects(Array.isArray(p) ? p : []);
      // Skills endpoint returns {skills: [{name, count, projects}]}
      const skillList = s?.skills || (Array.isArray(s) ? s : []);
      setSkills(skillList.slice(0, 10));
      setPortfolio(pf);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="page-wrap"><div className="spinner" /></div>;

  const topProjects = [...projects]
    .sort((a, b) => (b.importance_score || 0) - (a.importance_score || 0))
    .slice(0, 5);

  const stats = [
    { label: "Projects", value: projects.length },
    { label: "Skills", value: skills.length },
    { label: "Top Score", value: topProjects[0]?.importance_score != null ? Number(topProjects[0].importance_score).toFixed(2) : "—" },
    { label: "Portfolio", value: portfolio?.projects?.length ?? "—" },
  ];

  return (
    <div className="page-wrap">
      <div className="dash-header">
        <h1>Dashboard</h1>
        <button className="btn-primary" onClick={() => nav("/upload")}>+ Upload Project</button>
      </div>

      <div className="stat-row">
        {stats.map(s => (
          <div key={s.label} className="stat-card card">
            <div className="stat-val">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="dash-grid">
        <div className="card">
          <h2>Top Projects</h2>
          {topProjects.length === 0
            ? <p className="text-muted mt-12">No projects yet. <a href="/upload">Upload one.</a></p>
            : topProjects.map(p => (
              <div key={p.id} className="dash-project-row" onClick={() => nav(`/projects/${p.id}`)}>
                <div className="dash-project-info">
                  <strong>{projectName(p)}</strong>
                  <span className="text-muted">{p.project_type || "unknown"}</span>
                </div>
                <span className="tag accent">{p.importance_score != null ? Number(p.importance_score).toFixed(1) : "—"}</span>
              </div>
            ))
          }
          <button className="btn-secondary mt-16" onClick={() => nav("/projects")}>View All →</button>
        </div>

        <div className="card">
          <h2>Top Skills</h2>
          {skills.length === 0
            ? <p className="text-muted" style={{ marginTop: 12 }}>
                No skills detected yet. Upload a project and run AI Analysis to extract skills.
              </p>
            : <div className="skill-chip-grid">
                {skills.map((s, i) => {
                  const name = s.name || s.skill_name || (typeof s === "string" ? s : "");
                  const count = s.count || s.project_count || null;
                  return (
                    <span key={i} className="tag accent" style={{ cursor: "pointer" }}
                      onClick={() => nav("/skills")}
                      title={count ? `${count} project${count !== 1 ? "s" : ""}` : ""}>
                      {name}
                    </span>
                  );
                })}
              </div>
          }
          <button className="btn-secondary mt-16" onClick={() => nav("/skills")}>All Skills →</button>
        </div>

        <div className="card dash-portfolio-card" onClick={() => nav("/portfolio")}>
          <h2>Portfolio</h2>
          <p className="text-muted">
            {portfolio?.projects?.length
              ? `${portfolio.projects.length} project(s) in your portfolio`
              : "Generate your portfolio from your projects"}
          </p>
          <button className="btn-primary mt-16">Open Portfolio →</button>
        </div>
      </div>
    </div>
  );
}