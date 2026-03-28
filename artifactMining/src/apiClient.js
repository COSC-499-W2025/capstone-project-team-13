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

export function apiUploadWithProgress(path, formData, onProgress) {
  loadingBar.start();
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const token = localStorage.getItem("token");
    xhr.open("POST", `${BASE}${path}`);
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      loadingBar.done();
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch { resolve({}); }
      } else {
        try { reject(new Error(JSON.parse(xhr.responseText).detail || `HTTP ${xhr.status}`)); }
        catch { reject(new Error(`HTTP ${xhr.status}`)); }
      }
    };
    xhr.onerror = () => { loadingBar.done(); reject(new Error("Network error")); };
    xhr.send(formData);
  });
}

/** Return the best human-readable name for a project object from the API */
export function projectName(p) {
  if (!p) return "Untitled";
  const cd = (p.display_name || p.custom_description || "").trim();
  if (cd) return cd;
  const name = (p.name || "").trim();
  // hide UUIDs (36-char hex-dash strings) — but extract any readable suffix after the UUID
  if (/^[0-9a-f-]{30,}/i.test(name)) {
    const suffix = name.replace(/^[0-9a-f-]{30,}_?/i, "").trim();
    if (suffix && !/^[0-9a-f-]{8,}/i.test(suffix)) return suffix;
    return `${p.project_type || "Project"} ${p.id}`;
  }
  return name || "Untitled";
}