import React, { useEffect, useState, useRef } from "react";
import { Joyride } from 'react-joyride';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Dashboard.css";

const TIPS = [
  "Add quantifiable metrics to your resume bullets — numbers stand out to recruiters.",
  "Tailor your resume keywords to each job description for a higher ATS score.",
  "A strong GitHub profile can be just as powerful as a degree.",
  "Your top 3 projects matter more than a long list of mediocre ones.",
  "Export your resume as both PDF and DOCX to maximize compatibility.",
  "Keep bullet points to 1–2 lines for maximum readability.",
  "Showcase side projects — they demonstrate passion and self-motivation.",
  "Update your portfolio regularly, even with small wins.",
  "Action verbs like 'built', 'led', 'reduced' score higher in ATS systems.",
  "Skills section tip: list Expert skills first — recruiters scan top-down.",
];

function useCountUp(target, duration = 900) {
  const [value, setValue] = useState(0);
  const frame = useRef(null);
  useEffect(() => {
    if (typeof target !== "number") return;
    const start = performance.now();
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) frame.current = requestAnimationFrame(step);
    }
    frame.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame.current);
  }, [target, duration]);
  return value;
}

function getStreak() {
  const today = new Date().toDateString();
  const last = localStorage.getItem("dash_last_visit");
  const streak = parseInt(localStorage.getItem("dash_streak") || "0", 10);
  if (last === today) return streak;
  const yesterday = new Date(Date.now() - 86400000).toDateString();
  const newStreak = last === yesterday ? streak + 1 : 1;
  localStorage.setItem("dash_streak", newStreak);
  localStorage.setItem("dash_last_visit", today);
  return newStreak;
}

export default function Dashboard() {
  // Only run walkthrough if not seen
  const [runWalkthrough, setRunWalkthrough] = useState(() => {
    return localStorage.getItem('dashboard_walkthrough_seen') !== '1';
  });
  // Set flag as soon as walkthrough starts
  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('dashboard_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);
  const walkthroughSteps = [
    {
      target: 'body',
      placement: 'center',
      title: 'Welcome to your Dashboard',
      content: 'This dashboard is your launch point for the rest of the app. Let’s take a quick tour!'
    },
    {
      target: '#upload-project-btn',
      placement: 'bottom',
      title: 'Upload Project',
      content: 'Click here to add new projects into the system.'
    },
    {
      target: '.stat-row',
      placement: 'bottom',
      title: 'Portfolio Snap Judgements',
      content: 'This row gives you quick stats and snap judgements about your portfolio.'
    },
    {
      target: '.dash-grid',
      placement: 'top',
      title: 'Top Projects, Skills, Portfolio',
      content: 'Here you’ll find your top projects, top skills, and portfolio generation tools.'
    },
    {
      target: '.dash-charts-row',
      placement: 'top',
      title: 'Charts & Insights',
      content: 'This section contains charts for your projects and skills.'
    },
    {
      target: '.navbar-projects, [href="/projects"]',
      placement: 'bottom',
      title: 'Next: Projects',
      content: 'Click on Projects in the navigation bar to view and manage your projects.'
    }
  ];
  const [projects, setProjects] = useState([]);
  const [skills, setSkills] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [resumeExists, setResumeExists] = useState(false);
  const [showEmojis, setShowEmojis] = useState(() => localStorage.getItem("dash_show_emojis") !== "false");
  const [showStreak, setShowStreak] = useState(() => localStorage.getItem("dash_show_streak") !== "false");
  const [showTip, setShowTip] = useState(() => localStorage.getItem("dash_show_tip") !== "false");
  useEffect(() => {
    const sync = () => {
      setShowEmojis(localStorage.getItem("dash_show_emojis") !== "false");
      setShowStreak(localStorage.getItem("dash_show_streak") !== "false");
      setShowTip(localStorage.getItem("dash_show_tip") !== "false");
    };
    window.addEventListener("dash-settings-updated", sync);
    return () => window.removeEventListener("dash-settings-updated", sync);
  }, []);
  useEffect(() => {
    const sync = () => setShowEmojis(localStorage.getItem("dash_show_emojis") !== "false");
    window.addEventListener("dash-emojis-updated", sync);
    return () => window.removeEventListener("dash-emojis-updated", sync);
  }, []);

  function toggleEmojis() {
    setShowEmojis(prev => {
      const next = !prev;
      localStorage.setItem("dash_show_emojis", String(next));
      window.dispatchEvent(new Event("dash-emojis-updated"));
      return next;
    });
  }

  const e = (emoji) => showEmojis ? emoji : null;
  useEffect(() => {
    const sync = () => setResumeExists(!!localStorage.getItem("resume_saved"));
    sync();
    window.addEventListener("resume-updated", sync);
    return () => window.removeEventListener("resume-updated", sync);
  }, []);
  const [loading, setLoading] = useState(true);
  const [checklistDismissed, setChecklistDismissed] = useState(() => localStorage.getItem("onboarding_dismissed") === "1");
  const [theme, setTheme] = useState(() => document.body.getAttribute("data-theme") || "dark");
  useEffect(() => {
    const obs = new MutationObserver(() => setTheme(document.body.getAttribute("data-theme") || "dark"));
    obs.observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
    return () => obs.disconnect();
  }, []);
  const isDark = theme === "dark";
  const chartLabelColor = isDark ? "#a5b4fc" : "#1a1d3a";
  const chartMutedColor = isDark ? "#6b7a99" : "#5a6080";
  const chartTooltipBg = isDark ? "#1a1f4a" : "#ffffff";
  const chartTooltipBorder = isDark ? "1px solid rgba(99,102,241,0.4)" : "1px solid rgba(99,102,241,0.3)";
  const chartTooltipColor = isDark ? "#e0e7ff" : "#1a1d3a";

  const nav = useNavigate();
  const streak = getStreak();
  const tip = TIPS[new Date().getDate() % TIPS.length];

  useEffect(() => {
    Promise.all([
      apiFetch("/projects").catch(() => []),
      apiFetch("/skills/").catch(() => null),
      apiFetch("/portfolio").catch(() => null),
    ]).then(([p, s, pf]) => {
      setProjects(Array.isArray(p) ? p : []);
      const skillList = s?.skills || (Array.isArray(s) ? s : []);
      setSkills(skillList.slice(0, 10));
      setPortfolio(pf);
      setLoading(false);
    });
  }, []);

  // All hooks must be called before any early returns
  const topProjects = [...projects]
    .sort((a, b) => (b.importance_score || 0) - (a.importance_score || 0))
    .slice(0, 5);

  const topScore = topProjects[0]?.importance_score != null ? Number(topProjects[0].importance_score) : null;
  const portfolioCount = portfolio?.projects?.length ?? null;

  const cProjects = useCountUp(loading ? 0 : projects.length);
  const cSkills = useCountUp(loading ? 0 : skills.length);
  const cScore = useCountUp(loading ? 0 : topScore ?? 0);
  const cPortfolio = useCountUp(loading ? 0 : portfolioCount ?? 0);

  if (loading) return (
    <div className="page-wrap">
      <div className="dash-header">
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-btn" />
      </div>
      <div className="stat-row">
        {[0,1,2,3].map(i => <div key={i} className="stat-card card skeleton-card"><div className="skeleton skeleton-val" /><div className="skeleton skeleton-label" /></div>)}
      </div>
      <div className="dash-grid">
        {[0,1,2].map(i => <div key={i} className="card skeleton-card"><div className="skeleton skeleton-h2" /><div className="skeleton skeleton-line" /><div className="skeleton skeleton-line short" /></div>)}
      </div>
    </div>
  );

  const onboardingSteps = [
    { id: "upload",    label: "Upload your first project",       icon: e("📁"), done: projects.length > 0,                                                            link: "/upload" },
    { id: "ai",        label: "Run AI Analysis on a project",    icon: e("🔬"), done: projects.some(p => p.ai_description || p.ats_score != null),                    link: "/analysis" },
    { id: "skills",    label: "Discover your skills",            icon: e("⚡"), done: skills.length > 0,                                                              link: "/skills" },
    { id: "portfolio", label: "Generate your portfolio",         icon: e("🎨"), done: (portfolio?.projects?.length || 0) > 0,                                         link: "/portfolio" },
    { id: "resume",    label: "Build your resume",               icon: e("📄"), done: resumeExists,                                                                  link: "/resumes" },
  ];
  const doneCnt = onboardingSteps.filter(s => s.done).length;
  const allOnboardingDone = doneCnt === onboardingSteps.length;

  function dismissChecklist() {
    localStorage.setItem("onboarding_dismissed", "1");
    setChecklistDismissed(true);
  }

  const stats = [
    { label: "Projects", icon: e("📁"), animated: cProjects, raw: projects.length },
    { label: "Skills", icon: e("⚡"), animated: cSkills, raw: skills.length },
    { label: "Top Score", icon: e("🏆"), animated: topScore !== null ? cScore.toFixed(0) : null, raw: topScore !== null ? topScore.toFixed(2) : "—" },
  ];

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
            localStorage.setItem('dashboard_walkthrough_seen', '1');
            setRunWalkthrough(false);
          }
        }}
      />
      <div className="page-wrap">
      <div className="dash-header">
        <h1 style={{ display: "flex", alignItems: "center", gap: 8 }}>
          Dashboard
          <button onClick={() => nav("/settings?section=dashboard")} title="Customize Dashboard" style={{ background: "none", border: "none", cursor: "pointer", padding: "4px", lineHeight: 1, color: "var(--accent)", opacity: 0.8, display: "flex", alignItems: "center" }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
        </h1>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button id="upload-project-btn" className="btn-primary" onClick={() => nav("/upload")}>+ Upload Project</button>
        </div>
      </div>

      <div className="stat-row">
        {stats.map(s => (
          <div key={s.label} className="stat-card card">
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-val">{s.animated !== null ? s.animated : s.raw}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {(showStreak || showTip) && (
        <div className="dash-meta-row">
          {showStreak && (
            <div className="dash-streak card">
              {e(<span className="dash-streak-fire">🔥</span>)}
              <div>
                <div className="dash-streak-num">{streak}-day streak</div>
                <div className="dash-streak-sub">Keep it up! Come back tomorrow.</div>
              </div>
            </div>
          )}
          {showTip && (
            <div className="dash-tip card">
              {e(<span className="dash-tip-icon">💡</span>)}
              <div>
                <div className="dash-tip-label">Tip of the day</div>
                <div className="dash-tip-text">{tip}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {!checklistDismissed && (
        <div className="dash-onboarding card">
          <div className="dash-onboarding-header">
            <div>
              <div className="dash-onboarding-title">{allOnboardingDone ? `${e("🎉 ")}You're all set!` : "Getting Started"}</div>
              <div className="dash-onboarding-sub">{doneCnt} of {onboardingSteps.length} complete</div>
            </div>
            <button className="dash-onboarding-dismiss" onClick={dismissChecklist} title="Dismiss">✕</button>
          </div>
          <div className="dash-onboarding-track">
            <div className="dash-onboarding-fill" style={{ width: `${doneCnt / onboardingSteps.length * 100}%` }} />
          </div>
          <div className="dash-onboarding-steps">
            {onboardingSteps.map(step => (
              <div key={step.id} className={`dash-onboarding-step ${step.done ? "done" : ""}`} onClick={() => !step.done && nav(step.link)}>
                <div className="dash-onboarding-check">{step.done ? "✓" : ""}</div>
                <span className="dash-onboarding-icon">{step.icon}</span>
                <span className="dash-onboarding-label">{step.label}</span>
                {!step.done && <span className="dash-onboarding-arrow">→</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dash-grid">
        <div className="card dash-hover-card" onClick={() => nav("/projects")}>
          <h2>Top Projects</h2>
          {topProjects.length === 0
            ? (
              <div className="dash-empty-state">
                {e(<div className="dash-empty-icon">📁</div>)}
                <p>No projects yet.</p>
                <a href="/upload" className="btn-primary" style={{ fontSize: "0.82rem", padding: "6px 16px" }}>Upload your first →</a>
              </div>
            )
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
          <button className="btn-primary mt-16" onClick={() => nav("/projects")}>View All →</button>
        </div>

        <div className="card dash-hover-card" onClick={() => nav("/skills")}>
          <h2>Top Skills</h2>
          {skills.length === 0
            ? (
              <div className="dash-empty-state">
                {e(<div className="dash-empty-icon">⚡</div>)}
                <p>No skills yet. Upload a project and run AI Analysis.</p>
              </div>
            )
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
          <button className="btn-primary mt-16" onClick={() => nav("/skills")}>All Skills →</button>
        </div>

        <div className="card dash-portfolio-card">
          <h2>Portfolio</h2>
          <p className="text-muted">
            {portfolio?.projects?.length
              ? `${portfolio.projects.length} project(s) in your portfolio`
              : "Generate your portfolio from your projects"}
          </p>
          <div className="dash-portfolio-modes">
            <button
              className="dash-mode-btn dash-mode-private"
              onClick={() => { localStorage.setItem("portfolio_mode", "private"); nav("/portfolio"); }}
              title="Edit and customize your portfolio"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              Private
            </button>
            <button
              className="dash-mode-btn dash-mode-public"
              onClick={() => { localStorage.setItem("portfolio_mode", "public"); nav("/portfolio"); }}
              title="View your public portfolio"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
              Public
            </button>
          </div>
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
              <ResponsiveContainer width="100%" height={260}>
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
                    outerRadius={95}
                    stroke="none"
                  >
                    {Object.keys(projects.reduce((acc, p) => {
                      const type = p.project_type || "Unknown";
                      acc[type] = true;
                      return acc;
                    }, {})).map((type, idx) => (
                      <Cell key={type} fill={["#6366f1","#818cf8","#a5b4fc","#7c3aed","#c4b5fd","#4f46e5","#ddd6fe"][idx % 7]} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{ background: chartTooltipBg, border: chartTooltipBorder, borderRadius: 8, color: chartTooltipColor, fontSize: '0.85rem' }}
                    itemStyle={{ color: chartLabelColor }}
                  />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ color: chartLabelColor, fontSize: '0.82rem', paddingTop: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Bar Chart: Top Skills */}
        <div className="card insights">
          <h2>Top Skills</h2>
          <div className="insights-chart-area">
            {skills.length === 0 ? (
              <p className="text-muted">No skills to display.</p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={skills.map(s => ({
                    name: s.name || s.skill_name || (typeof s === "string" ? s : ""),
                    count: s.count || s.project_count || 0
                  }))}
                  layout="vertical"
                  margin={{ left: 8, right: 24, top: 4, bottom: 4 }}
                >
                  <defs>
                    <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="100%" stopColor="#a78bfa" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" horizontal={false} />
                  <XAxis
                    type="number"
                    allowDecimals={false}
                    tick={{ fill: chartMutedColor, fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={150}
                    tick={{ fill: chartLabelColor, fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <RechartsTooltip
                    contentStyle={{ background: chartTooltipBg, border: chartTooltipBorder, borderRadius: 8, color: chartTooltipColor, fontSize: '0.85rem' }}
                    itemStyle={{ color: chartLabelColor }}
                    cursor={{ fill: 'rgba(99,102,241,0.08)' }}
                  />
                  <Bar dataKey="count" fill="url(#barGrad)" radius={[0, 6, 6, 0]} maxBarSize={18} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
    </>
  );
}