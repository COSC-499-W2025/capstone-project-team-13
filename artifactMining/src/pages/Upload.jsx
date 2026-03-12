import React, { useState } from "react";
import "./Upload.css";

function UploadProject() {

  const [file, setFile] = useState(null);
  const [thumbnail, setThumbnail] = useState(null);
  const [status, setStatus] = useState("");

  const token = localStorage.getItem("token");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleThumbnailChange = (e) => {
    setThumbnail(e.target.files[0]);
  };

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

      const response = await fetch("http://127.0.0.1:8000/projects/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setStatus("Project uploaded and analyzed successfully!");
      console.log("Analysis result:", data);

    } catch (err) {
      console.error(err);
      setStatus("Upload failed.");
    }

  };

  return (
    <div className="upload-wrapper">

      <h1>Project Manager</h1>

    <div className="upload-page">
    

      {/* Upload Section */}
      <div className="upload-card">

        <h2>Upload Project</h2>

        <label>Upload Project File / ZIP</label>
        <input type="file" onChange={handleFileChange} />

        <label>Upload Thumbnail (optional)</label>
        <input type="file" onChange={handleThumbnailChange} />

        <button onClick={uploadProject}>
          Upload & Analyze
        </button>

        <p>{status}</p>

      </div>

      {/* Project Management */}
      <div className="upload-card">

        <h2>Project Management</h2>

        <button>View All Projects</button>

        <button>Sort / Score Projects</button>

        <button>Add Files to Existing Project</button>

        <button>Manage Project Evidence</button>

        <button>Delete Project (Safe)</button>

        <button>Bulk Delete Projects</button>

      </div>


      {/* AI Insights */}
      <div className="upload-card">

        <h2>AI Insights</h2>

        <button>Delete AI Insights (Single Project)</button>

        <button>Delete ALL AI Insights</button>

      </div>

    </div>
    </div>
  );
}

export default UploadProject;