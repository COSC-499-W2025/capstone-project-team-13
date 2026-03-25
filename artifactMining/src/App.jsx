import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Projects from "./pages/Projects";
import ProjectPage from "./pages/ProjectPage";
import Skills from "./pages/Skills";
import Portfolio from "./pages/Portfolio";
import Evidence from "./pages/Evidence";
import Analysis from "./pages/Analysis";
import Deletion from "./pages/Deletion";
import Resumes from "./pages/Resumes";
import Settings from "./pages/Settings";
import GuestUpload from "./pages/GuestUpload";
import WebShowcase from "./pages/WebShowcase";

const API_BASE = "http://127.0.0.1:8000";

function LoginGate({ onLogin }) {
  const [tab, setTab] = useState("login");
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function onChange(e) { setForm(f => ({ ...f, [e.target.name]: e.target.value })); }

  async function submit(e) {
    e.preventDefault(); setError(""); setLoading(true);
    const url = tab === "login" ? "/auth/login" : "/auth/signup";
    try {
      const res = await fetch(`${API_BASE}${url}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      if (data.token) { localStorage.setItem("token", data.token); onLogin(data.user); }
      else { setError("No token returned"); }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Digital Artifact Mining</h1>
      <p className="text-muted" style={{ marginBottom: 32 }}>Analyse and showcase your projects</p>

      <div className="card" style={{ width: "100%", maxWidth: 420, padding: 32 }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          {["login", "signup"].map(t => (
            <button key={t} className={tab === t ? "btn-primary" : "btn-secondary"}
              style={{ flex: 1 }} onClick={() => setTab(t)}>
              {t === "login" ? "Log In" : "Sign Up"}
            </button>
          ))}
        </div>

        {error && <div className="alert error" style={{ marginBottom: 16 }}>{error}</div>}

        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {tab === "signup" && (
            <>
              <input name="first_name" placeholder="First name" value={form.first_name} onChange={onChange} required style={{ padding: "10px 12px" }} />
              <input name="last_name" placeholder="Last name" value={form.last_name} onChange={onChange} required style={{ padding: "10px 12px" }} />
            </>
          )}
          <input name="email" type="email" placeholder="Email" value={form.email} onChange={onChange} required style={{ padding: "10px 12px" }} />
          <input name="password" type="password" placeholder="Password" value={form.password} onChange={onChange} required style={{ padding: "10px 12px" }} />
          <button className="btn-primary" type="submit" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? "..." : tab === "login" ? "Log In" : "Create Account"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 20, paddingTop: 20, borderTop: "1px solid var(--border)" }}>
          <p className="text-muted" style={{ marginBottom: 12, fontSize: "0.85rem" }}>Just want to try it out?</p>
          <a href="/guest" style={{ color: "var(--accent)", fontSize: "0.9rem" }}>Continue as Guest (no account needed)</a>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(undefined); // undefined = loading, null = not logged in

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setUser(null); return; }
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(u => setUser(u || null))
      .catch(() => setUser(null));
  }, []);

  function handleLogout() {
    localStorage.removeItem("token");
    setUser(null);
  }

  if (user === undefined) return <div style={{ padding: 40 }}>Loading…</div>;

  // Guest route is always accessible
  if (window.location.pathname === "/guest") {
    return <BrowserRouter><GuestUpload /></BrowserRouter>;
  }

  if (!user) return <BrowserRouter><LoginGate onLogin={u => setUser(u)} /></BrowserRouter>;

  return (
    <BrowserRouter>
      <Navbar onLogout={handleLogout} user={user} />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:projectId" element={<ProjectPage />} />
        <Route path="/skills" element={<Skills />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/showcase" element={<WebShowcase />} />
        <Route path="/evidence" element={<Evidence />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/deletion" element={<Deletion />} />
        <Route path="/resumes" element={<Resumes />} />
        <Route path="/settings" element={<Settings onLogout={handleLogout} />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
