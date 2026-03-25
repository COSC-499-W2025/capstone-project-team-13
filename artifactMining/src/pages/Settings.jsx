import React, { useEffect, useState } from "react";
import "./Settings.css";

const API_BASE = "http://127.0.0.1:8000";

export default function Settings({ onLogout }) {
  const [signupForm, setSignupForm] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [authLoading, setAuthLoading] = useState(false);
  const [currentUserLoading, setCurrentUserLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [accountMessage, setAccountMessage] = useState("");
  const [accountError, setAccountError] = useState("");
  const [activeSection, setActiveSection] = useState("account");

  // ── Theme ────────────────────────────────────────────────────────────────────
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme(t => t === "dark" ? "light" : "dark");
  }

  // ── Consent ──────────────────────────────────────────────────────────────────
  const [basicConsent, setBasicConsent] = useState(false);
  const [aiConsent, setAiConsent] = useState(false);
  const [loadingBasic, setLoadingBasic] = useState(true);
  const [loadingAi, setLoadingAi] = useState(true);
  const [updatingBasic, setUpdatingBasic] = useState(false);
  const [updatingAi, setUpdatingAi] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // ── Privacy ──────────────────────────────────────────────────────────────────
  const [privacySettings, setPrivacySettings] = useState({
    excluded_folders: [],
    excluded_file_types: [],
  });
  const [privacyLoading, setPrivacyLoading] = useState(false);
  const [newExcludedFolder, setNewExcludedFolder] = useState("");
  const [newExcludedFileType, setNewExcludedFileType] = useState("");

  // ── Current Configuration ────────────────────────────────────────────────────
  const [currentConfig, setCurrentConfig] = useState(null);
  const [currentConfigLoading, setCurrentConfigLoading] = useState(false);
  const [currentConfigError, setCurrentConfigError] = useState("");

  useEffect(() => {
    if (activeSection === "account") fetchCurrentUser();
    if (activeSection === "consent") fetchConsentStatuses();
    if (activeSection === "privacy") fetchPrivacySettings();
    if (activeSection === "currentConfig") fetchCurrentConfiguration();
  }, [activeSection]);

  async function fetchCurrentConfiguration() {
    try {
      setCurrentConfigLoading(true); setCurrentConfigError("");
      const res = await fetch(`${API_BASE}/configuration/current-configuration`);
      if (!res.ok) throw new Error("Failed to fetch current configuration");
      setCurrentConfig(await res.json());
    } catch (err) { setCurrentConfigError("Could not load current configuration."); }
    finally { setCurrentConfigLoading(false); }
  }

  // ── Privacy Settings ─────────────────────────────────────────────────────────
  async function fetchPrivacySettings() {
    try {
      setPrivacyLoading(true); setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/configuration/privacy-settings`);
      if (!response.ok) throw new Error("Failed to fetch privacy settings");
      const data = await response.json();
      setPrivacySettings({
        excluded_folders: data.excluded_folders ?? [],
        excluded_file_types: data.excluded_file_types ?? [],
      });
    } catch (err) { setError("Could not load privacy settings."); }
    finally { setPrivacyLoading(false); }
  }

  async function addExcludedFolder() {
    const folderPath = newExcludedFolder.trim(); if (!folderPath) return;
    try {
      setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/configuration/privacy-settings/excluded-folders`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to add excluded folder"); }
      setNewExcludedFolder(""); setMessage("Excluded folder added successfully.");
      await fetchPrivacySettings();
    } catch (err) { setError(err.message || "Could not add excluded folder."); }
  }

  async function removeExcludedFolder(folder) {
    try {
      setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/configuration/privacy-settings/excluded-folders`, {
        method: "DELETE", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folder.trim() }),
      });
      if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to remove excluded folder"); }
      setMessage("Excluded folder removed successfully.");
      await fetchPrivacySettings();
    } catch (err) { setError(err.message || "Could not remove excluded folder."); }
  }

  async function addExcludedFileType() {
    const fileType = newExcludedFileType.trim(); if (!fileType) return;
    try {
      setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/configuration/privacy-settings/excluded-file-types`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_type: fileType }),
      });
      if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to add excluded file type"); }
      setNewExcludedFileType(""); setMessage("Excluded file type added successfully.");
      await fetchPrivacySettings();
    } catch (err) { setError(err.message || "Could not add excluded file type."); }
  }

  async function removeExcludedFileType(fileType) {
    try {
      setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/configuration/privacy-settings/excluded-file-types`, {
        method: "DELETE", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_type: fileType.trim() }),
      });
      if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to remove excluded file type"); }
      setMessage("Excluded file type removed successfully.");
      await fetchPrivacySettings();
    } catch (err) { setError(err.message || "Could not remove excluded file type."); }
  }

  // ── Consent ──────────────────────────────────────────────────────────────────
  async function fetchConsentStatuses() {
    setError(""); setMessage("");
    await Promise.all([fetchBasicConsentStatus(), fetchAiConsentStatus()]);
  }

  async function fetchBasicConsentStatus() {
    try {
      setLoadingBasic(true);
      const response = await fetch(`${API_BASE}/consent/basic-consent-status`);
      if (!response.ok) throw new Error("Failed to fetch basic consent status");
      const data = await response.json();
      setBasicConsent(Boolean(data.granted ?? data.basic_consent_granted ?? data.status ?? false));
    } catch (err) { setError("Could not load basic consent status."); }
    finally { setLoadingBasic(false); }
  }

  async function fetchAiConsentStatus() {
    try {
      setLoadingAi(true);
      const response = await fetch(`${API_BASE}/consent/ai-consent-status`);
      if (!response.ok) throw new Error("Failed to fetch AI consent status");
      const data = await response.json();
      setAiConsent(Boolean(data.granted ?? data.ai_consent_granted ?? data.status ?? false));
    } catch (err) { setError("Could not load AI consent status."); }
    finally { setLoadingAi(false); }
  }

  async function grantBasicConsent() {
    try {
      setUpdatingBasic(true); setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/consent/basic-consent-grant`, { method: "POST", headers: { "Content-Type": "application/json" } });
      if (!response.ok) throw new Error("Failed to grant basic consent");
      setBasicConsent(true); setMessage("Basic consent granted successfully.");
    } catch (err) { setError("Could not grant basic consent."); }
    finally { setUpdatingBasic(false); }
  }

  async function revokeBasicConsent() {
    try {
      setUpdatingBasic(true); setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/consent/basic-consent-revoke`, { method: "POST", headers: { "Content-Type": "application/json" } });
      if (!response.ok) throw new Error("Failed to revoke basic consent");
      setBasicConsent(false); setMessage("Basic consent revoked successfully.");
    } catch (err) { setError("Could not revoke basic consent."); }
    finally { setUpdatingBasic(false); }
  }

  async function grantAiConsent() {
    try {
      setUpdatingAi(true); setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/consent/ai-consent-grant`, { method: "POST", headers: { "Content-Type": "application/json" } });
      if (!response.ok) throw new Error("Failed to grant AI consent");
      setAiConsent(true); setMessage("AI consent granted successfully.");
    } catch (err) { setError("Could not grant AI consent."); }
    finally { setUpdatingAi(false); }
  }

  async function revokeAiConsent() {
    try {
      setUpdatingAi(true); setError(""); setMessage("");
      const response = await fetch(`${API_BASE}/consent/ai-consent-revoke`, { method: "POST", headers: { "Content-Type": "application/json" } });
      if (!response.ok) throw new Error("Failed to revoke AI consent");
      setAiConsent(false); setMessage("AI consent revoked successfully.");
    } catch (err) { setError("Could not revoke AI consent."); }
    finally { setUpdatingAi(false); }
  }

  // ── Account ───────────────────────────────────────────────────────────────────
  function handleSignupChange(e) { const { name, value } = e.target; setSignupForm(p => ({ ...p, [name]: value })); }
  function handleLoginChange(e) { const { name, value } = e.target; setLoginForm(p => ({ ...p, [name]: value })); }

  async function handleSignup(e) {
    e.preventDefault(); setAccountMessage(""); setAccountError("");
    try {
      setAuthLoading(true);
      const response = await fetch(`${API_BASE}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(signupForm) });
      if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to sign up"); }
      const data = await response.json().catch(() => ({}));
      setAccountMessage(data.message || "Signup successful.");
      setSignupForm({ first_name: "", last_name: "", email: "", password: "" });
    } catch (err) { setAccountError(err.message || "Could not sign up."); }
    finally { setAuthLoading(false); }
  }

  async function handleLogin(e) {
    e.preventDefault(); setAccountMessage(""); setAccountError("");
    try {
      setAuthLoading(true);
      const response = await fetch(`${API_BASE}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(loginForm) });
      if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to log in"); }
      const data = await response.json().catch(() => ({}));
      if (data.token) localStorage.setItem("token", data.token);
      setAccountMessage(data.message || "Login successful.");
      setLoginForm({ email: "", password: "" });
      await fetchCurrentUser();
    } catch (err) { setAccountError(err.message || "Could not log in."); }
    finally { setAuthLoading(false); }
  }

  async function fetchCurrentUser() {
    setCurrentUserLoading(true); setAccountError("");
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE}/auth/me`, { method: "GET", headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (!response.ok) { if (response.status === 401 || response.status === 403) { setCurrentUser(null); return; } const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to load current user"); }
      setCurrentUser(await response.json());
    } catch (err) { setAccountError(err.message || "Could not load current user."); }
    finally { setCurrentUserLoading(false); }
  }

  function handleLogout() {
    localStorage.removeItem("token"); setCurrentUser(null);
    setAccountMessage("Logged out successfully."); setAccountError("");
    if (onLogout) onLogout();
  }

  // ── Render helpers ────────────────────────────────────────────────────────────
  function renderStatusBadge(isGranted, isLoading) {
    if (isLoading) return <span className="settings-badge settings-badge-loading">Loading...</span>;
    return isGranted
      ? <span className="settings-badge settings-badge-granted">Granted</span>
      : <span className="settings-badge settings-badge-revoked">Not Granted</span>;
  }

  function renderBooleanBadge(val) {
    return val
      ? <span className="settings-badge settings-badge-granted">Yes</span>
      : <span className="settings-badge settings-badge-revoked">No</span>;
  }

  function formatKey(key) {
    return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  }

  function formatTimestamp(ts) {
    if (!ts) return "N/A";
    try { return new Date(ts).toLocaleString(); } catch { return ts; }
  }

  // ── Current Config sections ───────────────────────────────────────────────────
  const CONFIG_SECTIONS = [
    {
      key: "consent",
      title: "Consent",
      description: "Current consent status and timestamps.",
      render: (data) => (
        <>
          <div className="settings-config-row">
            <span>Basic Consent</span>
            {renderBooleanBadge(data.basic_consent_granted)}
          </div>
          {data.basic_consent_granted && data.basic_consent_timestamp && (
            <div className="settings-config-row">
              <span>Basic Consent Granted</span>
              <span className="settings-config-value">{formatTimestamp(data.basic_consent_timestamp)}</span>
            </div>
          )}
          <div className="settings-config-row">
            <span>AI Consent</span>
            {renderBooleanBadge(data.ai_consent_granted)}
          </div>
          {data.ai_consent_granted && data.ai_consent_timestamp && (
            <div className="settings-config-row">
              <span>AI Consent Granted</span>
              <span className="settings-config-value">{formatTimestamp(data.ai_consent_timestamp)}</span>
            </div>
          )}
        </>
      ),
    },
    {
      key: "privacy_settings",
      title: "Privacy Settings",
      description: "Excluded folders and file types.",
      render: (data) => (
        <>
          {data.excluded_folders?.length > 0 && (
            <div className="settings-config-list-block">
              <span className="settings-config-list-label">Excluded Folders</span>
              <ul className="settings-config-list">
                {data.excluded_folders.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}
          {data.excluded_file_types?.length > 0 && (
            <div className="settings-config-list-block">
              <span className="settings-config-list-label">Excluded File Types</span>
              <ul className="settings-config-list">
                {data.excluded_file_types.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
          {!data.excluded_folders?.length && !data.excluded_file_types?.length && (
            <p>No exclusions configured.</p>
          )}
        </>
      ),
    },
  ];

  function renderCurrentConfigSection() {
    return (
      <div className="settings-section-panel">
        <h2>Current Configuration</h2>
        <p className="settings-section-description">A read-only snapshot of the full active configuration.</p>
        {currentConfigError && (
          <div className="settings-alerts">
            <div className="settings-alert settings-alert-error">{currentConfigError}</div>
          </div>
        )}
        {currentConfigLoading ? (
          <p>Loading current configuration...</p>
        ) : !currentConfig ? (
          <p>No configuration data available.</p>
        ) : (
          <div className="settings-content-grid">
            {CONFIG_SECTIONS.map(({ key, title, description, render }) =>
              currentConfig[key] != null ? (
                <div key={key} className="settings-card">
                  <div className="settings-card-header">
                    <div><h3>{title}</h3><p>{description}</p></div>
                  </div>
                  <div className="settings-card-body">{render(currentConfig[key])}</div>
                </div>
              ) : null
            )}
          </div>
        )}
        <div className="settings-footer">
          <button className="settings-button settings-button-refresh" onClick={fetchCurrentConfiguration} disabled={currentConfigLoading} type="button">
            Refresh
          </button>
        </div>
      </div>
    );
  }

  function renderAccountSection() {
    return (
      <div className="settings-section-panel">
        <h2>Account Settings</h2>
        <p className="settings-section-description">Manage your account and authentication.</p>
        {(accountMessage || accountError) && (
          <div className="settings-alerts">
            {accountMessage && <div className="settings-alert settings-alert-success">{accountMessage}</div>}
            {accountError && <div className="settings-alert settings-alert-error">{accountError}</div>}
          </div>
        )}
        <div className="settings-content-grid">
          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Create Account</h3><p>Register a new account.</p></div></div>
            <form className="settings-form" onSubmit={handleSignup}>
              <label className="settings-label">First Name<input className="settings-input" type="text" name="first_name" value={signupForm.first_name} onChange={handleSignupChange} required /></label>
              <label className="settings-label">Last Name<input className="settings-input" type="text" name="last_name" value={signupForm.last_name} onChange={handleSignupChange} required /></label>
              <label className="settings-label">Email<input className="settings-input" type="email" name="email" value={signupForm.email} onChange={handleSignupChange} required /></label>
              <label className="settings-label">Password<input className="settings-input" type="password" name="password" value={signupForm.password} onChange={handleSignupChange} required /></label>
              <button className="settings-button settings-button-primary" type="submit" disabled={authLoading}>{authLoading ? "Submitting..." : "Sign Up"}</button>
            </form>
          </div>

          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Login</h3><p>Sign in to your account.</p></div></div>
            <form className="settings-form" onSubmit={handleLogin}>
              <label className="settings-label">Email<input className="settings-input" type="email" name="email" value={loginForm.email} onChange={handleLoginChange} required /></label>
              <label className="settings-label">Password<input className="settings-input" type="password" name="password" value={loginForm.password} onChange={handleLoginChange} required /></label>
              <div className="settings-card-actions">
                <button className="settings-button settings-button-primary" type="submit" disabled={authLoading}>{authLoading ? "Submitting..." : "Log In"}</button>
                <button className="settings-button settings-button-secondary" type="button" onClick={handleLogout}>Log Out</button>
              </div>
            </form>
          </div>

          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Current User</h3><p>Your logged-in account details.</p></div></div>
            <div className="settings-card-body">
              {currentUserLoading ? <p>Loading current user...</p> : currentUser ? (
                <div className="settings-info-block">
                  <p><strong>Email:</strong> {currentUser.email || "N/A"}</p>
                  <p><strong>ID:</strong> {currentUser.id || "N/A"}</p>
                </div>
              ) : <p>No logged-in user found.</p>}
            </div>
            <div className="settings-card-actions">
              <button className="settings-button settings-button-refresh" onClick={fetchCurrentUser} disabled={currentUserLoading} type="button">Refresh</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderSectionContent() {
    if (activeSection === "account") return renderAccountSection();
    if (activeSection === "currentConfig") return renderCurrentConfigSection();

    if (activeSection === "privacy") {
      return (
        <div className="settings-section-panel">
          <h2>Privacy Settings</h2>
          <p className="settings-section-description">Manage excluded folders and file types.</p>
          {(message || error) && (
            <div className="settings-alerts">
              {message && <div className="settings-alert settings-alert-success">{message}</div>}
              {error && <div className="settings-alert settings-alert-error">{error}</div>}
            </div>
          )}
          {privacyLoading ? <p>Loading privacy settings...</p> : (
            <div className="settings-content-grid">
              <div className="settings-card">
                <div className="settings-card-header"><div><h3>Excluded Folders</h3><p>Folders listed here will be ignored by the system.</p></div></div>
                <div className="settings-card-body">
                  <div className="settings-inline-form">
                    <input className="settings-input" type="text" placeholder="Enter folder path" value={newExcludedFolder} onChange={e => setNewExcludedFolder(e.target.value)} onKeyDown={e => e.key === "Enter" && addExcludedFolder()} />
                    <button className="settings-button settings-button-primary" type="button" onClick={addExcludedFolder}>Add</button>
                  </div>
                  {privacySettings.excluded_folders.length > 0 ? (
                    <ul className="settings-list">
                      {privacySettings.excluded_folders.map((folder, i) => (
                        <li key={`${folder}-${i}`} className="settings-list-item-row">
                          <span>{folder}</span>
                          <button className="settings-button settings-button-secondary" type="button" onClick={() => removeExcludedFolder(folder)}>Remove</button>
                        </li>
                      ))}
                    </ul>
                  ) : <p>No excluded folders set.</p>}
                </div>
              </div>

              <div className="settings-card">
                <div className="settings-card-header"><div><h3>Excluded File Types</h3><p>File types listed here will be skipped during scanning.</p></div></div>
                <div className="settings-card-body">
                  <div className="settings-inline-form">
                    <input className="settings-input" type="text" placeholder="Enter file type, e.g. .log" value={newExcludedFileType} onChange={e => setNewExcludedFileType(e.target.value)} onKeyDown={e => e.key === "Enter" && addExcludedFileType()} />
                    <button className="settings-button settings-button-primary" type="button" onClick={addExcludedFileType}>Add</button>
                  </div>
                  {privacySettings.excluded_file_types.length > 0 ? (
                    <ul className="settings-list">
                      {privacySettings.excluded_file_types.map((fileType, i) => (
                        <li key={`${fileType}-${i}`} className="settings-list-item-row">
                          <span>{fileType}</span>
                          <button className="settings-button settings-button-secondary" type="button" onClick={() => removeExcludedFileType(fileType)}>Remove</button>
                        </li>
                      ))}
                    </ul>
                  ) : <p>No excluded file types set.</p>}
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }

    if (activeSection === "consent") {
      return (
        <div className="settings-section-panel">
          <h2>Consent Settings</h2>
          <p className="settings-section-description">Manage your file access and AI consent preferences.</p>
          {(message || error) && (
            <div className="settings-alerts">
              {message && <div className="settings-alert settings-alert-success">{message}</div>}
              {error && <div className="settings-alert settings-alert-error">{error}</div>}
            </div>
          )}
          <div className="settings-content-grid">
            <div className="settings-card">
              <div className="settings-card-header">
                <div><h3>Basic File Access Consent</h3><p>Allows the application to access and analyze files you choose.</p></div>
                {renderStatusBadge(basicConsent, loadingBasic)}
              </div>
              <div className="settings-card-body">
                <ul className="settings-list">
                  <li>Read selected files and folders</li>
                  <li>Extract metadata for analysis</li>
                  <li>Store consent status in your local system</li>
                </ul>
              </div>
              <div className="settings-card-actions">
                <button className="settings-button settings-button-primary" onClick={grantBasicConsent} disabled={loadingBasic || updatingBasic || basicConsent}>{updatingBasic && !basicConsent ? "Saving..." : "Grant Consent"}</button>
                <button className="settings-button settings-button-secondary" onClick={revokeBasicConsent} disabled={loadingBasic || updatingBasic || !basicConsent}>{updatingBasic && basicConsent ? "Saving..." : "Revoke Consent"}</button>
              </div>
            </div>

            <div className="settings-card">
              <div className="settings-card-header">
                <div><h3>AI Service Consent</h3><p>Allows the application to use AI-powered features for enhanced analysis.</p></div>
                {renderStatusBadge(aiConsent, loadingAi)}
              </div>
              <div className="settings-card-body">
                <ul className="settings-list">
                  <li>Enable AI-generated summaries</li>
                  <li>Support intelligent extraction and analysis</li>
                  <li>Allow use of configured AI services</li>
                </ul>
              </div>
              <div className="settings-card-actions">
                <button className="settings-button settings-button-primary" onClick={grantAiConsent} disabled={loadingAi || updatingAi || aiConsent}>{updatingAi && !aiConsent ? "Saving..." : "Grant Consent"}</button>
                <button className="settings-button settings-button-secondary" onClick={revokeAiConsent} disabled={loadingAi || updatingAi || !aiConsent}>{updatingAi && aiConsent ? "Saving..." : "Revoke Consent"}</button>
              </div>
            </div>
          </div>
          <div className="settings-footer">
            <button className="settings-button settings-button-refresh" onClick={fetchConsentStatuses} disabled={loadingBasic || loadingAi}>Refresh Status</button>
          </div>
        </div>
      );
    }

    return <div className="settings-section-panel"><h2>Settings</h2></div>;
  }

  return (
    <div className="settings-page">
      <div className="settings-layout">
        <aside className="settings-sidebar">
          <div className="settings-sidebar-header">
            <div className="settings-sidebar-title-row">
              <h1>Settings</h1>
              <button className="settings-theme-toggle" onClick={toggleTheme} title="Toggle theme">
                {theme === "dark" ? "☀️" : "🌙"}
              </button>
            </div>
            <p>Choose a section</p>
          </div>
          <nav className="settings-nav">
            {[
              ["account", "Account Settings"],
              ["privacy", "Privacy"],
              ["consent", "Consent"],
              ["currentConfig", "Current Configuration"],
            ].map(([key, label]) => (
              <button key={key} className={`settings-nav-item ${activeSection === key ? "active" : ""}`} onClick={() => setActiveSection(key)}>{label}</button>
            ))}
          </nav>
        </aside>
        <main className="settings-main">{renderSectionContent()}</main>
      </div>
    </div>
  );
}