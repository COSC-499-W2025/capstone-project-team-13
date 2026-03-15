import React, { useState } from "react";

const VIEWS = [
  { id: "skill-frequency", label: "Skill Frequency" },
  { id: "project-types", label: "By Project Type" },
];

const STAND_IN_SKILL_DATA = [
  { name: "JavaScript", value: 8 },
  { name: "Python", value: 6 },
  { name: "React", value: 5 },
  { name: "SQL", value: 3 },
];

const STAND_IN_TYPE_DATA = [
  { label: "Code", value: 50, color: "#3b82f6" },
  { label: "Text", value: 30, color: "#8b5cf6" },
  { label: "Media", value: 20, color: "#06b6d4" },
];

function StandInBarChart() {
  const max = Math.max(...STAND_IN_SKILL_DATA.map((item) => item.value));

  return (
    <div className="standin-bars" aria-label="Skill frequency stand-in chart">
      {STAND_IN_SKILL_DATA.map((item) => (
        <div key={item.name} className="standin-row">
          <span className="standin-label">{item.name}</span>
          <div className="standin-track">
            <div className="standin-fill" style={{ width: `${(item.value / max) * 100}%` }} />
          </div>
          <span className="standin-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

function StandInPieChart() {
  const gradient = STAND_IN_TYPE_DATA.map((slice, index) => {
    const start = STAND_IN_TYPE_DATA
      .slice(0, index)
      .reduce((sum, current) => sum + current.value, 0);
    const end = start + slice.value;
    return `${slice.color} ${start}% ${end}%`;
  }).join(", ");

  return (
    <div className="standin-pie-wrap" aria-label="Project type stand-in chart">
      <div className="standin-pie" style={{ background: `conic-gradient(${gradient})` }} />
      <div className="standin-legend">
        {STAND_IN_TYPE_DATA.map((slice) => (
          <div key={slice.label} className="standin-legend-item">
            <span className="standin-dot" style={{ backgroundColor: slice.color }} />
            <span>{slice.label}</span>
            <strong>{slice.value}%</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function InsightsChart() {
  const [activeView, setActiveView] = useState(VIEWS[0].id);

  return (
    <div className="insights-chart-container">
      <div className="insights-toggle-bar">
        {VIEWS.map((view) => (
          <button
            key={view.id}
            type="button"
            className={`insights-toggle-btn${activeView === view.id ? " active" : ""}`}
            onClick={() => setActiveView(view.id)}
          >
            {view.label}
          </button>
        ))}
      </div>

      <div className="insights-chart-area">
        {activeView === "skill-frequency" ? <StandInBarChart /> : <StandInPieChart />}
      </div>
    </div>
  );
}
