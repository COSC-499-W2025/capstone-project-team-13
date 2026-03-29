import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./Portfolio.css";

export default function WebShowcase() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    apiFetch("/portfolio/showcase")
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-wrap"><div className="spinner" style={{ marginTop: 60 }} /></div>;
  if (error) return <div className="page-wrap"><div className="alert error">{error}</div></div>;

  const projects = data?.projects || [];

  return (
    <div className="page-wrap">
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 6 }}>
          <button
            onClick={() => nav(-1)}
            className="showcase-back-btn"
            title="Go back"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/>
            </svg>
            Back
          </button>
          <h1 style={{ margin: 0 }}>Web Portfolio Showcase</h1>
        </div>
        <p className="text-muted">Top 3 projects ranked by importance, illustrating your process and evolution.</p>
      </div>

      {projects.length === 0 ? (
        <div className="empty-state">
          <p>No projects yet. Upload and generate your portfolio first.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
          {projects.map((p, idx) => (
            <ShowcaseCard key={p.id} project={p} rank={idx + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function ShowcaseCard({ project: p, rank }) {
  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      {/* Header band */}
      <div style={{ background: "var(--bg-secondary)", padding: "20px 28px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--accent)" }}>#{rank}</span>
            <h2 style={{ margin: 0 }}>{p.name || "Untitled"}</h2>
            {p.is_featured && <span className="tag success">Featured</span>}
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {p.project_type && <span className="tag">{p.project_type}</span>}
            {p.user_role && <span className="tag accent">{p.user_role}</span>}
            {p.importance_score > 0 && <span className="tag">Score: {p.importance_score}</span>}
          </div>
        </div>
        {(p.date_start || p.date_end) && (
          <div style={{ textAlign: "right" }}>
            <p className="text-muted" style={{ fontSize: "0.8rem", marginBottom: 2 }}>Timeline</p>
            <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>
              {p.date_start || "?"} {p.date_end && p.date_end !== p.date_start ? `→ ${p.date_end}` : ""}
            </p>
          </div>
        )}
      </div>

      <div style={{ padding: "24px 28px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28 }}>
        {/* Left: description + tech */}
        <div>
          {p.description && <p style={{ marginBottom: 16, lineHeight: 1.7 }}>{p.description}</p>}
          {p.success_evidence && (
            <div style={{ background: "var(--bg-secondary)", borderRadius: 6, padding: "10px 14px", marginBottom: 16, fontSize: "0.85rem" }}>
              <strong style={{ color: "var(--accent)" }}>Evidence: </strong>{p.success_evidence}
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
            {[["Files", p.file_count], ["LOC", p.lines_of_code?.toLocaleString()]].filter(([, v]) => v).map(([label, val]) => (
              <div key={label} className="card" style={{ padding: "10px 14px", textAlign: "center" }}>
                <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>{val}</div>
                <div className="text-muted" style={{ fontSize: "0.75rem" }}>{label}</div>
              </div>
            ))}
          </div>

          {p.languages?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <p className="text-muted" style={{ fontSize: "0.75rem", marginBottom: 5 }}>Languages</p>
              <div className="chip-group">{p.languages.map((l, i) => <span key={i} className="tag accent">{l}</span>)}</div>
            </div>
          )}
          {p.skills?.length > 0 && (
            <div>
              <p className="text-muted" style={{ fontSize: "0.75rem", marginBottom: 5 }}>Skills</p>
              <div className="chip-group">{p.skills.slice(0, 8).map((s, i) => <span key={i} className="tag">{s}</span>)}</div>
            </div>
          )}
        </div>

        {/* Right: evolution timeline */}
        <div>
          <h3 style={{ marginBottom: 16, fontSize: "0.95rem", color: "var(--text-muted)" }}>Evolution of Changes</h3>
          {p.evolution?.length > 0 ? (
            <div style={{ position: "relative", paddingLeft: 20 }}>
              {/* Vertical line */}
              <div style={{ position: "absolute", left: 6, top: 8, bottom: 8, width: 2, background: "var(--border)" }} />
              {p.evolution.map((step, i) => (
                <div key={i} style={{ position: "relative", marginBottom: i < p.evolution.length - 1 ? 20 : 0, paddingLeft: 20 }}>
                  {/* Dot */}
                  <div style={{
                    position: "absolute", left: -8, top: 4, width: 10, height: 10,
                    borderRadius: "50%", background: i === 0 || i === p.evolution.length - 1 ? "var(--accent)" : "var(--border)",
                    border: "2px solid var(--accent)"
                  }} />
                  <p style={{ margin: 0, fontWeight: 500, fontSize: "0.9rem" }}>{step.label}</p>
                  {step.date && <p className="text-muted" style={{ margin: 0, fontSize: "0.78rem" }}>{step.date}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted" style={{ fontSize: "0.85rem" }}>No evolution data available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
