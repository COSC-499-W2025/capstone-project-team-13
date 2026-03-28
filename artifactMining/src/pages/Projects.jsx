import React, { useEffect, useState } from "react";
import { Joyride } from 'react-joyride';
import { useNavigate, useLocation } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Projects.css";

export default function Projects() {
  // Only run walkthrough if not seen
  const [runWalkthrough, setRunWalkthrough] = useState(() => {
    return localStorage.getItem('projects_walkthrough_seen') !== '1';
  });
  // Set flag as soon as walkthrough starts
  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('projects_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);
  const walkthroughSteps = [
    {
      target: 'body',
      placement: 'center',
      title: 'Projects Overview',
      content: 'This page lets you view, filter, and manage all your uploaded projects. Let’s take a quick tour!'
    },
    {
      target: '.proj-grid, .empty-state',
      placement: 'top',
      title: 'Your Projects',
      content: 'Here you can find all of your uploaded projects. When populated, you will be able to see a project\'s stats.'
    },
    {
      target: '.btn-primary',
      placement: 'bottom',
      title: 'Upload a Project',
      content: 'Like on the dashboard, you can also upload projects through here.'
    },
    {
      target: '.deletion-tab',
      placement: 'bottom',
      title: 'Deletion Manager & Insights',
      content: 'Here is a deletion manager for your project as well as generated insights.'
    }
  ];

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const nav = useNavigate();
  const { pathname } = useLocation();

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
    <>
      <Joyride
        steps={walkthroughSteps}
        run={runWalkthrough}
        continuous
        showSkipButton
        showProgress
        styles={{
          options: {
            zIndex: 10000,
            primaryColor: 'var(--accent, #6366f1)',
            backgroundColor: 'var(--card-bg, #181a2a)',
            textColor: 'var(--text, #e0e7ff)',
            arrowColor: 'var(--card-bg, #181a2a)',
            overlayColor: 'rgba(30, 34, 54, 0.7)',
            spotlightShadow: '0 0 0 2px var(--accent, #6366f1), 0 1px 8px 0 rgba(99,102,241,0.10)',
            spotlightPadding: 0,
          },
          tooltipContainer: {
            borderRadius: 10,
            boxShadow: '0 2px 12px 0 rgba(30,34,54,0.13)',
            padding: '8px 14px',
            fontSize: '0.97rem',
            minWidth: 200,
            maxWidth: 300,
          },
          tooltip: {
            margin: 0,
          },
          buttonNext: {
            background: 'var(--accent, #6366f1)',
            color: '#fff',
            borderRadius: 7,
            fontWeight: 600,
            boxShadow: '0 1px 4px 0 rgba(99,102,241,0.08)',
            padding: '6px 18px',
            fontSize: '0.98rem',
          },
          buttonBack: {
            color: 'var(--accent, #6366f1)',
            background: 'transparent',
            fontWeight: 500,
            fontSize: '0.98rem',
          },
          buttonSkip: {
            color: 'var(--text-muted, #a5b4fc)',
            background: 'transparent',
            fontSize: '0.98rem',
          },
          dot: {
            background: 'var(--accent, #6366f1)',
          },
          badge: {
            background: 'var(--accent, #6366f1)',
            color: '#fff',
          },
          close: {
            color: 'var(--text-muted, #a5b4fc)',
            top: 10,
            right: 10,
          },
        }}
        disableScrolling={true}
        callback={(data) => {
          if (data.status === 'finished' || data.status === 'skipped') {
            localStorage.setItem('projects_walkthrough_seen', '1');
            setRunWalkthrough(false);
          }
        }}
      />
      <div className="page-wrap">
      <div className="proj-header">
        <h1>Projects</h1>
        <button className="btn-primary" onClick={() => nav("/upload")}>+ Upload</button>
      </div>

      {/* Sub Tabs */}
      <div className="proj-subtabs">
        <button
          className={`subtab-btn ${pathname === "/projects" ? "active" : ""}`}
          onClick={() => nav("/projects")}
        >
          All Projects
        </button>

        <button
          className={`subtab-btn deletion-tab ${pathname === "/deletion" ? "active" : ""}`}
          onClick={() => nav("/deletion")}
        >
          Deletion Manager
        </button>
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
    </>
  );
}