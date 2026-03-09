import React, { useEffect, useState } from "react";
import "./Dashboard.css";

function Dashboard() {

  const [projects, setProjects] = useState([]);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    const token = localStorage.getItem("token");

    try {
      const response = await fetch("http://127.0.0.1:8000/projects", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      const data = await response.json();
      setProjects(data);

    } catch (error) {
      console.error("Error loading projects:", error);
    }
  };

  const openProject = (projectId) => {
    window.location.href = `/projects/${projectId}`;
  };

  return (
    <div className="dashboard-grid">

      <div className="card projects">
        <h2>Projects</h2>

        {projects.length === 0 ? (
          <p>No projects uploaded yet.</p>
        ) : (
          <div className="project-list">

            {projects.map(project => (
              <div
                key={project.id}
                className="project-card"
                onClick={() => openProject(project.id)}
              >

                <img
                  src={
                    project.thumbnail_path
                      ? `http://127.0.0.1:8000/${project.thumbnail_path}`
                      : "/default-thumbnail.png"
                  }
                  className="project-thumbnail"
                  alt="project"
                />

                <div className="project-info">
                  <h3>{project.name || "Untitled Project"}</h3>
                  <p>{project.language || "Code Project"}</p>
                </div>

              </div>
            ))}

          </div>
        )}

      </div>

      <div className="card resumes">
        <h2>AI Generated Resumes</h2>
      </div>

      <div className="card portfolios">
        <h2>AI Generated Portfolios</h2>
      </div>

      <div className="card insights">
        <h2>Charts & Insights</h2>
      </div>

    </div>
  );
}

export default Dashboard;