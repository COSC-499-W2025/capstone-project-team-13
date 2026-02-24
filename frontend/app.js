const API_BASE = "http://127.0.0.1:8000";

/* ------------------ Generate Resume ------------------ */
function generateResume() {
  const projectId = document.getElementById("genProjectId").value;
  const numBullets = document.getElementById("numBullets").value;
  const output = document.getElementById("generateResult");

  fetch(`${API_BASE}/resume/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      project_id: Number(projectId),
      num_bullets: Number(numBullets)
    })
  })
    .then(res => res.json())
    .then(data => {
      output.textContent = JSON.stringify(data, null, 2);
    })
    .catch(err => {
      output.textContent = "Failed to generate resume";
      console.error(err);
    });
}

/* ------------------ Get Resume ------------------ */
function getResume() {
  const projectId = document.getElementById("viewProjectId").value;
  const output = document.getElementById("resumeDisplay");

  fetch(`${API_BASE}/resume/${projectId}`)
    .then(res => res.json())
    .then(data => {
      output.textContent = JSON.stringify(data, null, 2);
    })
    .catch(err => {
      output.textContent = "Resume not found";
      console.error(err);
    });
}

/* ------------------ Edit Resume ------------------ */
function editResume() {
  const projectId = document.getElementById("editProjectId").value;
  const header = document.getElementById("resumeHeader").value;
  const bulletsRaw = document.getElementById("resumeBullets").value;
  const output = document.getElementById("editResult");

  const bullets = bulletsRaw
    .split("\n")
    .map(b => b.trim())
    .filter(b => b.length > 0);

  fetch(`${API_BASE}/resume/${projectId}/edit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      header: header || null,
      bullets: bullets
    })
  })
    .then(res => res.json())
    .then(data => {
      output.textContent = JSON.stringify(data, null, 2);
    })
    .catch(err => {
      output.textContent = "Failed to edit resume";
      console.error(err);
    });
}

function showTab(tabId) {
  const tabs = document.querySelectorAll(".tab-content");
  tabs.forEach(tab => {
    tab.style.display = tab.id === tabId ? "block" : "none";
  });

  const buttons = document.querySelectorAll(".tab-links button");
  buttons.forEach(btn => {
    btn.classList.toggle("active", btn.textContent.replace(" ", "").toLowerCase() === tabId);
  });
}