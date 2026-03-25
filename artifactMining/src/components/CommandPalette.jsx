import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, projectName } from "../apiClient";
import "./CommandPalette.css";

const STATIC_COMMANDS = [
  // Navigation
  { id: "nav-dashboard",  group: "Navigate", icon: "🏠", label: "Dashboard",       path: "/" },
  { id: "nav-projects",   group: "Navigate", icon: "📁", label: "Projects",         path: "/projects" },
  { id: "nav-skills",     group: "Navigate", icon: "⚡", label: "Skills",           path: "/skills" },
  { id: "nav-portfolio",  group: "Navigate", icon: "🎨", label: "Portfolio",        path: "/portfolio" },
  { id: "nav-resume",     group: "Navigate", icon: "📄", label: "Resume Builder",   path: "/resumes" },
  { id: "nav-upload",     group: "Navigate", icon: "⬆️", label: "Upload Project",   path: "/upload" },
  { id: "nav-analysis",   group: "Navigate", icon: "🔬", label: "AI Analysis",      path: "/analysis" },
  { id: "nav-settings",   group: "Navigate", icon: "⚙️", label: "Settings",         path: "/settings" },
  // Actions
  { id: "act-dark",   group: "Actions", icon: "🌙", label: "Switch to Dark Mode",  action: "dark" },
  { id: "act-light",  group: "Actions", icon: "☀️", label: "Switch to Light Mode", action: "light" },
  { id: "act-upload", group: "Actions", icon: "📂", label: "Upload a new project",  path: "/upload" },
];

// Module-level open/close so it can be triggered from anywhere
const _listeners = new Set();
export function openCommandPalette() { _listeners.forEach(fn => fn()); }

export default function CommandPalette() {
  const [open, setOpen]       = useState(false);
  const [query, setQuery]     = useState("");
  const [projects, setProjects] = useState([]);
  const [active, setActive]   = useState(0);
  const inputRef = useRef(null);
  const listRef  = useRef(null);
  const nav = useNavigate();

  // Subscribe to external open trigger
  useEffect(() => {
    const fn = () => setOpen(true);
    _listeners.add(fn);
    return () => _listeners.delete(fn);
  }, []);

  // Keyboard shortcut Ctrl+K / Cmd+K
  useEffect(() => {
    function onKey(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen(o => !o);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Load projects when opened
  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    setTimeout(() => inputRef.current?.focus(), 30);
    apiFetch("/projects").then(d => {
      setProjects(Array.isArray(d) ? d.slice(0, 40) : []);
    }).catch(() => {});
  }, [open]);

  const projectCommands = projects.map(p => ({
    id: `proj-${p.id}`,
    group: "Projects",
    icon: "📁",
    label: projectName(p),
    path: `/projects/${p.id}`,
  }));

  const all = [...STATIC_COMMANDS, ...projectCommands];

  const filtered = query.trim()
    ? all.filter(c => c.label.toLowerCase().includes(query.toLowerCase()) ||
                      c.group.toLowerCase().includes(query.toLowerCase()))
    : all;

  // Group filtered results
  const grouped = filtered.reduce((acc, cmd) => {
    if (!acc[cmd.group]) acc[cmd.group] = [];
    acc[cmd.group].push(cmd);
    return acc;
  }, {});

  const flat = Object.values(grouped).flat();

  function execute(cmd) {
    setOpen(false);
    if (cmd.action === "dark" || cmd.action === "light") {
      document.body.setAttribute("data-theme", cmd.action);
      localStorage.setItem("theme", cmd.action);
      return;
    }
    if (cmd.path) nav(cmd.path);
  }

  function onKeyDown(e) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive(a => Math.min(a + 1, flat.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive(a => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      if (flat[active]) execute(flat[active]);
    }
  }

  // Scroll active item into view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${active}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [active]);

  if (!open) return null;

  let idx = 0;
  return (
    <div className="cp-backdrop" onClick={() => setOpen(false)}>
      <div className="cp-modal" onClick={e => e.stopPropagation()}>
        <div className="cp-search-row">
          <span className="cp-search-icon">⌘</span>
          <input
            ref={inputRef}
            className="cp-input"
            placeholder="Search pages, projects, actions…"
            value={query}
            onChange={e => { setQuery(e.target.value); setActive(0); }}
            onKeyDown={onKeyDown}
          />
          <kbd className="cp-esc">esc</kbd>
        </div>

        <div className="cp-list" ref={listRef}>
          {Object.entries(grouped).map(([group, cmds]) => (
            <div key={group} className="cp-group">
              <div className="cp-group-label">{group}</div>
              {cmds.map(cmd => {
                const i = idx++;
                return (
                  <div
                    key={cmd.id}
                    data-idx={i}
                    className={`cp-item ${i === active ? "cp-item-active" : ""}`}
                    onMouseEnter={() => setActive(i)}
                    onClick={() => execute(cmd)}
                  >
                    <span className="cp-item-icon">{cmd.icon}</span>
                    <span className="cp-item-label">{cmd.label}</span>
                    {i === active && <span className="cp-item-enter">↵</span>}
                  </div>
                );
              })}
            </div>
          ))}
          {flat.length === 0 && (
            <div className="cp-empty">No results for "{query}"</div>
          )}
        </div>

        <div className="cp-footer">
          <span><kbd>↑↓</kbd> navigate</span>
          <span><kbd>↵</kbd> select</span>
          <span><kbd>esc</kbd> close</span>
        </div>
      </div>
    </div>
  );
}
