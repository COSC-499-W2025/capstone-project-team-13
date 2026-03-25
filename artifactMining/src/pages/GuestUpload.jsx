import { useState, useRef } from "react";

const BASE = "http://127.0.0.1:8000";
const ACCEPTED = ".zip,.py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.cs,.go,.rs,.rb,.php,.swift,.kt,.r,.txt,.md,.pdf,.docx,.csv,.json,.html,.png,.jpg,.jpeg,.gif,.mp4,.mp3";

export default function GuestUpload() {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef();

  function onDrop(e) {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if (f) setFile(f);
  }

  async function analyze() {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    const fd = new FormData(); fd.append("file", file);
    try {
      const res = await fetch(`${BASE}/projects/guest-analyze`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 24px" }}>
      <div style={{ width: "100%", maxWidth: 680 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
          <div>
            <h1 style={{ marginBottom: 4 }}>Guest Analysis</h1>
            <p className="text-muted">Upload a project to see its analysis. Nothing is saved.</p>
          </div>
          <a href="/" className="btn-secondary" style={{ padding: "0.6em 1.2em", textDecoration: "none", borderRadius: 8 }}>Sign In</a>
        </div>

        {error && <div className="alert error" style={{ marginBottom: 16 }}>{error}</div>}

        <div className="card" style={{ marginBottom: 24 }}>
          <div
            style={{
              border: "2px dashed var(--border)", borderRadius: 8, padding: 40,
              textAlign: "center", cursor: "pointer",
              background: dragging ? "var(--bg-secondary)" : "transparent",
              opacity: loading ? 0.5 : 1,
            }}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => !loading && fileRef.current.click()}
          >
            <input ref={fileRef} type="file" accept={ACCEPTED} style={{ display: "none" }} onChange={e => setFile(e.target.files[0])} />
            {file ? (
              <>
                <div style={{ fontSize: 32, marginBottom: 8 }}>📦</div>
                <p style={{ fontWeight: 600 }}>{file.name}</p>
                <p className="text-muted" style={{ fontSize: "0.85rem" }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </>
            ) : (
              <>
                <div style={{ fontSize: 32, marginBottom: 8 }}>⬆</div>
                <p>Drag & drop a file or click to browse</p>
                <p className="text-muted" style={{ fontSize: "0.8rem", marginTop: 4 }}>ZIP, code files, documents, images, or media</p>
              </>
            )}
          </div>
          {file && (
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn-primary" onClick={analyze} disabled={loading} style={{ flex: 1 }}>
                {loading ? "Analysing…" : "Analyse Now"}
              </button>
              <button className="btn-secondary" onClick={() => { setFile(null); setResult(null); }}>Remove</button>
            </div>
          )}
        </div>

        {result && result.status === "analyzed" && (
          <div className="card">
            <h2 style={{ marginBottom: 4 }}>{result.name || "Project"}</h2>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
              {result.project_type && <span className="tag">{result.project_type}</span>}
              {result.importance_score > 0 && <span className="tag accent">Score: {result.importance_score}</span>}
            </div>

            {result.description && <p style={{ marginBottom: 16, lineHeight: 1.6 }}>{result.description}</p>}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12, marginBottom: 16 }}>
              {[
                ["Files", result.file_count],
                ["Lines of Code", result.lines_of_code?.toLocaleString()],
              ].filter(([, v]) => v).map(([label, val]) => (
                <div key={label} className="card" style={{ padding: 14, textAlign: "center" }}>
                  <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{val}</div>
                  <div className="text-muted" style={{ fontSize: "0.8rem" }}>{label}</div>
                </div>
              ))}
            </div>

            {result.languages?.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <p className="text-muted" style={{ fontSize: "0.8rem", marginBottom: 6 }}>Languages</p>
                <div className="chip-group">{result.languages.map((l, i) => <span key={i} className="tag accent">{l}</span>)}</div>
              </div>
            )}
            {result.skills?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <p className="text-muted" style={{ fontSize: "0.8rem", marginBottom: 6 }}>Skills</p>
                <div className="chip-group">{result.skills.slice(0, 10).map((s, i) => <span key={i} className="tag">{s}</span>)}</div>
              </div>
            )}

            <div style={{ borderTop: "1px solid var(--border)", paddingTop: 16, marginTop: 4 }}>
              <p className="text-muted" style={{ marginBottom: 12, fontSize: "0.9rem" }}>
                Create a free account to save projects, build a portfolio, and track your skills over time.
              </p>
              <a href="/" className="btn-primary" style={{ display: "inline-block", padding: "0.6em 1.2em", textDecoration: "none", borderRadius: 8 }}>
                Create Account
              </a>
            </div>
          </div>
        )}

        {result && result.status !== "analyzed" && (
          <div className="alert error">{result.detail || "Could not analyse this file."}</div>
        )}
      </div>
    </div>
  );
}
