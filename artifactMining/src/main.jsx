import React from "react";
import ReactDOM from "react-dom/client";
import "./theme.css";
import "./index.css";
import App from "./App";

// Set theme before anything renders so there's no flash
const savedTheme = localStorage.getItem("theme") || "dark";
document.body.setAttribute("data-theme", savedTheme);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);