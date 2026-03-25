import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navbar.css";

const mainLinks = [
  { to: "/projects", label: "Projects" },
  { to: "/skills", label: "Skills" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/resumes", label: "Resume" },
];

const toolLinks = [
  { to: "/evidence", label: "Evidence" },
  { to: "/analysis", label: "Analysis" }
];

export default function Navbar({ onLogout, user }) {
  const { pathname } = useLocation();
  const [toolsOpen, setToolsOpen] = useState(false);
  const toolActive = toolLinks.some(l => pathname === l.to);
  const isDashboard = pathname === "/" || pathname === "/dashboard";

  return (
    <nav className="navbar" onClick={() => setToolsOpen(false)}>
      <Link to="/" className={`navbar-brand nav-link${isDashboard ? " active" : ""}`}>Digital Artifact Mining</Link>
      <div className="navbar-links">
        {mainLinks.map(({ to, label }) => {
          const isProjects = to === "/projects" && (pathname === "/projects" || pathname === "/upload");
          const isActive = isProjects || (pathname === to && to !== "/projects");
          return (
            <Link key={to} to={to} className={`nav-link ${isActive ? "active" : ""}`}>{label}</Link>
          );
        })}

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
      <div className="navbar-profile">
        {user && <span className="text-muted" style={{ fontSize: "0.8rem", marginRight: 8 }}>{user.first_name || user.email}</span>}
        <Link to="/settings" className={`nav-link${pathname === "/settings" ? " active" : ""}`}>Profile</Link>
        {onLogout && (
          <button className="nav-link" style={{ background: "none", border: "none", cursor: "pointer", color: "inherit" }} onClick={onLogout}>
            Log Out
          </button>
        )}
      </div>
    </nav>
  );
}
