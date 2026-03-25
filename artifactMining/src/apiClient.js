import { loadingBar } from "./components/LoadingBar";

const BASE = "http://127.0.0.1:8000";

function authHeaders(extra = {}) {
  const token = localStorage.getItem("token");
  return { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...extra };
}

export async function apiFetch(path, opts = {}) {
  loadingBar.start();
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...opts,
      headers: { ...authHeaders(), ...(opts.headers || {}) },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  } finally {
    loadingBar.done();
  }
}

export async function apiUpload(path, formData) {
  loadingBar.start();
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  } finally {
    loadingBar.done();
  }
}

/** Return the best human-readable name for a project object from the API */
export function projectName(p) {
  if (!p) return "Untitled";
  const cd = (p.display_name || p.custom_description || "").trim();
  if (cd) return cd;
  const name = (p.name || "").trim();
  // hide UUIDs (36-char hex-dash strings)
  if (/^[0-9a-f-]{30,}/i.test(name)) {
    return p.description || p.ai_description || `${p.project_type || "Project"} ${p.id}`;
  }
  return name || "Untitled";
}