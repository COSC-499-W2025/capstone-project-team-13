import React from 'react'
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <div className="navbar">
      <Link to="/">Dashboard</Link>
      <Link to="/upload">Projects</Link>
      <Link to="/resumes">Resumes</Link>
      <Link to="/settings">Settings</Link>
      <Link to="/portfolio">Portfolio</Link>
      <Link to="/profile">Profile</Link>
    </div>
  );
}

export default Navbar;
