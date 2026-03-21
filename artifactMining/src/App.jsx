import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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

function App() {
  return (
    <BrowserRouter>
      <Navbar />
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
    </BrowserRouter>
  );
}

export default App;