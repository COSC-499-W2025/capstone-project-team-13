/**
 * PortfolioShared.jsx
 * Shared helpers and read-only display components used by both
 * Portfolio.jsx (owner view) and PublicPortfolios.jsx (visitor view).
 */

import React, { useEffect, useRef, useState } from "react";
import { apiFetch, projectName } from "../apiClient";

const API_BASE = "http://127.0.0.1:8000";

// ── Colour helpers ────────────────────────────────────────────────────────────

export const TYPE_COLORS = {
  python:     "#3b82f6", javascript: "#f59e0b", typescript: "#6366f1",
  java:       "#ef4444", web:        "#10b981", mobile:     "#8b5cf6",
  ml:         "#ec4899", data:       "#14b8a6", default:    "#6366f1",
};

export function typeColor(type) {
  const t = (type || "").toLowerCase();
  for (const [key, col] of Object.entries(TYPE_COLORS)) if (t.includes(key)) return col;
  return TYPE_COLORS.default;
}

export function thumbUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  const filename = path.split(/[/\\]/).pop();
  return `${API_BASE}/uploads/${filename}`;
}

// ── Entry-type classifiers ────────────────────────────────────────────────────

export function educationEntryTypeOf(entry) {
  const degreeType = (entry?.degree_type || "").trim();
  const topic = (entry?.topic || "").trim();
  if (degreeType === "Certification") return "certifications";
  if (degreeType === "Extra Curricular") return "extracurricular";
  if (degreeType === "Secondary School Diploma" || topic === "General Studies") return "secondary";
  return "postsecondary";
}

export function experienceTypeOf(entry) {
  const explicit = (entry?.experience_type || "").toLowerCase().trim();
  if (["work", "internship", "volunteering", "freelance"].includes(explicit)) return explicit;
  const combined = `${(entry?.company || "").toLowerCase()} ${(entry?.role || "").toLowerCase()}`;
  if (combined.includes("intern")) return "internship";
  if (combined.includes("volunteer")) return "volunteering";
  if (combined.includes("freelance") || combined.includes("contract") || combined.includes("self-employed")) return "freelance";
  return "work";
}

// ── EvidenceSection ───────────────────────────────────────────────────────────

export function EvidenceSection({ p }) {
  const ev = p.success_evidence;
  if (!ev) return null;

  let data = null;
  try { data = JSON.parse(ev); } catch (_) {}

  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return <p className="port-evidence">{ev}</p>;
  }

  const chips = [];
  if (data.manual_metrics && typeof data.manual_metrics === "object") {
    Object.entries(data.manual_metrics).forEach(([k, v]) =>
      chips.push({ label: k.replace(/_/g, " "), value: v.value ?? v })
    );
  }
  if (data.test_coverage != null) chips.push({ label: "coverage", value: `${data.test_coverage}%` });
  if (Array.isArray(data.achievements) && data.achievements.length > 0)
    chips.push({ label: "achievements", value: data.achievements.length });
  if (Array.isArray(data.feedback) && data.feedback.length > 0)
    chips.push({ label: "feedback", value: data.feedback.length });
  if (Array.isArray(data.readme_badges) && data.readme_badges.length > 0)
    chips.push({ label: "badges", value: data.readme_badges.length });

  const skip = new Set(["manual_metrics", "test_coverage", "achievements", "feedback", "readme_badges"]);
  Object.entries(data).forEach(([k, v]) => {
    if (skip.has(k) || typeof v === "object") return;
    chips.push({ label: k.replace(/_/g, " "), value: v });
  });

  if (chips.length === 0) return null;

  return (
    <div className="port-evidence-chips">
      {chips.map((c, i) => (
        <span key={i} className="port-evidence-chip">
          <span className="port-evidence-chip-label">{c.label}</span>
          <span className="port-evidence-chip-val">{c.value}</span>
        </span>
      ))}
    </div>
  );
}

// ── ContactField ──────────────────────────────────────────────────────────────

export function ContactField({ label, value, isPublic, type = "text", placeholder, href, onChange }) {
  if (isPublic) {
    if (!value) return null;
    return (
      <div className="port-contact-field">
        <span className="port-contact-field-label">{label}</span>
        {href ? (
          <a
            className="port-contact-link"
            href={href}
            target={href.startsWith("mailto:") || href.startsWith("tel:") ? undefined : "_blank"}
            rel={href.startsWith("mailto:") || href.startsWith("tel:") ? undefined : "noreferrer"}
          >
            {value}
          </a>
        ) : (
          <p className="port-contact-value">{value}</p>
        )}
      </div>
    );
  }

  return (
    <label className="port-contact-field">
      <span className="port-contact-field-label">{label}</span>
      <input
        className="port-contact-input"
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
      />
    </label>
  );
}

// ── CustomPresenceField ───────────────────────────────────────────────────────

export function CustomPresenceField({ item, isPublic, onChange, onRemove }) {
  if (isPublic) {
    if (!item.url) return null;
    return (
      <div className="port-contact-field">
        <span className="port-contact-field-label">{item.label || "Online Presence"}</span>
        <a className="port-contact-link" href={item.url} target="_blank" rel="noreferrer">
          {item.url}
        </a>
      </div>
    );
  }

  return (
    <div className="port-contact-custom-row">
      <div className="port-contact-custom-inputs">
        <label className="port-contact-field">
          <span className="port-contact-field-label">Title</span>
          <input
            className="port-contact-input"
            type="text"
            placeholder="e.g. Behance"
            value={item.label}
            onChange={e => onChange("label", e.target.value)}
          />
        </label>
        <label className="port-contact-field">
          <span className="port-contact-field-label">Link</span>
          <input
            className="port-contact-input"
            type="url"
            placeholder="https://example.com/profile"
            value={item.url}
            onChange={e => onChange("url", e.target.value)}
          />
        </label>
      </div>
      <button className="port-contact-remove-btn" type="button" onClick={onRemove} title="Remove online presence">
        Remove
      </button>
    </div>
  );
}

// ── EditForm (owner-only) ─────────────────────────────────────────────────────

export function EditForm({ p, editForm, setEditForm, saveEdit, setEditId }) {
  return (
    <div className="port-inline-edit">
      <div className="port-edit-grid">
        <label>Description<textarea rows={3} value={editForm.custom_description} onChange={e => setEditForm({ ...editForm, custom_description: e.target.value })} /></label>
        <label>Your Role<input value={editForm.user_role} onChange={e => setEditForm({ ...editForm, user_role: e.target.value })} placeholder="Lead Developer, Designer…" /></label>
        <label>Success Evidence<textarea rows={2} value={editForm.success_evidence} onChange={e => setEditForm({ ...editForm, success_evidence: e.target.value })} placeholder="Metrics, feedback, grades…" /></label>
        <label>Importance Score (0–1)<input type="number" min="0" max="1" step="0.01" value={editForm.importance_score} onChange={e => setEditForm({ ...editForm, importance_score: e.target.value })} /></label>
        <label>Languages (comma-sep)<input value={editForm.languages} onChange={e => setEditForm({ ...editForm, languages: e.target.value })} /></label>
        <label>Frameworks (comma-sep)<input value={editForm.frameworks} onChange={e => setEditForm({ ...editForm, frameworks: e.target.value })} /></label>
        <label>Skills (comma-sep)<input value={editForm.skills} onChange={e => setEditForm({ ...editForm, skills: e.target.value })} /></label>
        <label>Tags (comma-sep)<input value={editForm.tags} onChange={e => setEditForm({ ...editForm, tags: e.target.value })} /></label>
      </div>
      <div className="port-edit-checks">
        <label><input type="checkbox" checked={editForm.is_featured} onChange={e => setEditForm({ ...editForm, is_featured: e.target.checked })} /> Featured</label>
        <label><input type="checkbox" checked={editForm.is_hidden} onChange={e => setEditForm({ ...editForm, is_hidden: e.target.checked })} /> Hidden</label>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button className="btn-primary" onClick={() => saveEdit(p.id)}>Save</button>
        <button className="btn-secondary" onClick={() => setEditId(null)}>Cancel</button>
      </div>
    </div>
  );
}

// ── ProjectCard ───────────────────────────────────────────────────────────────

export function ProjectCard({ p, rank, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav, isPublic, toggleHidden }) {
  const accent = typeColor(p.type || p.project_type);
  const thumb = thumbUrl(p.thumbnail_path);
  return (
    <div className={`port-top-card card${p.is_featured ? " port-featured-card" : ""}`} style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="port-rank">#{rank}</div>
      <div className="port-card-tags">
        <span className="tag">{p.type || p.project_type}</span>
        {p.is_featured && <span className="port-featured-badge">★ Featured</span>}
        {p.is_hidden && !isPublic && <span className="tag warning">hidden</span>}
      </div>
      <div className="port-card-thumb-wrapper">
        <img
          src={thumb}
          alt="thumbnail"
          className="port-card-thumb"
          style={{ display: thumb ? "block" : "none" }}
          onError={e => { e.target.style.display = "none"; e.target.parentNode.querySelector(".port-card-thumb-placeholder").style.display = "flex"; }}
        />
        <div className="port-card-thumb-placeholder" style={{ display: thumb ? "none" : "flex", background: `linear-gradient(135deg, ${accent}22 0%, ${accent}44 100%)`, borderColor: `${accent}44` }}>
          {(projectName(p) || "?")[0].toUpperCase()}
        </div>
        {thumb && <div className="port-card-thumb-overlay" />}
      </div>
      <h3 className="port-proj-name">{projectName(p)}</h3>
      <p className="port-proj-desc text-muted">{p.description || "No description"}</p>
      {p.user_role && <p style={{ fontSize: "0.8rem", color: "#a5b4fc", marginTop: 4 }}>Role: {p.user_role}</p>}
      <EvidenceSection p={p} />
      <div className="chip-group" style={{ marginTop: 8 }}>
        {[...new Set([...(p.skills || []), ...(p.tech_stack || p.languages || [])])].slice(0, 6).map((t, i) => {
          const tc = typeColor(t);
          return <span key={i} className="tag accent" style={{ color: tc, borderColor: `${tc}55`, background: `${tc}18` }}>{t}</span>;
        })}
      </div>
      {p.importance_score != null && (
        <div className="port-score-track">
          <div className="port-score-track-inner">
            <div className="port-score-fill" style={{ width: `${Math.round((p.importance_score || 0) * 100)}%`, background: accent }} />
          </div>
          <span className="port-score-label">{Number(p.importance_score).toFixed(2)}</span>
        </div>
      )}
      {p.metrics && (
        <div className="port-metrics">
          {p.metrics.lines_of_code > 0 && <span>{p.metrics.lines_of_code?.toLocaleString()} lines</span>}
          {p.metrics.file_count > 0 && <span>{p.metrics.file_count} files</span>}
        </div>
      )}
      {!isPublic && (
        <div className="port-rank-row">
          <input type="number" min="0" max="1" step="0.01" placeholder="Score 0–1"
            value={rankInput[p.id] ?? p.importance_score ?? ""}
            onChange={e => setRankInput({ ...rankInput, [p.id]: e.target.value })}
            style={{ width: 100, padding: "5px 8px" }} />
          <button className="btn-secondary" style={{ padding: "5px 10px", fontSize: "0.8rem" }} onClick={() => saveRank(p.id)}>Set</button>
        </div>
      )}
      <div className="port-card-actions">
        <button className="btn-secondary" onClick={() => nav(`/projects/${p.id}`)}>View</button>
        {!isPublic && (
          <button className="btn-secondary" onClick={() => editId === p.id ? setEditId(null) : startEdit(p)}>{editId === p.id ? "Cancel" : "Edit"}</button>
        )}
        {!isPublic && (
          <button className={`btn-secondary port-hide-btn${p.is_hidden ? " hidden-active" : ""}`} onClick={() => toggleHidden(p)} title={p.is_hidden ? "Show in portfolio" : "Hide from portfolio"}>
            {p.is_hidden ? "Unhide" : "Hide"}
          </button>
        )}
      </div>
      {!isPublic && editId === p.id && <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />}
    </div>
  );
}

// ── ProjectRow ────────────────────────────────────────────────────────────────

export function ProjectRow({ p, editId, editForm, setEditForm, startEdit, saveEdit, setEditId, rankInput, setRankInput, saveRank, nav, isPublic, toggleHidden }) {
  const accent = typeColor(p.type || p.project_type);
  const score = p.importance_score ?? 0;
  const thumb = thumbUrl(p.thumbnail_path);
  return (
    <div className="port-list-row card" style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="port-score-bar" style={{ background: accent, height: `${Math.round(score * 100)}%` }} />
      {thumb ? (
        <img src={thumb} alt="thumbnail" className="port-row-thumb" onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }} />
      ) : null}
      <div className="port-row-thumb-placeholder" style={{ display: thumb ? "none" : "flex" }}>
        {(projectName(p) || "?")[0].toUpperCase()}
      </div>
      <div className="port-list-main">
        <div className="port-list-top">
          <strong className="port-list-name">{projectName(p)}</strong>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            <span className="tag">{p.type || p.project_type}</span>
            {p.is_hidden && !isPublic && <span className="tag warning">hidden</span>}
            {p.importance_score != null && (
              <div className="port-row-score-wrap" title={`Score: ${Number(p.importance_score).toFixed(2)}`}>
                <div className="port-row-score-bar" style={{ width: `${Math.round((p.importance_score || 0) * 100)}%`, background: accent }} />
              </div>
            )}
          </div>
        </div>
        <div className="port-list-desc-fade">
          <p className="port-list-desc text-muted">{p.description || "No description"}</p>
        </div>
        {p.user_role && <p style={{ fontSize: "0.78rem", color: "#a5b4fc", marginTop: 2 }}>Role: {p.user_role}</p>}
        <EvidenceSection p={p} />
        <div className="chip-group" style={{ marginTop: 6 }}>
          {[...new Set([...(p.skills || []), ...(p.languages || p.tech_stack || [])])].slice(0, 8).map((t, i) => {
            const tc = typeColor(t);
            return <span key={i} className="tag accent" style={{ color: tc, borderColor: `${tc}55`, background: `${tc}18` }}>{t}</span>;
          })}
        </div>
      </div>
      <div className="port-list-actions">
        {!isPublic && (
          <div className="port-rank-row">
            <input type="number" min="0" max="1" step="0.01" placeholder="0–1"
              value={rankInput[p.id] ?? p.importance_score ?? ""}
              onChange={e => setRankInput({ ...rankInput, [p.id]: e.target.value })}
              style={{ width: 70, padding: "5px 6px", fontSize: "0.8rem" }} />
            <button className="btn-secondary" style={{ padding: "5px 8px", fontSize: "0.75rem" }} onClick={() => saveRank(p.id)}>Set</button>
          </div>
        )}
        <button className="btn-secondary" style={{ padding: "6px 12px" }} onClick={() => nav(`/projects/${p.id}`)}>View</button>
        {!isPublic && (
          <button className="btn-secondary" style={{ padding: "6px 12px" }} onClick={() => editId === p.id ? setEditId(null) : startEdit(p)}>{editId === p.id ? "Cancel" : "Edit"}</button>
        )}
        {!isPublic && (
          <button className={`btn-secondary port-hide-btn${p.is_hidden ? " hidden-active" : ""}`} style={{ padding: "6px 12px" }} onClick={() => toggleHidden(p)} title={p.is_hidden ? "Show in portfolio" : "Hide from portfolio"}>
            {p.is_hidden ? "Unhide" : "Hide"}
          </button>
        )}
      </div>
      {!isPublic && editId === p.id && (
        <div style={{ width: "100%", marginTop: 12 }}>
          <EditForm p={p} editForm={editForm} setEditForm={setEditForm} saveEdit={saveEdit} setEditId={setEditId} />
        </div>
      )}
    </div>
  );
}
