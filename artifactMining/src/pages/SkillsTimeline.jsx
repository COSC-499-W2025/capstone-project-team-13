import React, { useEffect, useState } from "react";
import { apiFetch } from "../apiClient";

// Assign a consistent colour to each skill based on its name
const COLOURS = ["#a5b4fc","#f9a8d4","#6ee7b7","#fcd34d","#7dd3fc","#c4b5fd","#86efac","#fdba74","#67e8f9","#d4d4d8"];
function skillColour(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) & 0xffffffff;
  return COLOURS[Math.abs(h) % COLOURS.length];
}

function parseDate(s) { return s ? new Date(s) : null; }
function fmtDate(s) {
  const d = parseDate(s);
  return d ? d.toLocaleDateString("en-CA", { year: "numeric", month: "short" }) : "?";
}

// Map a date value to a 0–100 percentage along the timeline axis
function pct(d, minMs, spanMs) {
  if (!d || !spanMs) return 0;
  return Math.max(0, Math.min(100, ((d.getTime() - minMs) / spanMs) * 100));
}

export default function SkillsTimeline() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("");
  const [minProjects, setMinProjects] = useState(1);

  useEffect(() => {
    apiFetch("/skills/timeline")
      .then(d => { setSkills(d.skills || []); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <p style={{ color: "var(--text-muted)", padding: 16 }}>Loading skills timeline…</p>;
  if (error)   return <p style={{ color: "#f87171", padding: 16 }}>Failed to load: {error}</p>;

  const visible = skills.filter(s =>
    s.first_seen &&
    s.project_count >= minProjects &&
    s.name.toLowerCase().includes(filter.toLowerCase())
  );

  if (visible.length === 0)
    return (
      <div style={{ padding: 16 }}>
        <Controls filter={filter} setFilter={setFilter} minProjects={minProjects} setMinProjects={setMinProjects} />
        <p style={{ color: "var(--text-muted)", marginTop: 12 }}>No skills match the current filters.</p>
      </div>
    );

  const allDates = visible.flatMap(s => [parseDate(s.first_seen), parseDate(s.last_seen)]).filter(Boolean);
  const minMs   = Math.min(...allDates.map(d => d.getTime()));
  const maxMs   = Math.max(...allDates.map(d => d.getTime()));
  const spanMs  = maxMs - minMs || 1;

  // Build year tick marks
  const minYear = new Date(minMs).getFullYear();
  const maxYear = new Date(maxMs).getFullYear();
  const ticks = [];
  for (let y = minYear; y <= maxYear; y++) {
    const p = pct(new Date(y, 0, 1), minMs, spanMs);
    if (p >= 0 && p <= 100) ticks.push({ year: y, p });
  }

  return (
    <div data-testid="skills-timeline">
      <Controls filter={filter} setFilter={setFilter} minProjects={minProjects} setMinProjects={setMinProjects} />

      {/* Year axis */}
      <div style={{ position: "relative", height: 24, marginBottom: 4 }}>
        {ticks.map(t => (
          <span key={t.year} style={{
            position: "absolute", left: `${t.p}%`, transform: "translateX(-50%)",
            fontSize: "0.7rem", color: "var(--text-muted)", userSelect: "none",
          }}>{t.year}</span>
        ))}
      </div>

      {/* Grid lines */}
      <div style={{ position: "relative" }}>
        {ticks.map(t => (
          <div key={t.year} style={{
            position: "absolute", left: `${t.p}%`, top: 0, bottom: 0,
            width: 1, background: "rgba(107,114,244,0.12)", pointerEvents: "none",
          }} />
        ))}

        {/* Skill rows */}
        {visible.map(skill => {
          const start = parseDate(skill.first_seen);
          const end   = parseDate(skill.last_seen) || start;
          const left  = pct(start, minMs, spanMs);
          const right = pct(end,   minMs, spanMs);
          const width = Math.max(right - left, 0.5);
          const colour = skillColour(skill.name);

          return (
            <div key={skill.name} data-testid="skill-row"
              style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              {/* Label */}
              <div style={{ width: 130, flexShrink: 0, fontSize: "0.78rem",
                color: "var(--text)", textAlign: "right", whiteSpace: "nowrap",
                overflow: "hidden", textOverflow: "ellipsis" }}
                title={skill.name}>
                {skill.name}
              </div>

              {/* Bar track */}
              <div style={{ flex: 1, position: "relative", height: 18, background: "rgba(255,255,255,0.04)", borderRadius: 4 }}>
                <div
                  title={`${fmtDate(skill.first_seen)} → ${fmtDate(skill.last_seen)} · ${skill.project_count} project${skill.project_count !== 1 ? "s" : ""}`}
                  style={{
                    position: "absolute",
                    left: `${left}%`, width: `${width}%`,
                    height: "100%", borderRadius: 4,
                    background: colour, opacity: 0.85,
                    cursor: "default", transition: "opacity 0.15s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.opacity = "1"}
                  onMouseLeave={e => e.currentTarget.style.opacity = "0.85"}
                />
              </div>

              {/* Project count badge */}
              <div style={{ width: 28, flexShrink: 0, fontSize: "0.68rem",
                color: colour, fontWeight: 700, textAlign: "left" }}>
                ×{skill.project_count}
              </div>
            </div>
          );
        })}
      </div>

      <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 10 }}>
        Hover a bar for date range. Showing {visible.length} skill{visible.length !== 1 ? "s" : ""}.
      </p>
    </div>
  );
}

function Controls({ filter, setFilter, minProjects, setMinProjects }) {
  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
      <input
        data-testid="filter-input"
        placeholder="Filter skills…"
        value={filter}
        onChange={e => setFilter(e.target.value)}
        style={{ padding: "5px 10px", fontSize: "0.82rem", width: 160 }}
      />
      <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 6 }}>
        Min projects:
        <select
          data-testid="min-projects-select"
          value={minProjects}
          onChange={e => setMinProjects(Number(e.target.value))}
          style={{ width: "auto", padding: "4px 8px", fontSize: "0.8rem" }}>
          {[1, 2, 3, 5].map(n => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>
    </div>
  );
}
