import React, { useState } from "react";
import "./Upload.css";
import { useNavigate } from "react-router-dom";

function Updates() {

  const [mainTab, setMainTab] = useState("upload");
  const [subTab, setSubTab] = useState("uploadProject");

  const [file, setFile] = useState(null);
  const [thumbnail, setThumbnail] = useState(null);
  const [status, setStatus] = useState("");

  const [projects, setProjects] = useState([]);

  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  const handleFileChange = (e) => setFile(e.target.files[0]);
  const handleThumbnailChange = (e) => setThumbnail(e.target.files[0]);

  /* ---------- Upload Project ---------- */

  const uploadProject = async () => {

    if (!file) {
      setStatus("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    if (thumbnail) {
      formData.append("thumbnail", thumbnail);
    }

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/projects/upload",
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        }
      );

      if (!response.ok) throw new Error("Upload failed");

      await response.json();
      setStatus("Project uploaded successfully!");

    } catch (err) {

      console.error(err);
      setStatus("Upload failed.");

    }

  };

  /* ---------- Load Projects ---------- */

  const loadProjects = async () => {

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/projects",
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const data = await response.json();

      setProjects(data.projects || data);

    } catch (error) {

      console.error("Error loading projects:", error);

    }

  };

  const openProject = (projectId) => {
    navigate(`/projects/${projectId}`);
  };

  return (

    <div className="manager-wrapper">

      <h1>Project Manager</h1>

      {/* TOP TABS */}

      <div className="top-tabs">

        <button
          className={mainTab === "upload" ? "active" : ""}
          onClick={() => {
            setMainTab("upload");
            setSubTab("uploadProject");
          }}
        >
          Upload
        </button>

        <button
          className={mainTab === "management" ? "active" : ""}
          onClick={() => {
            setMainTab("management");
            setSubTab("viewProjects");
          }}
        >
          Management
        </button>

        <button
          className={mainTab === "ai" ? "active" : ""}
          onClick={() => {
            setMainTab("ai");
            setSubTab("deleteInsights");
          }}
        >
          AI Tools
        </button>

      </div>


      <div className="manager-layout">

        {/* LEFT MENU */}

        <div className="side-menu">

          {mainTab === "upload" && (
            <>
              <button onClick={() => setSubTab("uploadProject")}>
                Upload Project
              </button>
            </>
          )}

          {mainTab === "management" && (
            <>
              <button onClick={() => setSubTab("viewProjects")}>
                View Projects
              </button>

              <button>Add Files</button>
              <button>Delete Project</button>
              <button>Bulk Delete</button>
            </>
          )}

          {mainTab === "ai" && (
            <>
              <button>Delete AI Insights</button>
              <button>Delete ALL Insights</button>
            </>
          )}

        </div>


        {/* CONTENT PANEL */}

        <div className="content-panel">

          {/* Upload Panel */}

          {subTab === "uploadProject" && (

          <div className="panel upload-panel">

            <div className="upload-card">

              <label className="upload-label">
                Upload Project File / ZIP
              </label>

              <input
                type="file"
                className="upload-input"
                onChange={handleFileChange}
              />

              <label className="upload-label">
                Upload Thumbnail (optional)
              </label>

              <input
                type="file"
                className="upload-input"
                onChange={handleThumbnailChange}
              />

              <button
                className="upload-button"
                onClick={uploadProject}
              >
                Upload & Analyze
              </button>

              <p className="status-text">{status}</p>

            </div>

          </div>

        )}

          {/* View Projects Panel */}

          {subTab === "viewProjects" && (

            <div className="panel">

              <h2>Stored Projects</h2>

              <button className="load-button" onClick={loadProjects}>
                Load Projects
              </button>

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

          )}

        </div>

      </div>

    </div>

  );
}

export default Updates;