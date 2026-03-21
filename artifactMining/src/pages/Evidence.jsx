import React, { useEffect, useState } from "react";
import { apiFetch } from "../apiClient";
import "./Evidence.css";

const BASE = "http://127.0.0.1:8000";

export default function Evidence() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  // Forms
  const [metricForm, setMetricForm] = useState({ name: "", value: "", description: "" });
  const [feedbackForm, setFeedbackForm] = useState({ text: "", source: "", rating: "" });
  const [achieveForm, setAchieveForm] = useState({ description: "", date: "" });
  const [activeTab, setActiveTab] = useState("view");

  useEffect(() => {
    apiFetch("/projects").then(d => setProjects(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);

  async function loadEvidence(id) {
    setSelected(id); setEvidence(null); setLoading(true); setMsg(null);
    try {
      const d = await apiFetch(`/evidence/${id}`);
      setEvidence(d);
    } catch (e) { setEvidence({}); }
    finally { setLoading(false); }
  }

  async function autoExtract() {
    setLoading(true); setMsg(null);
    try {
      await apiFetch(`/evidence/${selected}/extract`, { method: "POST" });
      setMsg({ type: "success", text: "Evidence extracted!" });
      loadEvidence(selected);
    } catch (e) { setMsg({ type: "error", text: e.message }); setLoading(false); }
  }

  async function addMetric() {
    if (!metricForm.name || !metricForm.value) { setMsg({ type: "error", text: "Name and value required." }); return; }
    try {
      await apiFetch(`/evidence/${selected}/metric`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metric_name: metricForm.name, value: metricForm.value, description: metricForm.description }),
      });
      setMsg({ type: "success", text: "Metric added!" });
      setMetricForm({ name: "", value: "", description: "" });
      loadEvidence(selected);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function addFeedback() {
    if (!feedbackForm.text) { setMsg({ type: "error", text: "Feedback text required." }); return; }
    try {
      await apiFetch(`/evidence/${selected}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: feedbackForm.text, source: feedbackForm.source, rating: feedbackForm.rating ? Number(feedbackForm.rating) : null }),
      });
      setMsg({ type: "success", text: "Feedback added!" });
      setFeedbackForm({ text: "", source: "", rating: "" });
      loadEvidence(selected);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function addAchievement() {
    if (!achieveForm.description) { setMsg({ type: "error", text: "Description required." }); return; }
    try {
      await apiFetch(`/evidence/${selected}/achievement`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: achieveForm.description, date: achieveForm.date || null }),
      });
      setMsg({ type: "success", text: "Achievement added!" });
      setAchieveForm({ description: "", date: "" });
      loadEvidence(selected);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function clearEvidence() {
    if (!window.confirm("Clear all evidence for this project?")) return;
    try {
      await apiFetch(`/evidence/${selected}`, { method: "DELETE" });
      setMsg({ type: "success", text: "Evidence cleared." });
      loadEvidence(selected);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  const projName = (p) => p.custom_description || p.name || `Project ${p.id}`;

  return (
    <div className="page-wrap">
      <h1 style={{ marginBottom: 8 }}>Evidence Manager</h1>
      <p className="text-muted" style={{ marginBottom: 24 }}>Add metrics, feedback, and achievements to showcase success</p>

      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="ev-layout">
        {/* Project list */}
        <div className="card ev-sidebar">
          <h3 style={{ marginBottom: 12 }}>Projects</h3>
          {projects.length === 0
            ? <p className="text-muted">No projects yet.</p>
            : projects.map(p => (
              <div key={p.id} className={`ev-proj-row ${selected === p.id ? "active" : ""}`} onClick={() => loadEvidence(p.id)}>
                <span>{projName(p)}</span>
                <span className="tag">{p.project_type || "?"}</span>
              </div>
            ))
          }
        </div>

        {/* Main panel */}
        <div className="ev-main">
          {!selected ? (
            <div className="card" style={{ textAlign: "center", padding: "60px 24px", color: "#9aa6de" }}>
              Select a project to manage evidence
            </div>
          ) : (
            <>
              <div className="ev-tabs">
                {["view", "metric", "feedback", "achievement"].map(t => (
                  <button key={t} className={`ev-tab ${activeTab === t ? "active" : ""}`} onClick={() => setActiveTab(t)}>
                    {t === "view" ? "View" : t === "metric" ? "+ Metric" : t === "feedback" ? "+ Feedback" : "+ Achievement"}
                  </button>
                ))}
                <button className="ev-tab" style={{ marginLeft: "auto" }} onClick={autoExtract} disabled={loading}>
                  ⚡ Auto-Extract
                </button>
                <button className="ev-tab danger" onClick={clearEvidence}>🗑 Clear All</button>
              </div>

              {loading ? <div className="spinner" style={{ marginTop: 24 }} /> : (

                activeTab === "view" ? (
                  <div className="ev-view-grid">
                    {(!evidence || Object.keys(evidence).length === 0) ? (
                      <div className="card" style={{ gridColumn: "1/-1", color: "#9aa6de", padding: 32 }}>
                        No evidence yet. Use Auto-Extract or add manually.
                      </div>
                    ) : <>
                      {evidence.test_coverage != null && <EvidenceCard title="Test Coverage" value={`${evidence.test_coverage}%`} icon="🧪" />}
                      {evidence.code_quality && <EvidenceCard title="Code Quality" value={evidence.code_quality} icon="⭐" />}
                      {evidence.manual_metrics && Object.keys(evidence.manual_metrics).length > 0 && (
                        <div className="card">
                          <h3 style={{ marginBottom: 10 }}>Manual Metrics</h3>
                          {Object.entries(evidence.manual_metrics).map(([k, v]) => (
                            <div key={k} className="ev-metric-row">
                              <span className="ev-metric-name">{k}</span>
                              <span className="ev-metric-val">{typeof v === "object" ? v.value : v}</span>
                              {typeof v === "object" && v.description && <span className="ev-metric-desc">{v.description}</span>}
                            </div>
                          ))}
                        </div>
                      )}
                      {evidence.feedback?.length > 0 && (
                        <div className="card">
                          <h3 style={{ marginBottom: 10 }}>Feedback ({evidence.feedback.length})</h3>
                          {evidence.feedback.map((fb, i) => (
                            <div key={i} className="ev-feedback-item">
                              <p className="ev-feedback-text">"{fb.text}"</p>
                              <div className="ev-feedback-meta">
                                {fb.source && <span>{fb.source}</span>}
                                {fb.rating && <span>{"★".repeat(fb.rating)}{"☆".repeat(5 - fb.rating)}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      {evidence.achievements?.length > 0 && (
                        <div className="card">
                          <h3 style={{ marginBottom: 10 }}>Achievements ({evidence.achievements.length})</h3>
                          {evidence.achievements.map((a, i) => (
                            <div key={i} className="ev-achieve-row">
                              <span>🏆 {a.description}</span>
                              {a.date && <span className="text-muted" style={{ fontSize: "0.78rem" }}>{a.date}</span>}
                            </div>
                          ))}
                        </div>
                      )}
                      {evidence.readme_badges?.length > 0 && (
                        <div className="card">
                          <h3 style={{ marginBottom: 10 }}>README Badges ({evidence.readme_badges.length})</h3>
                          <div className="chip-group">
                            {evidence.readme_badges.map((b, i) => <span key={i} className="tag success">{b.alt || b.type || "badge"}</span>)}
                          </div>
                        </div>
                      )}
                    </>}
                  </div>
                ) : activeTab === "metric" ? (
                  <div className="card ev-form">
                    <h3 style={{ marginBottom: 16 }}>Add Manual Metric</h3>
                    <label>Metric Name *<input value={metricForm.name} onChange={e => setMetricForm({ ...metricForm, name: e.target.value })} placeholder="e.g. Users, Downloads, Test Coverage" /></label>
                    <label>Value *<input value={metricForm.value} onChange={e => setMetricForm({ ...metricForm, value: e.target.value })} placeholder="e.g. 1000, 95%, A+" /></label>
                    <label>Description (optional)<input value={metricForm.description} onChange={e => setMetricForm({ ...metricForm, description: e.target.value })} placeholder="Brief explanation" /></label>
                    <button className="btn-primary" style={{ marginTop: 8 }} onClick={addMetric}>Add Metric</button>
                  </div>
                ) : activeTab === "feedback" ? (
                  <div className="card ev-form">
                    <h3 style={{ marginBottom: 16 }}>Add Feedback / Testimonial</h3>
                    <label>Feedback Text *<textarea rows={4} value={feedbackForm.text} onChange={e => setFeedbackForm({ ...feedbackForm, text: e.target.value })} placeholder="What was said about this project?" /></label>
                    <label>Source (optional)<input value={feedbackForm.source} onChange={e => setFeedbackForm({ ...feedbackForm, source: e.target.value })} placeholder="e.g. Client, Professor, Manager" /></label>
                    <label>Rating 1–5 (optional)<input type="number" min="1" max="5" value={feedbackForm.rating} onChange={e => setFeedbackForm({ ...feedbackForm, rating: e.target.value })} /></label>
                    <button className="btn-primary" style={{ marginTop: 8 }} onClick={addFeedback}>Add Feedback</button>
                  </div>
                ) : (
                  <div className="card ev-form">
                    <h3 style={{ marginBottom: 16 }}>Add Achievement / Award</h3>
                    <label>Description *<input value={achieveForm.description} onChange={e => setAchieveForm({ ...achieveForm, description: e.target.value })} placeholder="e.g. Won 1st place at hackathon, Received A+, Deployed to production" /></label>
                    <label>Date (optional)<input type="date" value={achieveForm.date} onChange={e => setAchieveForm({ ...achieveForm, date: e.target.value })} /></label>
                    <button className="btn-primary" style={{ marginTop: 8 }} onClick={addAchievement}>Add Achievement</button>
                  </div>
                )
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function EvidenceCard({ title, value, icon }) {
  return (
    <div className="card" style={{ textAlign: "center", padding: "20px 16px" }}>
      <div style={{ fontSize: "2rem", marginBottom: 6 }}>{icon}</div>
      <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#a5b4fc" }}>{value}</div>
      <div style={{ fontSize: "0.78rem", color: "#9aa6de", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>{title}</div>
    </div>
  );
}
