import React, { useEffect, useState } from "react";
import { getPortfolio, generatePortfolio } from "../services/api";

function Portfolio() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPortfolio()
      .then((res) => {
        const all = res.data.projects || [];
        const top3 = all.slice(0, 3);
        setProjects(top3);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load portfolio. Make sure you are logged in.");
        setLoading(false);
      });
  }, []);

  const handleGenerate = () => {
    setLoading(true);
    generatePortfolio()
      .then(() => getPortfolio())
      .then((res) => {
        const all = res.data.projects || [];
        setProjects(all.slice(0, 3));
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to generate portfolio.");
        setLoading(false);
      });
  };

  if (loading) return <div className="page-container">Loading portfolio...</div>;
  if (error) return <div className="page-container">{error}</div>;

  return (
    <div className="page-container">
      <h1>My Portfolio</h1>
      <button onClick={handleGenerate}>Generate Portfolio</button>
      <h2>Top Projects</h2>
      {projects.length === 0 ? (
        <p>No projects found. Click Generate Portfolio to get started.</p>
      ) : (
        <div className="dashboard-grid">
          {projects.map((project) => (
            <div className="card" key={project.id}>
              <h3>{project.name}</h3>
              <p>{project.description}</p>
              <p><strong>Type:</strong> {project.project_type}</p>
              <p><strong>Languages:</strong> {project.languages?.join(", ")}</p>
              <p><strong>Word Count:</strong> {project.word_count}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Portfolio;