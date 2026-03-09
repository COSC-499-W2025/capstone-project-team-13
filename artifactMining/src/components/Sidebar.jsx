import React from 'react'
import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="sidebar">
      <h2>Resume Analyzer</h2>

      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/upload">Upload Resume</Link>
        <Link to="/resumes">View Resumes</Link>
        <Link to="/settings">Settings</Link>
      </nav>
    </div>
  );
}

export default Sidebar;
