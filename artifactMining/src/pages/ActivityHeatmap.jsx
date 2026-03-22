import React, { useEffect, useState, useMemo } from "react";
import { apiFetch } from "../apiClient";

const CELL = 13;   // px per day cell
const GAP  = 2;    // px gap
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DAYS   = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

function startOfWeek(d) {
  const c = new Date(d);
  c.setDate(c.getDate() - c.getDay());
  return c;
}
function addDays(d, n) {
  const c = new Date(d);
  c.setDate(c.getDate() + n);
  return c;
}
function toKey(d) { return d.toISOString().slice(0, 10); }

// Interpolate between two hex colours by intensity 0–1
function heatColour(intensity) {
  if (intensity <= 0) return "rgba(255,255,255,0.04)";
  const stops = [
    [0.001, [59, 64, 120]],
    [0.25,  [99, 102, 241]],
    [0.6,   [139, 92, 246]],
    [1.0,   [196, 73, 255]],
  ];
  let lo = stops[0], hi = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (intensity >= stops[i][0] && intensity <= stops[i+1][0]) { lo = stops[i]; hi = stops[i+1]; break; }
  }
  const t = hi[0] === lo[0] ? 1 : (intensity - lo[0]) / (hi[0] - lo[0]);
  const r = Math.round(lo[1][0] + t * (hi[1][0] - lo[1][0]));
  const g = Math.round(lo[1][1] + t * (hi[1][1] - lo[1][1]));
  const b = Math.round(lo[1][2] + t * (hi[1][2] - lo[1][2]));
  return `rgb(${r},${g},${b})`;
}

// Build a map of { "YYYY-MM-DD": count } from project date ranges
function buildActivityMap(projects) {
  const map = {};
  for (const p of projects) {
    const start = p.date_created ? new Date(p.date_created) : null;
    const end   = p.date_modified ? new Date(p.date_modified) : start;
    if (!start) continue;
    // Mark the start date and end date as active days
    [start, end].forEach(d => {
      const k = toKey(d);
      map[k] = (map[k] || 0) + 1;
    });
  }
  return map;
}

export default function ActivityHeatmap() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [tooltip, setTooltip]   = useState(null);  // { x, y, text }
  const [yearOffset, setYearOffset] = useState(0); // 0 = current year, -1 = last year, etc.

  useEffect(() => {
    apiFetch("/projects")
      .then(d => { setProjects(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const { weeks, activityMap, maxCount, year } = useMemo(() => {
    const now = new Date();
    const targetYear = now.getFullYear() + yearOffset;
    const year = targetYear;

    const activityMap = buildActivityMap(projects);

    // Generate all weeks that overlap with targetYear
    const janFirst = new Date(targetYear, 0, 1);
    const decLast  = new Date(targetYear, 11, 31);
    const gridStart = startOfWeek(janFirst);
    const gridEnd   = startOfWeek(decLast);

    const weeks = [];
    let cur = new Date(gridStart);
    while (cur <= gridEnd) {
      const week = [];
      for (let d = 0; d < 7; d++) {
        const day = addDays(cur, d);
        week.push({ date: new Date(day), key: toKey(day), inYear: day.getFullYear() === targetYear });
      }
      weeks.push(week);
      cur = addDays(cur, 7);
    }

    const maxCount = Math.max(1, ...Object.values(activityMap));
    return { weeks, activityMap, maxCount, year };
  }, [projects, yearOffset]);

  if (loading) return <p style={{ color: "#9aa6de", padding: 16 }}>Loading activity heatmap…</p>;
  if (error)   return <p style={{ color: "#f87171", padding: 16 }}>Failed to load: {error}</p>;

  const totalActive = Object.keys(activityMap).filter(k => k.startsWith(String(year))).length;
  const totalProjects = projects.filter(p => {
    const y = p.date_created ? new Date(p.date_created).getFullYear() : null;
    return y === year;
  }).length;

  // Month label positions (which week index does each month start?)
  const monthLabels = [];
  weeks.forEach((week, wi) => {
    const first = week.find(d => d.inYear);
    if (!first) return;
    if (first.date.getDate() <= 7) {
      const m = first.date.getMonth();
      if (!monthLabels.find(l => l.month === m))
        monthLabels.push({ month: m, wi });
    }
  });

  return (
    <div data-testid="activity-heatmap" style={{ position: "relative" }}>
      {/* Year nav */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
        <button
          data-testid="prev-year"
          onClick={() => setYearOffset(o => o - 1)}
          style={{ background: "none", border: "1px solid rgba(107,114,244,0.3)",
            color: "#9aa6de", borderRadius: 6, padding: "3px 10px", cursor: "pointer" }}>‹</button>
        <span style={{ fontWeight: 700, color: "#c4c9f0", fontSize: "0.95rem" }}>{year}</span>
        <button
          data-testid="next-year"
          onClick={() => setYearOffset(o => o + 1)}
          disabled={yearOffset >= 0}
          style={{ background: "none", border: "1px solid rgba(107,114,244,0.3)",
            color: yearOffset >= 0 ? "#4a5196" : "#9aa6de",
            borderRadius: 6, padding: "3px 10px", cursor: yearOffset >= 0 ? "default" : "pointer" }}>›</button>
        <span style={{ fontSize: "0.78rem", color: "#7b87c4" }}>
          {totalActive} active day{totalActive !== 1 ? "s" : ""} · {totalProjects} project{totalProjects !== 1 ? "s" : ""}
        </span>
      </div>

      <div style={{ display: "flex", gap: 4 }}>
        {/* Day-of-week labels */}
        <div style={{ display: "flex", flexDirection: "column", gap: GAP, paddingTop: 20 }}>
          {DAYS.map((d, i) => (
            <div key={d} style={{ height: CELL, fontSize: "0.6rem", color: "#7b87c4",
              lineHeight: `${CELL}px`, visibility: i % 2 === 1 ? "visible" : "hidden" }}>
              {d}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div style={{ overflowX: "auto", flex: 1 }}>
          {/* Month labels */}
          <div style={{ display: "flex", gap: GAP, marginBottom: 4, paddingLeft: 0 }}>
            {weeks.map((_, wi) => {
              const label = monthLabels.find(l => l.wi === wi);
              return (
                <div key={wi} style={{ width: CELL, flexShrink: 0, fontSize: "0.6rem",
                  color: "#7b87c4", whiteSpace: "nowrap" }}>
                  {label ? MONTHS[label.month] : ""}
                </div>
              );
            })}
          </div>

          {/* Cells */}
          <div style={{ display: "flex", gap: GAP }}>
            {weeks.map((week, wi) => (
              <div key={wi} style={{ display: "flex", flexDirection: "column", gap: GAP }}>
                {week.map(({ date, key, inYear }) => {
                  const count = activityMap[key] || 0;
                  const intensity = count / maxCount;
                  const colour = inYear ? heatColour(intensity) : "transparent";
                  return (
                    <div
                      key={key}
                      data-testid="heatmap-cell"
                      data-date={key}
                      data-count={count}
                      style={{
                        width: CELL, height: CELL, borderRadius: 3,
                        background: colour, cursor: count > 0 ? "pointer" : "default",
                        border: inYear ? "1px solid rgba(255,255,255,0.04)" : "none",
                        boxSizing: "border-box",
                      }}
                      onMouseEnter={e => {
                        if (!inYear) return;
                        const label = count > 0
                          ? `${key}: ${count} project activity`
                          : `${key}: no activity`;
                        setTooltip({ x: e.clientX, y: e.clientY, text: label });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 8, justifyContent: "flex-end" }}>
        <span style={{ fontSize: "0.68rem", color: "#7b87c4" }}>Less</span>
        {[0, 0.25, 0.5, 0.75, 1].map(i => (
          <div key={i} style={{ width: CELL, height: CELL, borderRadius: 3, background: heatColour(i) }} />
        ))}
        <span style={{ fontSize: "0.68rem", color: "#7b87c4" }}>More</span>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: "fixed", left: tooltip.x + 10, top: tooltip.y - 28, zIndex: 999,
          background: "#1e2044", border: "1px solid rgba(107,114,244,0.4)",
          borderRadius: 6, padding: "4px 10px", fontSize: "0.75rem", color: "#eef1ff",
          pointerEvents: "none", whiteSpace: "nowrap",
        }}>{tooltip.text}</div>
      )}
    </div>
  );
}
