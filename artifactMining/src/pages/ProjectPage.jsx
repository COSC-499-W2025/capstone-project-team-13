import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./ProjectPage.css";

function ProjectPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);

  useEffect(() => {
    loadProject();
  }, []);

  const loadProject = async () => {
    const token = localStorage.getItem("token");
    const response = await fetch(
      `http://127.0.0.1:8000/projects/${projectId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const data = await response.json();
    setProject(data);
  };

  function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  if (!project) return <p>Loading project...</p>;

  return (
    <div className="project-page">
      <button onClick={() => navigate(-1)}>← Back to Dashboard</button>

      <h1>{project.name}</h1>

      <p><strong>Type:</strong> {project.project_type}</p>
      <p><strong>Description:</strong> {project.description || "N/A"}</p>
      <p><strong>Tags:</strong> {project.tags.join(", ")}</p>
      <p><strong>Date Scanned:</strong> {new Date(project.date_scanned).toLocaleString()}</p>

      <h3>Stats</h3>
      <ul>
        <li><strong>Files:</strong> {project.file_count}</li>
        <li><strong>Lines of Code:</strong> {project.lines_of_code}</li>
        <li><strong>Word Count:</strong> {project.word_count}</li>
        <li><strong>Total Size:</strong> {formatBytes(project.total_size_bytes)}</li>
      </ul>

      <h3>Skills</h3>
      <ul>
        {project.skills.map((skill, idx) => (
          <li key={idx}>{skill.replace(/_/g, " ")}</li>
        ))}
      </ul>

      {project.languages.length > 0 && (
        <>
          <h3>Languages</h3>
          <ul>{project.languages.map((lang, idx) => <li key={idx}>{lang}</li>)}</ul>
        </>
      )}

      {project.frameworks.length > 0 && (
        <>
          <h3>Frameworks</h3>
          <ul>{project.frameworks.map((fw, idx) => <li key={idx}>{fw}</li>)}</ul>
        </>
      )}

    </div>
  );
}

export default ProjectPage;