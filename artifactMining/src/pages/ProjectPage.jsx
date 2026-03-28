import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./ProjectPage.css";

const BASE = "http://127.0.0.1:8000";

export default function ProjectPage() {
  const { projectId } = useParams();
  const nav = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [msg, setMsg] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null); // live result from this session
  const [aiType, setAiType] = useState("overview");
  const [deleting, setDeleting] = useState(false);
  const [thumbFile, setThumbFile] = useState(null);

  // Contributor stats state
  const [githubUsername, setGithubUsername] = useState(null);
  const [contributors, setContributors] = useState(null);
  const [contribLoading, setContribLoading] = useState(true);
  const [contribError, setContribError] = useState(null);
  const [userContrib, setUserContrib] = useState(null);
  const [aiConsentGranted, setAiConsentGranted] = useState(false);
  // Load user's GitHub username and contributors for this project
  useEffect(() => {
    async function fetchContribData(allowAutoExtract = true) {
      setContribLoading(true);
      setContribError(null);
      setUserContrib(null);
      try {
        // Get user's GitHub username
        const userResp = await apiFetch("/user/github-username");
        const username = userResp.github_username;
        setGithubUsername(username);
        // Get contributors for this project
        let contribResp = await apiFetch(`/projects/${projectId}/contributors`);
        // If no contributors and allowed, trigger extraction and retry
        if (Array.isArray(contribResp) && contribResp.length === 0 && allowAutoExtract) {
          try {
            await apiFetch(`/contributors/populate/project?project_id=${projectId}`, { method: "POST" });
            // Wait briefly to allow backend to populate
            await new Promise(res => setTimeout(res, 1200));
            contribResp = await apiFetch(`/projects/${projectId}/contributors`);
          } catch (extractErr) {
            // Extraction failed, show error
            setContribError("No contributors found and extraction failed.");
            setContribLoading(false);
            return;
          }
        }
        setContributors(contribResp);
        // Try to find user in contributors (by GitHub username or email)
        let found = null;
        if (username && Array.isArray(contribResp)) {
          found = contribResp.find(c => {
            // Try to match by GitHub username (case-insensitive)
            if (c.email && c.email.includes("noreply.github.com")) {
              const match = c.email.match(/\d+\+([^@]+)@users\.noreply\.github\.com/);
              if (match && match[1].toLowerCase() === username.toLowerCase()) return true;
            }
            // Optionally, match by name (if user has set it)
            if (c.name && c.name.toLowerCase() === username.toLowerCase()) return true;
            return false;
          });
        }
        setUserContrib(found || null);
      } catch (e) {
        setContribError(e.message || "Failed to load contributor data");
      } finally {
        setContribLoading(false);
      }
    }
    fetchContribData();
  }, [projectId]);

  // Evidence state
  const [evidenceTab, setEvidenceTab] = useState("view");
  const [evidence, setEvidence] = useState(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [metricForm, setMetricForm] = useState({ name: "", value: "", description: "" });
  const [feedbackForm, setFeedbackForm] = useState({ text: "", source: "", rating: "" });
  const [achieveForm, setAchieveForm] = useState({ description: "", date: "" });

  useEffect(() => { load(); loadConsent(); loadEvidence(); }, [projectId]);

  async function loadConsent() {
    try {
      const config = await apiFetch("/configuration/current-configuration");
      setAiConsentGranted(!!(config.consent.ai_consent_granted && config.ai_settings.ai_enabled));
    } catch {
      setAiConsentGranted(false);
    }
  }

  async function loadEvidence() {
    setEvidenceLoading(true);
    try {
      const d = await apiFetch(`/evidence/${projectId}`);
      setEvidence(d);
    } catch { setEvidence({}); }
    finally { setEvidenceLoading(false); }
  }

  async function autoExtractEvidence() {
    setEvidenceLoading(true); setMsg(null);
    try {
      await apiFetch(`/evidence/${projectId}/extract`, { method: "POST" });
      setMsg({ type: "success", text: "Evidence extracted!" });
      loadEvidence();
    } catch (e) { setMsg({ type: "error", text: e.message }); setEvidenceLoading(false); }
  }

  async function addMetric() {
    if (!metricForm.name || !metricForm.value) { setMsg({ type: "error", text: "Name and value required." }); return; }
    try {
      await apiFetch(`/evidence/${projectId}/metric`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metric_name: metricForm.name, value: metricForm.value, description: metricForm.description }),
      });
      setMsg({ type: "success", text: "Metric added!" });
      setMetricForm({ name: "", value: "", description: "" });
      loadEvidence();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function addFeedback() {
    if (!feedbackForm.text) { setMsg({ type: "error", text: "Feedback text required." }); return; }
    try {
      await apiFetch(`/evidence/${projectId}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: feedbackForm.text, source: feedbackForm.source, rating: feedbackForm.rating ? Number(feedbackForm.rating) : null }),
      });
      setMsg({ type: "success", text: "Feedback added!" });
      setFeedbackForm({ text: "", source: "", rating: "" });
      loadEvidence();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function addAchievement() {
    if (!achieveForm.description) { setMsg({ type: "error", text: "Description required." }); return; }
    try {
      await apiFetch(`/evidence/${projectId}/achievement`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: achieveForm.description, date: achieveForm.date || null }),
      });
      setMsg({ type: "success", text: "Achievement added!" });
      setAchieveForm({ description: "", date: "" });
      loadEvidence();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function clearEvidence() {
    if (!window.confirm("Clear all evidence for this project?")) return;
    try {
      await apiFetch(`/evidence/${projectId}`, { method: "DELETE" });
      setMsg({ type: "success", text: "Evidence cleared." });
      loadEvidence();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function load() {
    try {
      const d = await apiFetch(`/projects/${projectId}`);
      setProject(d);
      setForm({
        custom_description: d.custom_description || "",
        user_role: d.user_role || "",
        success_evidence: d.success_evidence || "",
        is_featured: d.is_featured || false,
        is_hidden: d.is_hidden || false,
        importance_score: d.importance_score ?? "",
      });
      // If project already has stored analysis, show it
      if (d.ai_analysis && !analysisResult) {
        setAnalysisResult(d.ai_analysis);
      }
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function saveEdit() {
    try {
      await apiFetch(`/portfolio/${projectId}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setMsg({ type: "success", text: "Saved!" });
      setEditing(false);
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function analyze() {
    if (!aiConsentGranted) {
      setMsg({ type: "error", text: "AI analysis is disabled. Please enable AI features in Settings." });
      return;
    }
    setAnalyzing(true);
    setMsg(null);
    setAnalysisResult(null);
    try {
      const d = await apiFetch(`/projects/${projectId}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_type: aiType }),
      });
      const results = d.results || d;
      setAnalysisResult(results);
      setMsg({ type: "success", text: "Analysis complete — results saved to this project." });
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setAnalyzing(false); }
  }

  async function deleteProject() {
    if (!window.confirm("Delete this project? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await apiFetch(`/projects/${projectId}`, { method: "DELETE" });
      nav("/projects");
    } catch (e) { setMsg({ type: "error", text: e.message }); setDeleting(false); }
  }

  async function uploadThumbnail() {
    if (!thumbFile) return;
    const fd = new FormData();
    fd.append("file", thumbFile);
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`${BASE}/projects/${projectId}/thumbnail`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setMsg({ type: "success", text: "Thumbnail updated!" });
      setThumbFile(null);
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function removeThumbnail() {
    if (!window.confirm("Remove thumbnail?")) return;
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`${BASE}/projects/${projectId}/thumbnail`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setMsg({ type: "success", text: "Thumbnail removed." });
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  function fmtBytes(b) {
    if (!b) return "—";
    const k = 1024, sz = ["B","KB","MB","GB"], i = Math.floor(Math.log(b)/Math.log(k));
    return (b/Math.pow(k,i)).toFixed(1) + " " + sz[i];
  }

  // Build thumbnail URL from stored filename or path
  function thumbUrl(path) {
    if (!path) return null;
    // If it already looks like a URL, use as-is
    if (path.startsWith("http")) return path;
    // Extract just the filename from any stored path
    const filename = path.split(/[/\\]/).pop();
    return `${BASE}/uploads/${filename}`;
  }

  // Render AI analysis results cleanly — no raw JSON, no meta-word cards
  function renderAnalysis(r) {
    if (!r) return null;
    const cards = [];

    // Overview — plain string
    if (r.overview) {
      const text = typeof r.overview === "string" ? r.overview
        : r.overview.summary || r.overview.description || "";
      if (text.trim()) cards.push(
        <div key="ov" className="ai-result-block">
          <h4 className="ai-result-title">📝 Overview</h4>
          <p className="ai-result-text">{text.trim()}</p>
        </div>
      );
    }

    // Technical depth — raw_analysis string or dict of string values
    if (r.technical_depth) {
      const td = r.technical_depth;
      const rawText = typeof td === "string" ? td : (td.raw_analysis || "");
      const extras = typeof td === "object"
        ? Object.entries(td).filter(([k, v]) => k !== "raw_analysis" && typeof v === "string" && v.trim())
        : [];
      if (rawText.trim() || extras.length > 0) {
        cards.push(
          <div key="td" className="ai-result-block">
            <h4 className="ai-result-title">🔬 Technical Depth</h4>
            {rawText.trim() && <p className="ai-result-text">{rawText.trim()}</p>}
            {extras.length > 0 && (
              <ul className="ai-result-list">
                {extras.map(([k, v]) => (
                  <li key={k}><strong>{k.replace(/_/g, " ")}:</strong> {v}</li>
                ))}
              </ul>
            )}
          </div>
        );
      }
    }

    // Skills — handle both plain strings and {skill, justification} objects
    if (r.skills && r.skills.length > 0) {
      const JUNK = new Set([
        "skill name", "skill", "justification", "n/a", "none", "—", "",
        "strong", "moderate", "weak", "demonstrated", "evidence", "level",
      ]);
      const items = [];
      const seen = new Set();
      for (const s of r.skills) {
        const name = (typeof s === "string" ? s : (s.skill || s.name || ""))
          .replace(/\*+/g, "").replace(/^skill name:?\s*/i, "").trim();
        const justification = typeof s === "object"
          ? (s.justification || s.evidence || "").replace(/^justification:?\s*/i, "").trim()
          : "";
        const lower = name.toLowerCase();
        if (!name || JUNK.has(lower) || seen.has(lower) || name.split(" ").length > 8) continue;
        seen.add(lower);
        items.push({ name, justification });
      }
      if (items.length > 0) {
        cards.push(
          <div key="sk" className="ai-result-block">
            <h4 className="ai-result-title">💡 Demonstrated Skills</h4>
            <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
              {items.map(({ name, justification }, i) => (
                <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                  <span className="tag accent" style={{ fontSize: "0.82rem", whiteSpace: "nowrap" }}>{name}</span>
                  {justification && (
                    <span style={{ fontSize: "0.82rem", color: "var(--text-muted, #9aa6de)" }}>{justification}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      }
    }

    if (cards.length === 0) {
      return <p className="text-muted" style={{ padding: "8px 0" }}>No results yet. Choose a type and click Run AI Analysis.</p>;
    }
    return <>{cards}</>;
  }

  if (loading) return <div className="page-wrap"><div className="spinner" /></div>;
  if (!project) return <div className="page-wrap"><p>Project not found.</p></div>;

  const displayName = projectName(project);
  const hasStoredAnalysis = !!(project.ai_analysis || project.ai_description);

  return (
    <div className="page-wrap">
      <button className="btn-secondary back-btn" onClick={() => nav(-1)}>← Back</button>

      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}



      {/* ── Hero ── */}
      <div className="pp-hero">
        <div className="pp-thumbnail-wrap">
          {project.thumbnail_path
            ? <img src={thumbUrl(project.thumbnail_path)} alt="thumbnail" className="pp-thumbnail"
                onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
              />
            : null
          }
          <div className="pp-thumbnail-placeholder"
            style={{ display: project.thumbnail_path ? "none" : "flex" }}>
            {(displayName || "?")[0].toUpperCase()}
          </div>
          <div className="thumb-upload">
            <input type="file" accept="image/*"
              onChange={e => setThumbFile(e.target.files[0])} />
            {thumbFile && (
              <button className="btn-primary" style={{ marginTop: 6 }} onClick={uploadThumbnail}>
                {project.thumbnail_path ? "Change Thumbnail" : "Set Thumbnail"}
              </button>
            )}
            {project.thumbnail_path && !thumbFile && (
              <button className="btn-danger" style={{ marginTop: 6, fontSize: "0.78rem" }} onClick={removeThumbnail}>
                Remove Thumbnail
              </button>
            )}
          </div>
        </div>

        <div className="pp-info">
          <div className="pp-tags">
            <span className="tag">{project.project_type || "unknown"}</span>
            {project.is_featured && <span className="tag success">⭐ featured</span>}
            {project.is_hidden && <span className="tag warning">hidden</span>}
            {project.importance_score != null && (
              <span className="tag accent">Score: {Number(project.importance_score).toFixed(2)}</span>
            )}
          </div>
          <h1>{displayName}</h1>
          <p className="pp-desc">
            {project.ai_description || project.description || "No description yet. Run AI Analysis to generate one."}
          </p>
          <div className="pp-actions">
            <button className="btn-primary" onClick={() => setEditing(!editing)}>
              {editing ? "Cancel" : "Edit"}
            </button>
            <button className="btn-danger" onClick={deleteProject} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete"}
            </button>
          </div>
        </div>
      </div>

      {/* ── Edit form ── */}
      {editing && (
        <div className="card pp-edit-form">
          <h2>Edit Project</h2>
          <div className="form-grid">
            <label>Custom Name / Description
              <textarea rows={3} value={form.custom_description}
                onChange={e => setForm({ ...form, custom_description: e.target.value })}
                placeholder="Override the auto-generated name shown everywhere" />
            </label>
            <label>Your Role
              <input value={form.user_role}
                onChange={e => setForm({ ...form, user_role: e.target.value })}
                placeholder="e.g. Lead Developer, Designer" />
            </label>
            <label>Success Evidence
              <textarea rows={3} value={form.success_evidence}
                onChange={e => setForm({ ...form, success_evidence: e.target.value })}
                placeholder="Metrics, feedback, grades, evaluation…" />
            </label>
            <label>Importance Score (0–1)
              <input type="number" min="0" max="1" step="0.01" value={form.importance_score}
                onChange={e => setForm({ ...form, importance_score: e.target.value })} />
            </label>
          </div>
          <div className="form-checks">
            <label><input type="checkbox" checked={form.is_featured}
              onChange={e => setForm({ ...form, is_featured: e.target.checked })} /> Featured</label>
            <label><input type="checkbox" checked={form.is_hidden}
              onChange={e => setForm({ ...form, is_hidden: e.target.checked })} /> Hidden from portfolio</label>
          </div>
          <button className="btn-primary" style={{ marginTop: 14 }} onClick={saveEdit}>Save Changes</button>
        </div>
      )}

      {/* ── Role & Evidence ── */}
      {project.user_role && (
        <div className="card pp-section">
          <h3>Your Role</h3>
          <p>{project.user_role}</p>
        </div>
      )}
      {project.success_evidence && (
        <div className="card pp-section">
          <h3>Success Evidence</h3>
          <p>{project.success_evidence}</p>
        </div>
      )}

      {/* ── AI Analysis ── */}
      <div className="card pp-ai-section">
        <div className="pp-ai-header">
          <div>
            <h2>AI Analysis</h2>
            <p className="text-muted" style={{ fontSize: "0.85rem", marginTop: 4 }}>
              {!aiConsentGranted
                ? "AI features are disabled. Enable them in Settings to run analysis."
                : hasStoredAnalysis
                  ? "Showing saved analysis. Run again to refresh."
                  : "No analysis yet. Choose a type and run to generate insights."}
            </p>
          </div>
          <div className="pp-ai-controls">
            <select value={aiType} onChange={e => setAiType(e.target.value)} disabled={!aiConsentGranted}>
              <option value="overview">Overview</option>
              <option value="technical_depth">Technical Depth</option>
              <option value="skills_extraction">Skills Extraction</option>
              <option value="skill_growth">Skill Growth</option>
            </select>
            <button
              className="btn-primary"
              onClick={analyze}
              disabled={analyzing || !aiConsentGranted}
              title={!aiConsentGranted ? "Enable AI features in Settings" : ""}
              style={{ whiteSpace: "nowrap" }}
            >
              {analyzing
                ? <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 2, marginRight: 6, display: "inline-block" }} />Analyzing…</>
                : "▶ Run Analysis"}
            </button>
          </div>
        </div>

        <div className="ai-results-wrap">
          {!aiConsentGranted
            ? <p className="text-muted" style={{ padding: "8px 0" }}>
                AI analysis is disabled. Go to <a href="/settings">Settings</a> to enable AI features.
              </p>
            : analyzing
              ? <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "16px 0", color: "#9aa6de" }}>
                  <div className="spinner" />
                  <span>Running {aiType.replace(/_/g, " ")} analysis…</span>
                </div>
              : renderAnalysis(analysisResult)
          }
        </div>
      </div>

      {/* ── Evidence ── */}
      <div className="card pp-ai-section">
        <div className="pp-ai-header">
          <div>
            <h2>Evidence</h2>
            <p className="text-muted" style={{ fontSize: "0.85rem", marginTop: 4 }}>
              Metrics, feedback, and achievements that demonstrate project success
            </p>
          </div>
          <div className="pp-ai-controls">
            <button className="btn-secondary" onClick={autoExtractEvidence} disabled={evidenceLoading} style={{ whiteSpace: "nowrap" }}>
              ⚡ Auto-Extract
            </button>
            <button className="btn-danger" onClick={clearEvidence} style={{ whiteSpace: "nowrap", fontSize: "0.82rem" }}>
              🗑 Clear
            </button>
          </div>
        </div>

        <div className="ev-tabs" style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
          {["view", "metric", "feedback", "achievement"].map(t => (
            <button key={t}
              className={`btn-secondary ${evidenceTab === t ? "active" : ""}`}
              style={{ fontSize: "0.82rem", padding: "4px 12px" }}
              onClick={() => setEvidenceTab(t)}>
              {t === "view" ? "View All" : t === "metric" ? "+ Metric" : t === "feedback" ? "+ Feedback" : "+ Achievement"}
            </button>
          ))}
        </div>

        {evidenceLoading ? <div className="spinner" /> : evidenceTab === "view" ? (
          <div>
            {(!evidence || Object.keys(evidence).length === 0) ? (
              <p className="text-muted">No evidence yet. Use Auto-Extract or add manually above.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {/* ── Code evidence ── */}
                {evidence.test_coverage != null && (
                  <div><strong>Test Coverage:</strong> {evidence.test_coverage}%</div>
                )}
                {evidence.code_quality && (
                  <div><strong>Code Quality:</strong> {evidence.code_quality}</div>
                )}
                {/* ── Text/writing evidence ── */}
                {(evidence.word_count || evidence.document_type || evidence.complexity || evidence.audience || evidence.estimated_reading_time_min) && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Document Info</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {evidence.word_count && <span className="tag accent">📝 {evidence.word_count.toLocaleString()} words</span>}
                      {evidence.document_type && <span className="tag accent">📄 {evidence.document_type}</span>}
                      {evidence.complexity && <span className="tag accent">⚡ {evidence.complexity}</span>}
                      {evidence.audience && <span className="tag accent">👥 {evidence.audience}</span>}
                      {evidence.estimated_reading_time_min && <span className="tag accent">⏱ {evidence.estimated_reading_time_min} min read</span>}
                    </div>
                  </div>
                )}
                {evidence.topics?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Topics</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {evidence.topics.map((t, i) => <span key={i} className="tag">{t}</span>)}
                    </div>
                  </div>
                )}
                {evidence.writing_strengths?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Writing Strengths</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {evidence.writing_strengths.map((s, i) => <span key={i} className="tag accent">{s}</span>)}
                    </div>
                  </div>
                )}
                {/* ── Media evidence ── */}
                {(evidence.media_type || evidence.complexity) && !evidence.word_count && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Media Info</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {evidence.media_type && <span className="tag accent">🎬 {evidence.media_type}</span>}
                      {evidence.complexity && <span className="tag accent">⚡ {evidence.complexity}</span>}
                    </div>
                  </div>
                )}
                {evidence.themes?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Themes</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {evidence.themes.map((t, i) => <span key={i} className="tag">{t}</span>)}
                    </div>
                  </div>
                )}
                {evidence.creative_strengths?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Creative Strengths</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {evidence.creative_strengths.map((s, i) => <span key={i} className="tag accent">{s}</span>)}
                    </div>
                  </div>
                )}
                {evidence.tools_used?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Tools Used</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {evidence.tools_used.map((t, i) => <span key={i} className="tag">{t}</span>)}
                    </div>
                  </div>
                )}
                {evidence.manual_metrics && Object.keys(evidence.manual_metrics).length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Metrics</h4>
                    {Object.entries(evidence.manual_metrics).map(([k, v]) => (
                      <div key={k} style={{ display: "flex", gap: 12, alignItems: "baseline", marginBottom: 4 }}>
                        <span className="tag accent">{k}</span>
                        <span>{typeof v === "object" ? v.value : v}</span>
                        {typeof v === "object" && v.description && <span className="text-muted" style={{ fontSize: "0.82rem" }}>{v.description}</span>}
                      </div>
                    ))}
                  </div>
                )}
                {evidence.feedback?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Feedback</h4>
                    {evidence.feedback.map((fb, i) => (
                      <div key={i} style={{ borderLeft: "2px solid #4a5568", paddingLeft: 12, marginBottom: 10 }}>
                        <p style={{ margin: 0 }}>"{fb.text}"</p>
                        <div style={{ display: "flex", gap: 12, marginTop: 4, fontSize: "0.78rem", color: "#9aa6de" }}>
                          {fb.source && <span>{fb.source}</span>}
                          {fb.rating && <span>{"★".repeat(fb.rating)}{"☆".repeat(5 - fb.rating)}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {evidence.achievements?.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Achievements</h4>
                    {evidence.achievements.map((a, i) => (
                      <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                        <span>🏆 {a.description}</span>
                        {a.date && <span className="text-muted" style={{ fontSize: "0.78rem" }}>{a.date}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : evidenceTab === "metric" ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 480 }}>
            <h4>Add Metric</h4>
            <label>Name *<input value={metricForm.name} onChange={e => setMetricForm({ ...metricForm, name: e.target.value })} placeholder="e.g. Users, Downloads, Test Coverage" /></label>
            <label>Value *<input value={metricForm.value} onChange={e => setMetricForm({ ...metricForm, value: e.target.value })} placeholder="e.g. 1000, 95%, A+" /></label>
            <label>Description<input value={metricForm.description} onChange={e => setMetricForm({ ...metricForm, description: e.target.value })} placeholder="Brief explanation" /></label>
            <button className="btn-primary" style={{ marginTop: 4 }} onClick={addMetric}>Add Metric</button>
          </div>
        ) : evidenceTab === "feedback" ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 480 }}>
            <h4>Add Feedback</h4>
            <label>Feedback *<textarea rows={3} value={feedbackForm.text} onChange={e => setFeedbackForm({ ...feedbackForm, text: e.target.value })} placeholder="What was said about this project?" /></label>
            <label>Source<input value={feedbackForm.source} onChange={e => setFeedbackForm({ ...feedbackForm, source: e.target.value })} placeholder="e.g. Client, Professor, Manager" /></label>
            <label>Rating 1–5<input type="number" min="1" max="5" value={feedbackForm.rating} onChange={e => setFeedbackForm({ ...feedbackForm, rating: e.target.value })} /></label>
            <button className="btn-primary" style={{ marginTop: 4 }} onClick={addFeedback}>Add Feedback</button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 480 }}>
            <h4>Add Achievement</h4>
            <label>Description *<input value={achieveForm.description} onChange={e => setAchieveForm({ ...achieveForm, description: e.target.value })} placeholder="e.g. Won 1st place at hackathon, Received A+" /></label>
            <label>Date<input type="date" value={achieveForm.date} onChange={e => setAchieveForm({ ...achieveForm, date: e.target.value })} /></label>
            <button className="btn-primary" style={{ marginTop: 4 }} onClick={addAchievement}>Add Achievement</button>
          </div>
        )}
      </div>

      {/* ── Stats grid ── */}
      <div className="pp-detail-grid">
        {userContrib ? (
          <div className="card">
            <h3>Contribution</h3>
            <table className="pp-table">
              <tbody>
                <tr><td>Name</td><td>{userContrib.name}</td></tr>
                <tr><td>Commits</td><td>{userContrib.commit_count}</td></tr>
                <tr><td>Lines added</td><td>{userContrib.lines_added}</td></tr>
                <tr><td>Lines deleted</td><td>{userContrib.lines_deleted}</td></tr>
                <tr><td>Contribution</td><td>{userContrib.contribution_percent}%</td></tr>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card">
            <h3>Metrics</h3>
            <table className="pp-table">
              <tbody>
                {[
                  ["Files", project.file_count],
                  ["Lines of Code", project.lines_of_code?.toLocaleString()],
                  ["Word Count", project.word_count?.toLocaleString()],
                  ["Total Size", fmtBytes(project.total_size_bytes)],
                ].filter(([,v]) => v != null && v !== "").map(([k, v]) => (
                  <tr key={k}><td>{k}</td><td>{v}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="card">
          <h3>Languages & Frameworks</h3>
          <div className="chip-group">
            {(project.languages || []).map((l, i) => <span key={i} className="tag accent">{l}</span>)}
            {(project.frameworks || []).map((f, i) => <span key={i} className="tag">{f}</span>)}
            {!project.languages?.length && !project.frameworks?.length &&
              <span className="text-muted">None detected</span>}
          </div>
        </div>

        <div className="card">
          <h3>Skills</h3>
          <div className="chip-group">
            {(project.skills || []).length === 0
              ? <span className="text-muted">No skills detected. Run AI Analysis or re-upload.</span>
              : (project.skills || []).map((s, i) => (
                <span key={i} className="tag">{typeof s === "string" ? s.replace(/_/g, " ") : s}</span>
              ))
            }
          </div>
        </div>

        <div className="card">
          <h3>Details</h3>
          <table className="pp-table">
            <tbody>
              {[
                ["Date Scanned", project.date_scanned && new Date(project.date_scanned).toLocaleDateString()],
                ["Date Created", project.date_created && new Date(project.date_created).toLocaleDateString()],
                ["Tags", (project.tags || []).join(", ") || null],
                ["Collaboration", project.collaboration_type || null],
              ].filter(([,v]) => v).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td>{v}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}