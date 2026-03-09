import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

function ProjectPage() {

  const { projectId } = useParams();

  const [project, setProject] = useState(null);

  useEffect(() => {
    loadProject();
  }, []);

  const loadProject = async () => {

    const token = localStorage.getItem("token");

    const response = await fetch(
      `http://127.0.0.1:8000/projects/${projectId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    const data = await response.json();
    setProject(data);
  };

  if (!project) {
    return <p>Loading project...</p>;
  }

  return (
    <div className="project-page">

      <h1>{project.name || "Project"}</h1>

      <p><strong>ID:</strong> {project.id}</p>

      <p><strong>Language:</strong> {project.language}</p>

      <p><strong>Description:</strong> {project.description}</p>

    </div>
  );
}

export default ProjectPage;