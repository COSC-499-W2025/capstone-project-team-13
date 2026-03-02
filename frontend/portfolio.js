const API_BASE = "http://127.0.0.1:8000/portfolio";

/* Tab switcher */
function showTab(tabId) {
  const tabs = document.querySelectorAll(".tab-content");
  tabs.forEach(tab => tab.style.display = tab.id === tabId ? "flex" : "none");

  const buttons = document.querySelectorAll(".tab-links button");
  buttons.forEach(btn => btn.classList.toggle("active", btn.textContent.replace(/\s/g, "").toLowerCase() === tabId));
}

/* Full Portfolio */
function getFullPortfolio() {
  fetch(`${API_BASE}?include_hidden=false`)
    .then(res => res.json())
    .then(data => document.getElementById("fullOutput").textContent = JSON.stringify(data, null, 2))
    .catch(err => console.error(err));
}

/* Portfolio Stats */
function getPortfolioStats() {
  fetch(`${API_BASE}/stats?include_hidden=false`)
    .then(res => res.json())
    .then(data => document.getElementById("statsOutput").textContent = JSON.stringify(data, null, 2))
    .catch(err => console.error(err));
}

/* Portfolio Summary */
function getPortfolioSummary() {
  fetch(`${API_BASE}/summary?include_hidden=false`)
    .then(res => res.json())
    .then(data => document.getElementById("summaryOutput").textContent = JSON.stringify(data, null, 2))
    .catch(err => console.error(err));
}

/* Single Project */
function getProject() {
  const id = document.getElementById("projectId").value;
  fetch(`${API_BASE}/${id}`)
    .then(res => res.json())
    .then(data => document.getElementById("projectOutput").textContent = JSON.stringify(data, null, 2))
    .catch(err => document.getElementById("projectOutput").textContent = "Project not found");
}

/* Generate Portfolio */
function generatePortfolio() {
  fetch(`${API_BASE}/generate`, { method: "POST" })
    .then(res => res.json())
    .then(data => document.getElementById("generateOutput").textContent = JSON.stringify(data, null, 2))
    .catch(err => console.error(err));
}

/* Edit Project */
function editProject() {
  const id = document.getElementById("editProjectId").value;
  const updates = document.getElementById("editData").value;

  let jsonData;
  try {
    jsonData = JSON.parse(updates);
  } catch {
    document.getElementById("editOutput").textContent = "Invalid JSON";
    return;
  }

  fetch(`${API_BASE}/${id}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jsonData)
  })
    .then(res => res.json())
    .then(data => document.getElementById("editOutput").textContent = JSON.stringify(data, null, 2))
    .catch(err => console.error(err));
}