import React, { useEffect, useState } from "react";
import "./Resumes.css";

const API_BASE = "http://127.0.0.1:8000";
const UID = 1; // TODO: replace with auth context when multi-user login is wired up

function Resumes() {
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState({ msg: "", type: "" });
  const [awards, setAwards] = useState([]);
  const [awardInput, setAwardInput] = useState("");
  const [aiConsent, setAiConsent] = useState(false);

  useEffect(() => {
    checkAiConsent();
    loadResume();
  }, []);

  function showStatus(msg, type = "ok") {
    setStatus({ msg, type });
    setTimeout(() => setStatus({ msg: "", type: "" }), 4000);
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

  async function loadResume() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/resume/${UID}`);
      if (res.status === 404) {
        await generateResume();
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      applyResume(data.resume || data);
    } catch (e) {
      showStatus("Failed to load resume: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  async function generateResume() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/resume/generate?user_id=${UID}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      applyResume(data.resume || data);
      showStatus("Resume generated.");
    } catch (e) {
      showStatus("Generation failed: " + e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  function applyResume(data) {
    setResume(data);
    setAwards(data.awards || []);
  }

  async function saveAwards() {
    try {
      const res = await fetch(`${API_BASE}/resume/${UID}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ awards }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      applyResume(data.resume || data);
      showStatus("Awards saved.");
    } catch (e) {
      showStatus("Save failed: " + e.message, "err");
    }
  }

  function addAward() {
    const val = awardInput.trim();
    if (!val) return;
    setAwards((prev) => [...prev, val]);
    setAwardInput("");
  }

  function removeAward(idx) {
    setAwards((prev) => prev.filter((_, i) => i !== idx));
  }

  const skillsByLevel = resume?.skills_by_level || {};

  return (
    <div className="resume-shell">
      {/* ── Sidebar ── */}
      <aside className="resume-sidebar">
        <a className="resume-back" href="/">
          &lt; Dashboard
        </a>
        <h2>Resume Controls</h2>

        <button
          className="resume-btn resume-btn-primary"
          onClick={generateResume}
          disabled={loading}
        >
          {loading ? "Loading..." : "Generate / Refresh"}
        </button>

        <a
          className="resume-btn resume-btn-outline"
          href={`${API_BASE}/resume/${UID}/download/pdf`}
          target="_blank"
          rel="noreferrer"
        >
          Download PDF
        </a>

        <a
          className="resume-btn resume-btn-outline"
          href={`${API_BASE}/resume/${UID}/download/docx`}
          target="_blank"
          rel="noreferrer"
        >
          Download DOCX
        </a>

        <label className="resume-label">Education &amp; Awards</label>

        <div className="resume-award-row">
          <input
            className="resume-award-input"
            placeholder="Add award or degree..."
            value={awardInput}
            onChange={(e) => setAwardInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addAward()}
          />
          <button className="resume-btn-add" onClick={addAward}>
            +
          </button>
        </div>

        <ul className="resume-awards-list">
          {awards.map((a, i) => (
            <li key={i}>
              <span>{a}</span>
              <button onClick={() => removeAward(i)}>&times;</button>
            </li>
          ))}
        </ul>

        <button
          className="resume-btn resume-btn-secondary"
          onClick={saveAwards}
        >
          Save Awards
        </button>

        {!aiConsent && (
          <p className="resume-ai-hint">
            Enable AI consent in <a href="/settings">Settings</a> for
            AI-generated bullets.
          </p>
        )}

        {status.msg && (
          <div className={`resume-status resume-status-${status.type}`}>
            {status.msg}
          </div>
        )}
      </aside>

      {/* ── Main ── */}
      <main className="resume-main">
        {loading && (
          <div className="resume-loader">Building your resume...</div>
        )}

        {!loading && resume && (
          <div className="resume-doc">
            {/* Name / role / contact */}
            <div className="r-name">{resume.name || "Your Name"}</div>
            {resume.role && <div className="r-role">{resume.role}</div>}
            {resume.contact && (
              <div className="r-contact">{resume.contact}</div>
            )}
            <hr className="r-rule" />

            {/* Education & Awards */}
            <div className="r-section">
              <hr className="r-rule" />
              <h2>Education and Awards</h2>
              <hr className="r-rule" />
            </div>

            {(resume.education || []).map((edu, i) => (
              <div key={i}>
                <div className="edu-row">
                  <span className="edu-degree">{edu.degree}</span>
                  <span className="edu-dates">{edu.dates}</span>
                </div>
                <div className="edu-inst">{edu.institution}</div>
              </div>
            ))}

            {awards.map((a, i) => (
              <div key={i} className="award-item">
                {a}
              </div>
            ))}

            {/* Skills */}
            {Object.keys(skillsByLevel).some(
              (k) => skillsByLevel[k].length > 0
            ) && (
              <>
                <div className="r-section">
                  <hr className="r-rule" />
                  <h2>Skills</h2>
                  <hr className="r-rule" />
                </div>
                {Object.entries(skillsByLevel).map(
                  ([level, skills]) =>
                    skills.length > 0 && (
                      <div key={level} className="skill-row">
                        <strong>{level}:</strong>
                        <span className="skill-sep">|</span>
                        {skills.join(", ")}
                      </div>
                    )
                )}
              </>
            )}

            {/* Projects */}
            {(resume.projects || []).length > 0 && (
              <>
                <div className="r-section">
                  <hr className="r-rule" />
                  <h2>Projects</h2>
                  <hr className="r-rule" />
                </div>
                {resume.projects.map((p, i) => (
                  <div key={i} className="proj-item">
                    <div className="proj-name">{p.name}</div>
                    {p.header && (
                      <div className="proj-sub">{p.header}</div>
                    )}
                    {p.bullets && p.bullets.length > 0 ? (
                      <ul className="proj-bullets">
                        {p.bullets.map((b, bi) => (
                          <li key={bi}>{b}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="proj-no-bul">
                        {aiConsent
                          ? "No bullets yet — click Generate / Refresh to create AI bullets."
                          : "No bullets generated yet."}
                      </div>
                    )}
                    {p.ats_score != null && (
                      <div className="proj-ats">
                        ATS score: {Math.round(p.ats_score)}/100
                      </div>
                    )}
                  </div>
                ))}
              </>
            )}

            {!(resume.projects || []).length && !loading && (
              <p className="resume-empty">
                No projects found. Upload a project and generate your resume.
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default Resumes;