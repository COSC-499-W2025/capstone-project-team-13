import React from "react";
import { useNavigate } from "react-router-dom";
import "./NotFound.css";

export default function NotFound() {
  const nav = useNavigate();
  return (
    <div className="nf-wrap">
      <div className="nf-code">404</div>
      <h1 className="nf-title">Page not found</h1>
      <p className="nf-desc">The page you're looking for doesn't exist or was moved.</p>
      <div className="nf-actions">
        <button className="btn-primary" onClick={() => nav("/")}>Go to Dashboard</button>
        <button className="btn-secondary" onClick={() => nav(-1)}>Go Back</button>
      </div>
    </div>
  );
}
