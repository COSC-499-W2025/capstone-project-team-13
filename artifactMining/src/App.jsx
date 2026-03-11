import React from 'react'
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Resumes from "./pages/Resumes";
import Portfolio from "./pages/Portfolio";
import Settings from "./pages/Settings";
import ProjectPage from "./pages/ProjectPage";

function App() {
  return (
    <BrowserRouter>

      <Navbar />

      <div className="page-container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/resumes" element={<Resumes />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/settings" element={<Settings />} />
         

        </Routes>
      </div>

    </BrowserRouter>
  );
}

export default App;