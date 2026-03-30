import { Joyride } from 'react-joyride';
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Analysis.css";

export default function Analysis() {
  // Only run walkthrough if not seen
  const [runWalkthrough, setRunWalkthrough] = useState(() => {
    return localStorage.getItem('analysis_walkthrough_seen') !== '1';
  });
  // Set flag as soon as walkthrough starts
  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('analysis_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);
  const walkthroughSteps = [
    {
      target: 'body',
      placement: 'center',
      title: 'Project Analysis',
      content: 'This page lets you score, rank, analyze, and manage your projects. Let’s take a quick tour!'
    },
    {
      target: '.an-tab:nth-child(1)',
      placement: 'bottom',
      title: 'Score & Rank Tab',
      content: 'Compute importance scores for all your projects and use AI to rank them based on your chosen skills.'
    },
    {
      target: '.an-tab:nth-child(2)',
      placement: 'bottom',
      title: 'AI Analysis Tab',
      content: 'Use AI to analyze a single project or batch analyze all projects for overviews, technical depth, and skills.'
    },
    {
      target: '.an-tab:nth-child(3)',
      placement: 'bottom',
      title: 'Timeline Tab',
      content: 'View your projects in chronological order to see your progress over time.'
    },
    {
      target: '.an-tab:nth-child(4)',
      placement: 'bottom',
      title: 'Roles Tab',
      content: 'Assign and manage your role for each project, such as Lead Developer, Designer, or PM.'
    }
  ];
  const [projects, setProjects] = useState([]);
  const [tab, setTab] = useState("score");
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scores, setScores] = useState(null);
  const [rankSkills, setRankSkills] = useState("");
  const [topK, setTopK] = useState(3);
  const [rankResults, setRankResults] = useState(null);
  const [aiProjectId, setAiProjectId] = useState("");
  const [aiType, setAiType] = useState("overview");
  const [aiResult, setAiResult] = useState(null);
  const [batchResults, setBatchResults] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [roleProjectId, setRoleProjectId] = useState("");
  const [roleValue, setRoleValue] = useState("");
  const [rolesData, setRolesData] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    apiFetch("/projects").then(d => setProjects(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);

  const pName = p => projectName(p);

  function setTabAndReset(t) {
    setTab(t); setMsg(null);
    if (t === "timeline") loadTimeline();
    if (t === "roles") loadRoles();
  }

  async function computeScores() {
    setLoading(true); setMsg(null); setScores(null); setRankResults(null);
    try {
      const d = await apiFetch("/projects/compute-importance", { method: "POST" });
      setScores(d);
      setMsg({ type: "success", text: "Updated importance scores for " + d.updated + " project" + (d.updated !== 1 ? "s" : "") + "." });
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function runRanking() {
    setLoading(true); setMsg(null); setRankResults(null); setScores(null);
    try {
      const skills = rankSkills.split(",").map(s => s.trim()).filter(Boolean);
      const d = await apiFetch("/projects/rank", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_skills: skills.length ? skills : null, top_k: Number(topK) }),
      });
      setRankResults(d);
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function runAiAnalysis() {
    if (!aiProjectId) { setMsg({ type: "error", text: "Select a project." }); return; }
    setLoading(true); setMsg(null); setAiResult(null);
    try {
      const d = await apiFetch("/projects/" + aiProjectId + "/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_type: aiType }),
      });
      setAiResult(d);
      setMsg({ type: "success", text: "Analysis complete!" });
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function runBatchAnalysis() {
    setLoading(true); setMsg(null); setBatchResults(null);
    try {
      const d = await apiFetch("/projects/analyze/batch", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_types: [aiType] }),
      });
      setBatchResults(d);
      setMsg({ type: "success", text: "Analyzed " + d.analyzed + " project" + (d.analyzed !== 1 ? "s" : "") + "." });
    } catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function loadTimeline() {
    setLoading(true);
    try { const d = await apiFetch("/projects/timeline"); setTimeline(d); }
    catch (e) { setMsg({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function assignRole() {
    if (!roleProjectId || !roleValue.trim()) { setMsg({ type: "error", text: "Select project and enter role." }); return; }
    try {
      await apiFetch("/portfolio/" + roleProjectId + "/edit", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_role: roleValue.trim() }),
      });
      setMsg({ type: "success", text: "Role assigned!" });
      setRoleValue("");
      loadRoles();
    } catch (e) { setMsg({ type: "error", text: e.message }); }
  }

  async function loadRoles() {
    try { const d = await apiFetch("/projects"); setRolesData(Array.isArray(d) ? d.filter(p => p.user_role) : []); }
    catch { setRolesData([]); }
  }

  function renderAiResult(result) {
    if (!result) return null;
    const r = result.results || result;
    const sections = [];

    if (r.overview) {
      // overview is a plain string from the AI analyzer
      const ov = r.overview;
      const ovText = typeof ov === "string" ? ov : (ov.summary || ov.description || "");
      const ovType = typeof ov === "object" ? ov.project_type : null;
      sections.push(
        <div key="ov" className="card an-result-card">
          <h3>Overview</h3>
          {ovText && <p className="an-result-text" style={{ lineHeight: 1.65, marginTop: 8 }}>{ovText}</p>}
          {ovType && <p className="text-muted" style={{ marginTop: 6 }}>Type: {ovType}</p>}
        </div>
      );
    }

    if (r.technical_depth) {
      sections.push(
        <div key="td" className="card an-result-card">
          <h3>Technical Depth</h3>
          {typeof r.technical_depth === "string"
            ? <p className="an-result-text" style={{ lineHeight: 1.65, marginTop: 8 }}>{r.technical_depth}</p>
            : <ul className="an-result-text" style={{ paddingLeft: 18, marginTop: 8 }}>
                {Object.entries(r.technical_depth).filter(([,v]) => v && typeof v === "string").map(([k,v]) => (
                  <li key={k} style={{ marginBottom: 6 }}><strong>{k.replace(/_/g," ")}:</strong> {v}</li>
                ))}
              </ul>
          }
        </div>
      );
    }

    if (r.skills || r.skills_extraction) {
      const sk = r.skills || r.skills_extraction;
      const items = Array.isArray(sk) ? sk : (typeof sk === "string" ? [sk] : []);
      if (items.length > 0) {
        sections.push(
          <div key="sk" className="card an-result-card">
            <h3>Skills Extracted</h3>
            <div className="chip-group" style={{ marginTop: 10 }}>
              {items.map((s, i) => <span key={i} className="tag accent">{typeof s === "string" ? s : s.skill || s.name || ""}</span>)}
            </div>
          </div>
        );
      }
    }

    if (sections.length === 0) {
      const textParts = Object.entries(r)
        .filter(([k,v]) => typeof v === "string" && v.length > 10 && k !== "project_id" && k !== "analysis_type")
        .map(([k,v]) => (
          <div key={k} className="card an-result-card">
            <h3>{k.replace(/_/g," ")}</h3>
            <p className="an-result-text" style={{ lineHeight: 1.65, marginTop: 8 }}>{v}</p>
          </div>
        ));
      return textParts.length > 0 ? <>{textParts}</> : <p className="text-muted">Analysis returned no readable output for this type.</p>;
    }
    return <>{sections}</>;
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
            localStorage.setItem('analysis_walkthrough_seen', '1');
            setRunWalkthrough(false);
          }
        }}
      />
      <div className="page-wrap">
      <h1 style={{ marginBottom: 8 }}>Analysis</h1>
      <p className="text-muted" style={{ marginBottom: 24 }}>Score, rank, analyze, and manage project roles</p>
      {msg && <div className={"alert " + msg.type}>{msg.text}</div>}

      <div className="an-tabs">
        {[["score","📊 Score & Rank"],["ai","🤖 AI Analysis"],["timeline","📅 Timeline"],["roles","👤 Roles"]].map(([t,l]) => (
          <button key={t} className={"an-tab " + (tab === t ? "active" : "")} onClick={() => setTabAndReset(t)}>{l}</button>
        ))}
      </div>

      {tab === "score" && (
        <div className="an-grid">
          <div className="card">
            <h3 style={{ marginBottom: 10 }}>Compute Importance Scores</h3>
            <p className="text-muted" style={{ marginBottom: 14, fontSize: "0.88rem" }}>Calculates and saves importance scores for all projects based on file count, lines of code, and contribution metrics.</p>
            <button className="btn-primary" onClick={computeScores} disabled={loading}>{loading && !rankResults ? "Computing…" : "Compute All Scores"}</button>
            {scores && (
              <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 4 }}>
                {(scores.scores || []).map((s, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderBottom: "1px solid rgba(107,114,244,0.12)" }}>
                    <span className="an-result-text" style={{ fontSize: "0.88rem" }}>{s.name}</span>
                    <span className="tag accent">{s.importance_score}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 10 }}>AI Project Ranking</h3>
            <p className="text-muted" style={{ marginBottom: 12, fontSize: "0.88rem" }}>Rank your top projects using AI with optional skill prioritization.</p>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 10 }}>
              Skills to prioritize (comma-separated, optional)
              <input value={rankSkills} onChange={e => setRankSkills(e.target.value)} placeholder="Python, React, ML…" />
            </label>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 14 }}>
              Top N
              <input type="number" min="1" max="20" value={topK} onChange={e => setTopK(e.target.value)} style={{ width: 80 }} />
            </label>
            <button className="btn-primary" onClick={runRanking} disabled={loading}>{loading && !scores ? "Ranking…" : "Run AI Ranking"}</button>
          </div>

          {rankResults && (
            <div className="card an-results" style={{ gridColumn: "1 / -1" }}>
              <h3 style={{ marginBottom: 14 }}>Ranking Results</h3>
              {(rankResults.selected || []).length === 0
                ? <p className="text-muted">No results returned.</p>
                : (rankResults.selected || []).map((p, i) => (
                  <div key={i} className="an-result-row" style={{ cursor: p.project_id ? "pointer" : "default" }}
                    onClick={() => p.project_id && nav("/projects/" + p.project_id)}>
                    <span className="an-result-rank">#{i+1}</span>
                    <div style={{ flex: 1 }}>
                      <span className="an-result-name">{p.project_name}</span>
                      {p.skills && p.skills.length > 0 && <p className="text-muted" style={{ fontSize: "0.78rem", marginTop: 2 }}>{p.skills.slice(0,5).join(", ")}</p>}
                    </div>
                    {p._rank_score != null && <span className="tag accent">Score: {Number(p._rank_score).toFixed(3)}</span>}
                    {p.importance_score != null && <span className="tag accent">Importance: {Number(p.importance_score).toFixed(2)}</span>}
                  </div>
                ))
              }
              {rankResults.summary && <p className="text-muted" style={{ marginTop: 14, fontSize: "0.85rem", lineHeight: 1.6 }}>{rankResults.summary}</p>}
            </div>
          )}
        </div>
      )}

      {tab === "ai" && (
        <div className="an-grid">
          <div className="card">
            <h3 style={{ marginBottom: 10 }}>Analyze Single Project</h3>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 10 }}>
              Project
              <select value={aiProjectId} onChange={e => setAiProjectId(e.target.value)}>
                <option value="">-- Select project --</option>
                {projects.map(p => <option key={p.id} value={p.id}>{pName(p)}</option>)}
              </select>
            </label>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 14 }}>
              Analysis type
              <select value={aiType} onChange={e => setAiType(e.target.value)}>
                <option value="overview">Overview — summary and description</option>
                <option value="technical_depth">Technical Depth — patterns and complexity</option>
                <option value="skills_extraction">Skills Extraction — demonstrated skills</option>
                <option value="skill_growth">Skill Growth — learning progression</option>
              </select>
            </label>
            <button className="btn-primary" onClick={runAiAnalysis} disabled={loading || !aiProjectId}>{loading && !batchResults ? "Analyzing…" : "Analyze"}</button>
            <p className="text-muted" style={{ marginTop: 10, fontSize: "0.8rem" }}>Results are saved to the project automatically.</p>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 10 }}>Batch Analyze All Projects</h3>
            <p className="text-muted" style={{ marginBottom: 12, fontSize: "0.88rem" }}>Runs AI analysis across all {projects.length} project{projects.length !== 1 ? "s" : ""}. Saves descriptions back to each project.</p>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 14 }}>
              Analysis type
              <select value={aiType} onChange={e => setAiType(e.target.value)}>
                <option value="overview">Overview</option>
                <option value="technical_depth">Technical Depth</option>
                <option value="skills_extraction">Skills Extraction</option>
              </select>
            </label>
            <button className="btn-primary" onClick={runBatchAnalysis} disabled={loading}>{loading && batchResults === null && !aiResult ? "Running…" : "Batch Analyze (" + projects.length + ")"}</button>
          </div>

          {aiResult && (
            <div style={{ gridColumn: "1 / -1" }}>
              <h3 style={{ marginBottom: 12 }}>Analysis Result</h3>
              {renderAiResult(aiResult)}
            </div>
          )}

          {batchResults && (
            <div className="card an-results" style={{ gridColumn: "1 / -1" }}>
              <h3 style={{ marginBottom: 12 }}>Batch Results — {batchResults.analyzed} projects processed</h3>
              {(batchResults.results || []).map((r, i) => (
                <div key={i} className="an-result-row">
                  <span className={"tag " + (r.success ? "success" : "warning")}>{r.success ? "✓ OK" : "✗ Failed"}</span>
                  <span className="an-result-name">{r.name}</span>
                  {r.error && <span className="text-muted" style={{ fontSize: "0.78rem" }}>{r.error}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "timeline" && (
        <div className="card">
          <h3 style={{ marginBottom: 14 }}>Project Timeline (Chronological)</h3>
          {loading
            ? <div className="spinner" />
            : !timeline || timeline.length === 0
              ? <p className="text-muted">No projects found.</p>
              : (timeline || []).map((p, i) => (
                <div key={p.id || i} className="an-timeline-row" onClick={() => p.id && nav("/projects/" + p.id)}>
                  <div className="an-timeline-dot" />
                  <div className="an-timeline-content">
                    <strong>{p.name || "Untitled"}</strong>
                    <span className="text-muted" style={{ fontSize: "0.78rem" }}>
                      {p.date_created ? new Date(p.date_created).toLocaleDateString("en-CA") : p.date_scanned ? new Date(p.date_scanned).toLocaleDateString("en-CA") : "Unknown date"}
                    </span>
                  </div>
                  <span className="tag">{p.project_type || "?"}</span>
                  {p.importance_score != null && <span className="tag accent">{Number(p.importance_score).toFixed(1)}</span>}
                </div>
              ))
          }
        </div>
      )}

      {tab === "roles" && (
        <div className="an-grid">
          <div className="card">
            <h3 style={{ marginBottom: 12 }}>Assign Role to Project</h3>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 10 }}>
              Project
              <select value={roleProjectId} onChange={e => setRoleProjectId(e.target.value)}>
                <option value="">-- Select --</option>
                {projects.map(p => <option key={p.id} value={p.id}>{pName(p)}</option>)}
              </select>
            </label>
            <label className="an-field-label" style={{ display: "flex", flexDirection: "column", gap: 5, fontSize: "0.82rem", marginBottom: 14 }}>
              Role
              <input value={roleValue} onChange={e => setRoleValue(e.target.value)} placeholder="Lead Developer, Designer, PM…"
                onKeyDown={e => e.key === "Enter" && assignRole()} />
            </label>
            <button className="btn-primary" onClick={assignRole} disabled={!roleProjectId || !roleValue.trim()}>Assign Role</button>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 12 }}>Projects with Assigned Roles</h3>
            {rolesData == null
              ? <p className="text-muted">Loading…</p>
              : rolesData.length === 0
                ? <p className="text-muted">No roles assigned yet. Use the form to assign a role.</p>
                : rolesData.map(p => (
                  <div key={p.id} className="an-result-row" style={{ cursor: "pointer" }} onClick={() => nav("/projects/" + p.id)}>
                    <span className="an-result-name">{pName(p)}</span>
                    <span className="tag accent">{p.user_role}</span>
                  </div>
                ))
            }
          </div>
        </div>
      )}
    </div>
      
  </>);
}