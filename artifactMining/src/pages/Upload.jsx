import React, { useState } from "react";
import "./Upload.css";

function UploadProject() {

  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const uploadProject = async () => {

    if (!file) {
      setStatus("Please select a file first.");
      return;
    }

    const token = localStorage.getItem("token");

    const formData = new FormData();
    formData.append("file", file);

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
    <div className="upload-page">

      <h1>Upload Project</h1>

      <div className="upload-card">

        <input
          type="file"
          onChange={handleFileChange}
        />

        <button onClick={uploadProject}>
          Upload & Analyze
        </button>

        <p>{status}</p>

      </div>

    </div>
  );
}

export default UploadProject;