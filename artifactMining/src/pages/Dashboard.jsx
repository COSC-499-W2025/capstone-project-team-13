import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import { useNavigate } from "react-router-dom";

function Dashboard() {

  const [projects, setProjects] = useState([]);
  const [hiddenThumbnails, setHiddenThumbnails] = useState({});
  const navigate = useNavigate(); 

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

  const getInitial = (name) => {
    if (!name || typeof name !== "string") return "P";
    return name.trim().charAt(0).toUpperCase() || "P";
  };

  const looksLikeUuid = (value) => {
    if (!value || typeof value !== "string") return false;
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.trim());
  };

  const getReadableNameFromPath = (filePath) => {
    if (!filePath || typeof filePath !== "string") return null;
    const cleanPath = filePath.replace(/\\/g, "/").replace(/\/+$/, "");
    const lastSegment = cleanPath.split("/").filter(Boolean).pop();
    if (!lastSegment) return null;
    return lastSegment.replace(/\.[^.]+$/, "");
  };

  const getProjectDisplayName = (project) => {
    const fromPath = getReadableNameFromPath(project?.file_path);
    if (fromPath && !looksLikeUuid(fromPath)) return fromPath;

    const projectName = project?.name;
    if (projectName && !looksLikeUuid(projectName)) return projectName;

    return "Untitled Project";
  };

  const getProjectUuid = (project) => {
    const projectName = project?.name;
    if (looksLikeUuid(projectName)) return projectName;

    const projectId = String(project?.id ?? "");
    if (looksLikeUuid(projectId)) return projectId;

    return null;
  };

  const formatProjectType = (project) => {
    const rawType = project?.project_type || project?.language || "Unknown";
    return String(rawType)
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
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

                {project.thumbnail_path && !hiddenThumbnails[project.id] ? (
                  <img
                    src={`http://127.0.0.1:8000/${project.thumbnail_path}`}
                    className="project-thumbnail"
                    alt="project"
                    onError={() =>
                      setHiddenThumbnails((prev) => ({
                        ...prev,
                        [project.id]: true,
                      }))
                    }
                  />
                ) : (
                  <div className="project-thumbnail-placeholder" aria-hidden="true">
                    {getInitial(project.name)}
                  </div>
                )}

                <div className="project-info">
                  <div className="project-title-row">
                    <h3>{getProjectDisplayName(project)}</h3>
                    <span className="project-type-badge">{formatProjectType(project)}</span>
                  </div>
                  {getProjectUuid(project) ? (
                    <p className="project-id-text">UUID {getProjectUuid(project)}</p>
                  ) : null}
                </div>

              </div>
            ))}
          <button
              className="upload-button"
              onClick={() => window.location.href = "/upload"}
            >
              Upload Project
            </button>
          </div>
        )}

      </div>

      <div className="card resumes">
        <h2>Resume Builder</h2>
        <p>Generated Resumes will appear here</p>
      </div>

      <div className="card insights">
        <h2>Charts & Insights</h2>
      </div>

      <div className="card portfolios click-card" 
            onClick={() => navigate("/portfolio")} >
          <h2>Portfolio Builder</h2>
          <p>Click to view and manage your portfolio</p>
      </div>

    </div>
  );
}

export default Dashboard;