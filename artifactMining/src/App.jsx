import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Toast from "./components/Toast";
import LoadingBar from "./components/LoadingBar";
import CommandPalette from "./components/CommandPalette";
import PageTransition from "./components/PageTransition";
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

const KONAMI = ["ArrowUp","ArrowUp","ArrowDown","ArrowDown","ArrowLeft","ArrowRight","ArrowLeft","ArrowRight","b","a"];

function KonamiEgg() {
  const [seq, setSeq] = useState([]);
  const [show, setShow] = useState(false);

  useEffect(() => {
    function onKey(e) {
      setSeq(prev => {
        const next = [...prev, e.key].slice(-KONAMI.length);
        if (next.join(",") === KONAMI.join(",")) {
          setShow(true);
          setTimeout(() => setShow(false), 3500);
        }
        return next;
      });
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!show) return null;
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 99999,
      display: "flex", alignItems: "center", justifyContent: "center",
      background: "rgba(0,0,0,0.7)", backdropFilter: "blur(6px)",
      animation: "toast-in 0.4s ease both",
    }}>
      <div style={{
        fontSize: "clamp(2rem,8vw,5rem)", textAlign: "center",
        padding: "40px 60px", borderRadius: "20px",
        background: "linear-gradient(135deg,#6366f1,#a78bfa,#ec4899)",
        boxShadow: "0 0 80px rgba(99,102,241,0.6)",
        color: "#fff",
      }}>
        <div style={{ fontSize: "5rem", marginBottom: 12 }}>🎮</div>
        <div style={{ fontWeight: 800, letterSpacing: "0.05em" }}>CHEAT CODE ACTIVATED</div>
        <div style={{ fontSize: "0.9rem", opacity: 0.8, marginTop: 8 }}>You found the secret!</div>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <LoadingBar />
      <Navbar />
      <Toast />
      <KonamiEgg />
      <CommandPalette />
      <PageTransition>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/evidence" element={<Evidence />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/deletion" element={<Deletion />} />
          <Route path="/resumes" element={<Resumes />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </PageTransition>
    </BrowserRouter>
  );
}

export default App;