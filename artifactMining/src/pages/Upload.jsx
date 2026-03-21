import React, { useState, useRef, useEffect } from "react";
import { apiUpload, apiFetch } from "../apiClient";
import "./Upload.css";

const ACCEPTED = ".zip,.py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.cs,.go,.rs,.rb,.php,.swift,.kt,.r,.m,.txt,.md,.pdf,.docx,.csv,.json,.xml,.html,.css,.png,.jpg,.jpeg,.gif,.webp,.mp4,.mov,.avi,.mp3,.wav";

export default function Upload() {
  const [tab, setTab] = useState("new"); // "new" | "incremental"
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [basicConsent, setBasicConsent] = useState(false);
  // incremental
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [incFile, setIncFile] = useState(null);
  const [incDragging, setIncDragging] = useState(false);
  const fileRef = useRef();
  const incFileRef = useRef();

  useEffect(() => { loadConsent(); }, []);

  async function loadConsent() {
    try {
      const config = await apiFetch("/configuration/current-configuration");
      setBasicConsent(!!config.consent.basic_consent_granted);
    } catch {
      setBasicConsent(false);
    }
  }

  function onDrop(e) {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if (f) setFile(f);
  }
  function onIncDrop(e) {
    e.preventDefault(); setIncDragging(false);
    const f = e.dataTransfer.files[0]; if (f) setIncFile(f);
  }

  async function upload() {
    if (!basicConsent) { setStatus({ type: "error", text: "File access consent is required. Grant it using the button below." }); return; }
    if (!file) { setStatus({ type: "error", text: "Select a file first." }); return; }
    setLoading(true); setStatus(null); setResult(null);
    const fd = new FormData(); fd.append("file", file);
    try {
      const d = await apiUpload("/projects/upload", fd);
      if (d.status === "skipped") {
        setStatus({ type: "error", text: `File was skipped — it may be an excluded file type. Check your excluded file types under Settings → Privacy before uploading.` });
      } else if (d.status === "exists") {
        setStatus({ type: "info", text: `This project already exists: "${d.project_name}".` });
      } else {
        setStatus({ type: "success", text: "Uploaded and analyzed!" });
        setFile(null);
      }
    } catch (e) { setStatus({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function loadProjects() {
    try { const d = await apiFetch("/projects"); setProjects(Array.isArray(d) ? d : []); }
    catch { setProjects([]); }
  }

  async function uploadIncremental() {
    if (!basicConsent) { setStatus({ type: "error", text: "File access consent is required. Grant it using the button below." }); return; }
    if (!selectedProject) { setStatus({ type: "error", text: "Select a project." }); return; }
    if (!incFile) { setStatus({ type: "error", text: "Select a file." }); return; }
    setLoading(true); setStatus(null); setResult(null);
    const fd = new FormData(); fd.append("file", incFile);
    try {
      const d = await apiUpload(`/projects/${selectedProject}/upload`, fd);
      if (d.success === false) {
        setStatus({ type: "error", text: d.error || "Upload failed." });
      } else if (d.files_added === 0) {
        setStatus({ type: "info", text: d.details?.message || "No new files added — all were duplicates or excluded." });
      } else {
        setStatus({ type: "success", text: `Added ${d.files_added} file${d.files_added !== 1 ? "s" : ""} to project.` });
        setIncFile(null);
      }
    } catch (e) { setStatus({ type: "error", text: e.message }); }
    finally { setLoading(false); }
  }

  async function revokeConsent(type) {
    try {
      await apiFetch(`/consent/${type}-consent-revoke`, { method: "POST", headers: { "Content-Type": "application/json" } });
      setStatus({ type: "success", text: `${type === "basic" ? "File access" : "AI"} consent revoked.` });
      if (type === "basic") setBasicConsent(false);
    } catch (e) { setStatus({ type: "error", text: e.message }); }
  }

  async function grantConsent(type) {
    try {
      await apiFetch(`/consent/${type}-consent-grant`, { method: "POST", headers: { "Content-Type": "application/json" } });
      setStatus({ type: "success", text: `${type === "basic" ? "File access" : "AI"} consent granted.` });
      if (type === "basic") setBasicConsent(true);
    } catch (e) { setStatus({ type: "error", text: e.message }); }
  }

  return (
    <div className="page-wrap">
      <h1 style={{ marginBottom: 24 }}>Upload Project</h1>

      <div className="upload-tabs">
        <button className={`upload-tab ${tab === "new" ? "active" : ""}`} onClick={() => setTab("new")}>New Project</button>
        <button className={`upload-tab ${tab === "incremental" ? "active" : ""}`} onClick={() => { setTab("incremental"); loadProjects(); }}>Add to Existing</button>
      </div>

      {!basicConsent && (
        <div className="alert error" style={{ marginBottom: 16 }}>
          File access consent is required before uploading. Grant it in the Consent panel on the right.
        </div>
      )}

      {status && <div className={`alert ${status.type}`}>{status.text}</div>}

      <div className="upload-layout">
        {tab === "new" ? (
          <div className="card upload-main">
            <div
              className={`drop-zone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""} ${!basicConsent ? "disabled" : ""}`}
              onDragOver={e => { e.preventDefault(); if (basicConsent) setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={basicConsent ? onDrop : e => e.preventDefault()}
              onClick={() => basicConsent && fileRef.current.click()}
              style={!basicConsent ? { opacity: 0.4, cursor: "not-allowed" } : {}}
            >
              <input ref={fileRef} type="file" accept={ACCEPTED} style={{ display: "none" }} onChange={e => setFile(e.target.files[0])} />
              {file ? (
                <><div className="drop-icon">📦</div><p className="drop-filename">{file.name}</p><p className="drop-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p></>
              ) : (
                <><div className="drop-icon">⬆</div><p>Drag & drop a file here</p><p className="drop-hint">or click to browse</p><p className="drop-hint" style={{ marginTop: 6 }}>ZIP · Python · JS/TS · Java · C/C++ · Text · Docs · Images · Media</p></>
              )}
            </div>
            {file && <button className="btn-danger" style={{ alignSelf: "flex-start", marginTop: 8 }} onClick={() => setFile(null)}>Remove</button>}
            <button className="btn-primary upload-btn" onClick={upload} disabled={loading || !file || !basicConsent}
              title={!basicConsent ? "Grant file access consent first" : ""}>
              {loading ? <><div className="spinner" /> Uploading…</> : "Upload & Analyze"}
            </button>
          </div>
        ) : (
          <div className="card upload-main">
            <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.85rem", color: "#9aa6de" }}>
              Select existing project
              <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)} style={{ marginTop: 2 }} disabled={!basicConsent}>
                <option value="">-- Choose a project --</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.custom_description || p.name || `Project ${p.id}`}</option>
                ))}
              </select>
            </label>
            <div
              className={`drop-zone ${incDragging ? "dragging" : ""} ${incFile ? "has-file" : ""}`}
              style={{ marginTop: 16, ...(!basicConsent ? { opacity: 0.4, cursor: "not-allowed" } : {}) }}
              onDragOver={e => { e.preventDefault(); if (basicConsent) setIncDragging(true); }}
              onDragLeave={() => setIncDragging(false)}
              onDrop={basicConsent ? onIncDrop : e => e.preventDefault()}
              onClick={() => basicConsent && incFileRef.current.click()}
            >
              <input ref={incFileRef} type="file" accept={ACCEPTED} style={{ display: "none" }} onChange={e => setIncFile(e.target.files[0])} />
              {incFile ? (
                <><div className="drop-icon">📦</div><p className="drop-filename">{incFile.name}</p></>
              ) : (
                <><div className="drop-icon">➕</div><p>Drop additional files here</p><p className="drop-hint">Duplicate files will be skipped automatically</p></>
              )}
            </div>
            {incFile && <button className="btn-danger" style={{ alignSelf: "flex-start", marginTop: 8 }} onClick={() => setIncFile(null)}>Remove</button>}
            <button className="btn-primary upload-btn" onClick={uploadIncremental} disabled={loading || !incFile || !selectedProject || !basicConsent}
              title={!basicConsent ? "Grant file access consent first" : ""}>
              {loading ? <><div className="spinner" /> Adding…</> : "Add to Project"}
            </button>
          </div>
        )}

        <div className="upload-sidebar">
          <div className="card">
            <h3>Consent</h3>
            <p className="text-muted" style={{ marginBottom: 8 }}>Your data is stored locally and never transmitted without AI consent.</p>
            <div style={{ marginBottom: 12 }}>
              <span className={`tag ${basicConsent ? "success" : "warning"}`}>
                File Access: {basicConsent ? "✓ Granted" : "✗ Not granted"}
              </span>
            </div>
            <div className="consent-btns">
              <button className="btn-secondary" onClick={() => grantConsent("basic")}>Grant File Access</button>
              <button className="btn-secondary" onClick={() => revokeConsent("basic")}>Revoke File Access</button>
              <button className="btn-secondary" onClick={() => grantConsent("ai")}>Grant AI Consent</button>
              <button className="btn-secondary" onClick={() => revokeConsent("ai")}>Revoke AI Consent</button>
            </div>
          </div>
          <div className="card">
            <h3>Accepted File Types</h3>
            <p className="text-muted" style={{ marginBottom: 10 }}>Upload any of these:</p>
            <div className="chip-group">
              {[".zip",".py",".js/.ts",".jsx/.tsx",".java",".cpp/.c",".cs",".go",".rs",".rb",".php",".swift",".kt",".txt",".md",".pdf",".docx",".csv",".json",".html",".png/.jpg",".mp4/.mov",".mp3"].map(t => (
                <span key={t} className="tag">{t}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}