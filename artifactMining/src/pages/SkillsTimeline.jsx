import React, { useEffect, useState } from "react";
import "./SkillsTimeline.css";

const API_BASE = "http://localhost:8000";

function SkillsTimeline() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSkill, setSelectedSkill] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE}/skills/timeline`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch skills");
        return res.json();
      })
      .then((data) => {
        setSkills(data.skills || []);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load skills.");
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="st-page"><div className="st-panel">Loading skills...</div></div>;
  if (error) return <div className="st-page"><div className="st-panel st-error">{error}</div></div>;

  return (
    <div className="st-page">
      <div className="st-panel">
        <h2>Skills Timeline</h2>
        <p className="st-subtitle">Skills ranked by project usage</p>

        {skills.length === 0 ? (
          <p className="st-empty">No skills found. Upload a project to get started.</p>
        ) : (
          <div className="st-timeline">
            {skills.map((skill, index) => {
              const maxCount = Math.max(...skills.map((s) => s.count));
              const barWidth = Math.max(8, (skill.count / maxCount) * 100);
              const isSelected = selectedSkill?.name === skill.name;

              return (
                <div key={skill.name} className="st-row">
                  <div className="st-index">{index + 1}</div>
                  <div className="st-skill-name">{skill.name}</div>
                  <div className="st-bar-track">
                    <div
                      className="st-bar"
                      style={{ width: `${barWidth}%`, animationDelay: `${index * 60}ms` }}
                    />
                  </div>
                  <div className="st-count">
                    {skill.count} project{skill.count !== 1 ? "s" : ""}
                  </div>
                  <button
                    className={`st-toggle ${isSelected ? "st-toggle-active" : ""}`}
                    onClick={() => setSelectedSkill(isSelected ? null : skill)}
                  >
                    {isSelected ? "▲" : "▼"}
                  </button>

                  {isSelected && (
                    <div className="st-projects">
                      {skill.projects.map((p) => (
                        <div key={p.project_id} className="st-project-chip">
                          <span className="st-project-name">{p.project_name}</span>
                          {p.project_type && (
                            <span className="st-project-type">{p.project_type}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default SkillsTimeline;