import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./ProjectPage.css";

const API_BASE = "http://127.0.0.1:8000";

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function ProjectPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [project, setProject] = useState(null);
  const [aiConsent, setAiConsent] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [analyzeSuccess, setAnalyzeSuccess] = useState("");

  useEffect(() => {
    loadProject();
    checkAiConsent();
  }, [projectId]);

  async function loadProject() {
    const token = localStorage.getItem("token");
    const response = await fetch(`${API_BASE}/projects/${projectId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const data = await response.json();
    setProject(data);
  }

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

  async function handleGenerateAiDescription() {
    setAnalyzing(true);
    setAnalyzeError("");
    setAnalyzeSuccess("");
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/projects/${projectId}/analyze`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setProject((prev) => ({
        ...prev,
        ai_description: data.ai_description,
      }));
      setAnalyzeSuccess("AI description generated.");
    } catch (e) {
      setAnalyzeError("Failed to generate: " + e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  if (!project) return <p className="project-loading">Loading project...</p>;

  // What description to show in the main block:
  // - If ai_description exists, always show it with the AI badge
  // - Otherwise fall back to the system description field
  const hasAiDesc = Boolean(project.ai_description);
  const systemDesc = project.description || null;

  return (
    <div className="project-page">
      <button className="back-button" onClick={() => navigate(-1)}>
        &larr; Back
      </button>

      <h1>{project.display_name || project.name || "Untitled Project"}</h1>

      <div className="project-meta-row">
        <span className="project-badge">{project.project_type}</span>
        {project.is_collaborative && (
          <span className="project-badge project-badge-collab">
            Collaborative
          </span>
        )}
      </div>

      {/* Description */}
      <div className="project-section">
        <h3>Description</h3>

        {hasAiDesc ? (
          <div className="ai-description">
            <span className="ai-badge">AI</span>
            <p>{project.ai_description}</p>
          </div>
        ) : systemDesc ? (
          <p>{systemDesc}</p>
        ) : (
          <p className="project-empty">No description available.</p>
        )}

        {/* AI generate button — only shown when consent is granted */}
        {aiConsent && (
          <div className="ai-actions">
            <button
              className="btn-ai"
              onClick={handleGenerateAiDescription}
              disabled={analyzing}
            >
              {analyzing
                ? "Generating..."
                : hasAiDesc
                ? "Regenerate AI Description"
                : "Generate AI Description"}
            </button>
            {analyzeSuccess && (
              <p className="ai-success">{analyzeSuccess}</p>
            )}
            {analyzeError && <p className="ai-error">{analyzeError}</p>}
          </div>
        )}

        {/* Hint shown only when no AI description exists and consent is off */}
        {!aiConsent && !hasAiDesc && (
          <p className="ai-hint">
            Enable AI consent in <a href="/settings">Settings</a> to generate
            an AI description.
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="project-section">
        <h3>Stats</h3>
        <ul className="project-stats">
          <li>
            <strong>Files:</strong> {project.file_count ?? "N/A"}
          </li>
          <li>
            <strong>Lines of Code:</strong> {project.lines_of_code ?? "N/A"}
          </li>
          <li>
            <strong>Word Count:</strong> {project.word_count ?? "N/A"}
          </li>
          <li>
            <strong>Total Size:</strong> {formatBytes(project.total_size_bytes)}
          </li>
          {project.date_scanned && (
            <li>
              <strong>Date Scanned:</strong>{" "}
              {new Date(project.date_scanned).toLocaleDateString()}
            </li>
          )}
        </ul>
      </div>

      {/* Skills */}
      {project.skills && project.skills.length > 0 && (
        <div className="project-section">
          <h3>Skills</h3>
          <div className="tag-list">
            {project.skills.map((skill, idx) => (
              <span key={idx} className="tag">
                {skill.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Languages */}
      {project.languages && project.languages.length > 0 && (
        <div className="project-section">
          <h3>Languages</h3>
          <div className="tag-list">
            {project.languages.map((lang, idx) => (
              <span key={idx} className="tag">
                {lang}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Frameworks */}
      {project.frameworks && project.frameworks.length > 0 && (
        <div className="project-section">
          <h3>Frameworks</h3>
          <div className="tag-list">
            {project.frameworks.map((fw, idx) => (
              <span key={idx} className="tag">
                {fw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tags */}
      {project.tags && project.tags.length > 0 && (
        <div className="project-section">
          <h3>Tags</h3>
          <div className="tag-list">
            {project.tags.map((tag, idx) => (
              <span key={idx} className="tag tag-secondary">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectPage;