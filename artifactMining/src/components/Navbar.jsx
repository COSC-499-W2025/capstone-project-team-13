import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

const mainLinks = [
  { to: "/", label: "Dashboard" },
  { to: "/upload", label: "Upload" },
  { to: "/projects", label: "Projects" },
  { to: "/skills", label: "Skills" },
  { to: "/portfolio", label: "Portfolio" },
];

const toolLinks = [
  { to: "/evidence", label: "Evidence" }, 
  { to: "/analysis", label: "Analysis" }, 
  { to: "/resumes", label: "Resumes" }, 
  { to: "/settings", label: "Settings" }
];

export default function Navbar() {
  const { pathname } = useLocation();
  const [toolsOpen, setToolsOpen] = useState(false);
  // Dropdown is active only if a tool page is selected
  const toolActive = toolLinks.some(l => pathname === l.to);

  return (
    <nav className="navbar" onClick={() => setToolsOpen(false)}>
      <div className="navbar-brand">⛏ Digital Artifact Mining</div>
      <div className="navbar-links">
        {mainLinks.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className={`nav-link ${pathname === to && !toolLinks.some(l => l.to === pathname) ? "active" : ""}`}
          >
            {label}
          </Link>
        ))}

        {/* Tools dropdown */}
        <div className={`nav-dropdown${toolActive ? " open" : ""}`} onClick={e => e.stopPropagation()}>
          <button
            className={`nav-link nav-dropdown-trigger${toolActive ? " active" : ""}`}
            onClick={() => setToolsOpen(o => !o)}
            aria-expanded={toolsOpen}
          >
            Tools ▾
          </button>
          {toolsOpen && (
            <div className="nav-dropdown-menu" onClick={() => setToolsOpen(false)}>
              {toolLinks.map(({ to, label }) => (
                <Link key={to} to={to} className={`nav-dropdown-item ${pathname === to ? "active" : ""}`}>{label}</Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}