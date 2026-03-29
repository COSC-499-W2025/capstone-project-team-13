import { Joyride } from 'react-joyride';
import React, { useEffect, useState } from "react";
import { apiFetch, projectName } from "../apiClient";
import "./Interview.css";

const ROLES = [
  "Software Engineer", "Frontend Engineer", "Backend Engineer",
  "Full Stack Engineer", "Data Scientist", "ML Engineer",
  "Product Manager", "UX Designer", "DevOps Engineer",
  "Research Assistant", "Creative Director", "Content Creator",
  "Data Analyst", "Game Developer", "Mobile Developer",
];

const THEME_ICONS = ["💡", "🏆", "🚀", "📚"];

export default function Interview() {
  // Only run walkthrough if not seen
  const [runWalkthrough, setRunWalkthrough] = useState(() => {
    return localStorage.getItem('interview_walkthrough_seen') !== '1';
  });
  // Set flag as soon as walkthrough starts
  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('interview_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);
  const walkthroughSteps = [
    {
      target: 'body',
      placement: 'center',
      title: 'Interview Prep',
      content: 'This page helps you generate STAR-format interview answers from your real projects. Let’s take a quick tour!'
    },
    {
      target: '.iv-hero',
      placement: 'bottom',
      title: 'Hero Section',
      content: 'See what this tool does and how it can help you prepare for interviews.'
    },
    {
      target: '.iv-role-pills',
      placement: 'bottom',
      title: 'Target Role',
      content: 'Select a target role or type your own to tailor your answers.'
    },
    {
      target: '.iv-project-list',
      placement: 'bottom',
      title: 'Projects to Include',
      content: 'Choose which projects to use for generating your interview answers.'
    },
    {
      target: '.iv-generate-btn',
      placement: 'top',
      title: 'Generate Answers',
      content: 'Click here to generate personalized STAR-format answers for your selected role and projects.'
    }
  ];
  const [projects, setProjects]     = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [role, setRole]             = useState("Software Engineer");
  const [customRole, setCustomRole] = useState("");
  const [answers, setAnswers]       = useState([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
  const [openIdx, setOpenIdx]       = useState(null);
  const [copied, setCopied]         = useState(null);
  const [authed, setAuthed]         = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setAuthed(false); return; }
    fetch("http://127.0.0.1:8000/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (r.ok) setAuthed(true); else setAuthed(false); })
      .catch(() => setAuthed(false));
  }, []);

  useEffect(() => {
    if (authed !== true) return;
    apiFetch("/projects").then(p => {
      const list = Array.isArray(p) ? p : [];
      setProjects(list);
      setSelectedIds(list.map(pr => pr.id));
    }).catch(() => {});
  }, [authed]);

  async function generate() {
    setLoading(true);
    setError(null);
    setAnswers([]);
    setOpenIdx(null);
    try {
      const targetRole = customRole.trim() || role;
      const data = await apiFetch("/interview/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_role: targetRole, project_ids: selectedIds }),
      });
      setAnswers(data.answers || []);
      if (data.answers?.length) setOpenIdx(0);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleProject(id) {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  }

  function copyAnswer(a, idx) {
    const text = `Q: ${a.question}\n\nSituation: ${a.situation}\n\nTask: ${a.task}\n\nAction: ${a.action}\n\nResult: ${a.result}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(idx);
      setTimeout(() => setCopied(null), 2000);
    });
  }

  function pName(p) { return projectName(p); }

  if (authed === null) return <div className="page-wrap" style={{ paddingTop: 80, textAlign: "center", color: "#818cf8" }}>Loading…</div>;

  if (authed === false) return (
    <div className="page-wrap">
      <div className="resume-auth-wall card">
        <div className="resume-auth-icon">🎤</div>
        <h2>Interview Prep</h2>
        <p className="text-muted">Sign in to generate personalized STAR interview answers from your projects.</p>
        <a className="btn-primary" href="/settings">Sign In / Sign Up →</a>
      </div>
    </div>
  );

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
            localStorage.setItem('interview_walkthrough_seen', '1');
            setRunWalkthrough(false);
          }
        }}
      />
      <div className="page-wrap">

      {/* Hero */}
      <div className="iv-hero card">
        <div>
          <h1 className="iv-hero-title">🎤 Interview Prep</h1>
          <p className="iv-hero-sub">Generate personalized STAR-format answers from your real projects.</p>
        </div>
      </div>

      {/* Config panel */}
      <div className="iv-config card">
        <div className="iv-config-row">
          <div className="iv-config-block">
            <label className="iv-label">Target role</label>
            <div className="iv-role-pills">
              {ROLES.map(r => (
                <button key={r}
                  className={`iv-role-pill ${role === r && !customRole ? "active" : ""}`}
                  onClick={() => { setRole(r); setCustomRole(""); }}>
                  {r}
                </button>
              ))}
            </div>
            <input
              className="iv-custom-role"
              placeholder="Or type a custom role…"
              value={customRole}
              onChange={e => setCustomRole(e.target.value)}
            />
          </div>

          <div className="iv-config-block">
            <label className="iv-label">
              Projects to include
              <span className="iv-label-count">{selectedIds.length} / {projects.length}</span>
            </label>
            <div className="iv-project-list">
              {projects.map(p => (
                <label key={p.id} className={`iv-proj-check ${selectedIds.includes(p.id) ? "selected" : ""}`}>
                  <input type="checkbox" checked={selectedIds.includes(p.id)} onChange={() => toggleProject(p.id)} />
                  <span className="iv-proj-name">{pName(p)}</span>
                  <span className="iv-proj-type tag">{p.project_type || "general"}</span>
                </label>
              ))}
            </div>
            <div className="iv-proj-shortcuts">
              <button className="iv-shortcut" onClick={() => setSelectedIds(projects.map(p => p.id))}>Select all</button>
              <button className="iv-shortcut" onClick={() => setSelectedIds([])}>Clear</button>
            </div>
          </div>
        </div>

        <button className="btn-primary iv-generate-btn" onClick={generate} disabled={loading || selectedIds.length === 0}>
          {loading ? "Generating answers…" : "✨ Generate STAR Answers"}
        </button>
      </div>

      {error && <div className="alert error">{error}</div>}

      {loading && (
        <div className="iv-loading card">
          <div className="iv-loading-icon">🤔</div>
          <p>Crafting personalized answers from your projects…</p>
          <p className="text-muted" style={{ fontSize: "0.82rem" }}>This takes about 15–20 seconds</p>
        </div>
      )}

      {/* Answers */}
      {answers.length > 0 && (
        <div className="iv-answers">
          <div className="iv-answers-header">
            <h2>Your Interview Answers</h2>
            <span className="text-muted" style={{ fontSize: "0.85rem" }}>{answers.length} questions · {customRole || role}</span>
          </div>

          {answers.map((a, i) => (
            <div key={i} className={`iv-answer-card card ${openIdx === i ? "open" : ""}`}>
              <button className="iv-answer-toggle" onClick={() => setOpenIdx(openIdx === i ? null : i)}>
                <span className="iv-answer-icon">{THEME_ICONS[i] || "💬"}</span>
                <span className="iv-answer-q">{a.question}</span>
                <span className="iv-answer-proj tag accent">{a.project_name}</span>
                <span className="iv-chevron">{openIdx === i ? "▲" : "▼"}</span>
              </button>

              {openIdx === i && (
                <div className="iv-answer-body">
                  <div className="iv-star-grid">
                    {[
                      { key: "situation", label: "S  Situation", color: "#6366f1" },
                      { key: "task",      label: "T  Task",      color: "#8b5cf6" },
                      { key: "action",    label: "A  Action",    color: "#a78bfa" },
                      { key: "result",    label: "R  Result",    color: "#34d399" },
                    ].map(({ key, label, color }) => (
                      <div key={key} className="iv-star-block" style={{ borderLeftColor: color }}>
                        <div className="iv-star-label" style={{ color }}>{label}</div>
                        <p className="iv-star-text">{a[key]}</p>
                      </div>
                    ))}
                  </div>
                  <div className="iv-answer-actions">
                    <button className="btn-secondary" onClick={() => copyAnswer(a, i)}>
                      {copied === i ? "✓ Copied!" : "Copy answer"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>   
  </>);
}
