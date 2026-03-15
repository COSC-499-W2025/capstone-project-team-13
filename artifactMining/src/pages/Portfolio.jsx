import React, { useEffect, useState } from "react";
import "./Portfolio.css";

const API_BASE = "http://127.0.0.1:8000";

function Portfolio() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notLoggedIn, setNotLoggedIn] = useState(false);
  const [aiConsent, setAiConsent] = useState(false);
  const [generatingAi, setGeneratingAi] = useState(false);
  const [aiMessage, setAiMessage] = useState("");

  useEffect(() => {
    checkAiConsent();
    loadPortfolio();
  }, []);

  async function checkAiConsent() {
    try {
      const res = await fetch(`${API_BASE}/consent/ai-consent-status`);
      const data = await res.json();
      const granted =
        data.granted ?? data.ai_consent_granted ?? data.status ?? false;
      setAiConsent(Boolean(granted));
    } catch {
      setAiConsent(false);
    }
  }

  async function loadPortfolio() {
    setLoading(true);
    setError(null);
    setNotLoggedIn(false);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/portfolio/generate`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.status === 401) {
        setNotLoggedIn(true);
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProjects((data.projects || []).slice(0, 3));
    } catch (e) {
      setError("Failed to load portfolio. " + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateAiDescriptions() {
    if (!aiConsent) return;
    setGeneratingAi(true);
    setAiMessage("");
    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const updated = await Promise.all(
        projects.map(async (p) => {
          try {
            const res = await fetch(`${API_BASE}/projects/${p.id}/analyze`, {
              method: "POST",
              headers,
            });
            if (!res.ok) return p;
            const data = await res.json();
            return { ...p, ai_description: data.ai_description };
          } catch {
            return p;
          }
        })
      );
      setProjects(updated);
      setAiMessage("AI descriptions generated.");
    } catch (e) {
      setAiMessage("Failed to generate AI descriptions: " + e.message);
    } finally {
      setGeneratingAi(false);
    }
  }

  if (loading) {
    return <div className="portfolio-loading">Loading portfolio...</div>;
  }

  if (notLoggedIn) {
    return (
      <div className="portfolio-auth-required">
        <h2>Sign in to view your portfolio</h2>
        <p>Your portfolio is tied to your account. Please log in to continue.</p>
        <a className="btn-portfolio-primary" href="/settings">
          Go to Settings to log in
        </a>
      </div>
    );
  }

  if (error) {
    return (
      <div className="portfolio-error">
        <p>{error}</p>
        <button className="btn-portfolio-primary" onClick={loadPortfolio}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="portfolio-page">
      <div className="portfolio-header">
        <h1>My Portfolio</h1>
        <p className="portfolio-subtitle">Top projects showcased for your portfolio</p>

        <div className="portfolio-actions">
          <button className="btn-portfolio-primary" onClick={loadPortfolio}>
            Refresh Portfolio
          </button>

          {aiConsent && (
            <button
              className="btn-portfolio-ai"
              onClick={handleGenerateAiDescriptions}
              disabled={generatingAi || projects.length === 0}
            >
              {generatingAi ? "Generating..." : "Generate AI Descriptions"}
            </button>
          )}

          {!aiConsent && (
            <p className="ai-hint">
              Enable AI consent in <a href="/settings">Settings</a> to add
              AI-generated descriptions.
            </p>
          )}
        </div>

        {aiMessage && <p className="portfolio-ai-message">{aiMessage}</p>}
      </div>

      {projects.length === 0 ? (
        <p className="portfolio-empty">
          No projects found. Upload a project to get started.
        </p>
      ) : (
        <div className="portfolio-grid">
          {projects.map((project) => (
            <PortfolioCard
              key={project.id}
              project={project}
              aiConsent={aiConsent}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PortfolioCard({ project, aiConsent }) {
  // Determine what description to show:
  // 1. AI description (if present) — shown with badge
  // 2. custom_description from portfolio edit
  // 3. regular description
  // 4. Nothing — prompt depends on consent
  const hasAiDesc = Boolean(project.ai_description);
  const fallbackDesc =
    project.custom_description || project.description || null;

  return (
    <div className="portfolio-card">
      {project.thumbnail_path ? (
        <img
          className="portfolio-card-thumbnail"
          src={`${API_BASE}/${project.thumbnail_path}`}
          alt={project.display_name || project.name}
        />
      ) : (
        <div className="portfolio-card-placeholder">
          {(project.display_name || project.name || "P")[0].toUpperCase()}
        </div>
      )}

      <div className="portfolio-card-body">
        <h2 className="portfolio-card-title">
          {project.display_name || project.name}
        </h2>

        <div className="portfolio-card-tags">
          {project.project_type && (
            <span className="portfolio-tag">{project.project_type}</span>
          )}
          {(project.languages || []).slice(0, 2).map((lang, i) => (
            <span key={i} className="portfolio-tag portfolio-tag-lang">
              {lang}
            </span>
          ))}
        </div>

        {hasAiDesc ? (
          <div className="portfolio-ai-desc">
            <span className="ai-badge">AI</span>
            <p>{project.ai_description}</p>
          </div>
        ) : fallbackDesc ? (
          <p className="portfolio-card-desc">{fallbackDesc}</p>
        ) : (
          <p className="portfolio-card-desc portfolio-card-empty">
            {aiConsent
              ? "Click \"Generate AI Descriptions\" to add a description."
              : "No description yet."}
          </p>
        )}

        <div className="portfolio-card-stats">
          {project.file_count != null && (
            <span>{project.file_count} files</span>
          )}
          {project.lines_of_code != null && (
            <span>{project.lines_of_code.toLocaleString()} lines</span>
          )}
        </div>

        <a className="portfolio-card-link" href={`/projects/${project.id}`}>
          View Details &rarr;
        </a>
      </div>
    </div>
  );
}

export default Portfolio;