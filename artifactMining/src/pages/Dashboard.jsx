import React, { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
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

      {/* Charts Row */}
      <div className="dash-charts-row" style={{ marginTop: 32 }}>
        {/* Pie Chart: Projects by Type */}
        <div className="card insights">
          <h2>Projects by Type</h2>
          <div className="insights-chart-area">
            {projects.length === 0 ? (
              <p className="text-muted">No projects to display.</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={Object.entries(projects.reduce((acc, p) => {
                      const type = p.project_type || "Unknown";
                      acc[type] = (acc[type] || 0) + 1;
                      return acc;
                    }, {})).map(([type, value]) => ({ name: type, value }))}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                    stroke="none"
                  >
                    {Object.keys(projects.reduce((acc, p) => {
                      const type = p.project_type || "Unknown";
                      acc[type] = true;
                      return acc;
                    }, {})).map((type, idx) => (
                      <Cell key={type} fill={["#6366f1", "#818cf8", "#a5b4fc", "#7c3aed", "#c4b5fd", "#64748b", "#475569"][idx % 7]} />
                    ))}
                  </Pie>
                  <RechartsTooltip contentStyle={{background:'#23295a', border:'1px solid #6366f1', color:'#e0e7ff'}}/>
                  <Legend wrapperStyle={{color:'#a5b4fc'}} iconType="circle"/>
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Bar Chart: Top 10 Skills */}
        <div className="card insights">
          <h2>Top 10 Skills</h2>
          <div className="insights-chart-area">
            {skills.length === 0 ? (
              <p className="text-muted">No skills to display.</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart
                  data={skills.map(s => ({
                    name: s.name || s.skill_name || (typeof s === "string" ? s : ""),
                    count: s.count || s.project_count || 0
                  }))}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#23295a" />
                  <XAxis type="number" allowDecimals={false} stroke="#6366f1" tick={{fill:'#a5b4fc'}} axisLine={{stroke:'#23295a'}} tickLine={{stroke:'#23295a'}}/>
                  <YAxis type="category" dataKey="name" width={120} stroke="#6366f1" tick={{fill:'#a5b4fc'}} axisLine={{stroke:'#23295a'}} tickLine={{stroke:'#23295a'}}/>
                  <RechartsTooltip contentStyle={{background:'#23295a', border:'1px solid #6366f1', color:'#e0e7ff'}}/>
                  <Legend wrapperStyle={{color:'#a5b4fc'}} iconType="circle"/>
                  <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 6, 6]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}