import { Joyride } from 'react-joyride';
import { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import "./Settings.css";

const API_BASE = "http://127.0.0.1:8000";

export default function Settings({ onLogout }) {
  // Only run walkthrough if not seen
  const [runWalkthrough, setRunWalkthrough] = useState(() => {
    return localStorage.getItem('settings_walkthrough_seen') !== '1';
  });
  // Set flag as soon as walkthrough starts
  useEffect(() => {
    if (runWalkthrough) {
      localStorage.setItem('settings_walkthrough_seen', '1');
    }
  }, [runWalkthrough]);
  const walkthroughSteps = [
    {
      target: 'body',
      placement: 'center',
      title: 'Settings',
      content: 'This page lets you manage your account, privacy, dashboard, and more. Let’s take a quick tour!'
    },
    {
      target: '.settings-nav-item:nth-child(1)',
      placement: 'right',
      title: 'Account Settings',
      content: 'Manage your profile, avatar, and account details here.'
    },
    {
      target: '.settings-nav-item:nth-child(2)',
      placement: 'right',
      title: 'Consent',
      content: 'Grant or revoke file and AI consent for your data.'
    },
    {
      target: '.settings-nav-item:nth-child(3)',
      placement: 'right',
      title: 'Privacy',
      content: 'Configure excluded folders and file types for privacy.'
    },
    {
      target: '.settings-nav-item:nth-child(4)',
      placement: 'right',
      title: 'Dashboard Settings',
      content: 'Customize dashboard display options like emojis, streak, and tips.'
    },
    {
      target: '.settings-nav-item:nth-child(5)',
      placement: 'right',
      title: 'Current Configuration',
      content: 'View a live summary of your current system and privacy settings.'
    },
    {
      target: '.settings-nav-item:nth-child(6)',
      placement: 'right',
      title: 'Community Portfolios',
      content: 'Explore and share public portfolios from the community.'
    },
    {
      target: '.settings-nav-item:nth-child(7)',
      placement: 'right',
      title: 'How to Use the App',
      content: 'Find keyboard shortcuts and feature guides for the app.'
    },
    {
      target: '.settings-nav-item:nth-child(8)',
      placement: 'right',
      title: 'About',
      content: 'Learn more about this app, its creators, and version info.'
    }
  ];
  const [searchParams] = useSearchParams();
  const [signupForm, setSignupForm] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [authLoading, setAuthLoading] = useState(false);
  const [currentUserLoading, setCurrentUserLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [accountMessage, setAccountMessage] = useState("");
  const [accountError, setAccountError] = useState("");
  const [activeSection, setActiveSection] = useState(() => searchParams.get("section") || "account");
  // GitHub username state
  const [githubUsername, setGithubUsername] = useState("");
  const [githubUsernameLoading, setGithubUsernameLoading] = useState(false);
  const [githubUsernameMessage, setGithubUsernameMessage] = useState("");
  const [githubUsernameError, setGithubUsernameError] = useState("");
    // Fetch GitHub username when user loads or logs in
    useEffect(() => {
      async function fetchGithubUsername() {
        setGithubUsernameLoading(true);
        setGithubUsernameError("");
        setGithubUsernameMessage("");
        const token = localStorage.getItem("token");
        if (!token) { setGithubUsername(""); setGithubUsernameLoading(false); return; }
        try {
          const res = await fetch(`${API_BASE}/user/github-username`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (!res.ok) throw new Error("Could not fetch GitHub username");
          const data = await res.json();
          setGithubUsername(data.github_username || "");
        } catch (err) {
          setGithubUsernameError(err.message || "Could not fetch GitHub username");
        } finally {
          setGithubUsernameLoading(false);
        }
      }
      if (currentUser) fetchGithubUsername();
      else setGithubUsername("");
    }, [currentUser]);

    async function handleGithubUsernameSave(e) {
      e.preventDefault();
      setGithubUsernameMessage("");
      setGithubUsernameError("");
      setGithubUsernameLoading(true);
      const token = localStorage.getItem("token");
      try {
        const res = await fetch(`${API_BASE}/user/github-username`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ github_username: githubUsername })
        });
        if (!res.ok) throw new Error("Could not update GitHub username");
        setGithubUsernameMessage("GitHub username updated.");
      } catch (err) {
        setGithubUsernameError(err.message || "Could not update GitHub username");
      } finally {
        setGithubUsernameLoading(false);
      }
    }
  const [showEmojis, setShowEmojis] = useState(() => localStorage.getItem("dash_show_emojis") !== "false");
  const [showStreak, setShowStreak] = useState(() => localStorage.getItem("dash_show_streak") !== "false");
  const [showTip, setShowTip] = useState(() => localStorage.getItem("dash_show_tip") !== "false");

  // ── Profile ──────────────────────────────────────────────────────────────────
  const [avatar, setAvatar] = useState(() => localStorage.getItem("profile_avatar") || null);
  const [avatarDrag, setAvatarDrag] = useState(false);
  const avatarInputRef = useRef(null);

  function handleImageFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = async (ev) => {
      const dataUrl = ev.target.result;
      setAvatar(dataUrl);
      localStorage.setItem("profile_avatar", dataUrl);
      window.dispatchEvent(new CustomEvent("profile-updated"));
      // Persist to backend
      const token = localStorage.getItem("token");
      if (token) {
        fetch(`${API_BASE}/auth/avatar`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ avatar: dataUrl }),
        }).catch(() => {});
      }
    };
    reader.readAsDataURL(file);
  }

  function removeAvatar() {
    setAvatar(null);
    localStorage.removeItem("profile_avatar");
    window.dispatchEvent(new CustomEvent("profile-updated"));
    const token = localStorage.getItem("token");
    if (token) {
      fetch(`${API_BASE}/auth/avatar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ avatar: null }),
      }).catch(() => {});
    }
  }

  // ── Theme ────────────────────────────────────────────────────────────────────
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);


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
      window.dispatchEvent(new CustomEvent("profile-updated"));
    } catch (err) { setAccountError(err.message || "Could not log in."); }
    finally { setAuthLoading(false); }
  }

  async function fetchCurrentUser() {
    setCurrentUserLoading(true); setAccountError("");
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE}/auth/me`, { method: "GET", headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (!response.ok) { if (response.status === 401 || response.status === 403) { setCurrentUser(null); return; } const d = await response.json().catch(() => ({})); throw new Error(d.detail || "Failed to load current user"); }
      const user = await response.json();
      setCurrentUser(user);
      // Restore avatar from backend
      if (user.avatar) {
        setAvatar(user.avatar);
        localStorage.setItem("profile_avatar", user.avatar);
        window.dispatchEvent(new CustomEvent("profile-updated"));
      }
    } catch (err) { setAccountError(err.message || "Could not load current user."); }
    finally { setCurrentUserLoading(false); }
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setAvatar(null);
    setCurrentUser(null);
    setAccountMessage("Logged out successfully."); setAccountError("");
    if (onLogout) onLogout();
    window.dispatchEvent(new CustomEvent("profile-updated"));
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
    function OnOffBadge({ on }) {
      return on
        ? <span className="settings-badge settings-badge-granted">On</span>
        : <span className="settings-badge settings-badge-revoked">Off</span>;
    }

    return (
      <div className="settings-section-panel">
        <h2>Current Configuration</h2>
        <p className="settings-section-description">A live view of all your active settings.</p>

        {currentConfigError && (
          <div className="settings-alerts">
            <div className="settings-alert settings-alert-error">{currentConfigError}</div>
          </div>
        )}
        {!currentConfigLoading && currentConfig && (
          <>
            <h3 style={{ marginBottom: 12, marginTop: 8, fontSize: "1rem", opacity: 0.7 }}>System Configuration</h3>
            <div className="settings-content-grid" style={{ marginBottom: 32 }}>
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
          </>
        )}

        <h3 style={{ marginBottom: 12, fontSize: "1rem", opacity: 0.7 }}>Dashboard Display</h3>
        <div className="settings-content-grid" style={{ marginBottom: 32 }}>
          <div className="settings-card">
            <div className="settings-card-header">
              <div><h3>Emojis</h3><p>Decorative icons shown throughout the dashboard.</p></div>
              <OnOffBadge on={showEmojis} />
            </div>
            <div className="settings-card-body">
              <ul className="settings-list">
                <li>Stat card icons (projects, skills, score, portfolio)</li>
                <li>Streak fire and tip of the day bulb</li>
                <li>Onboarding step icons and empty state icons</li>
              </ul>
            </div>
          </div>

          <div className="settings-card">
            <div className="settings-card-header">
              <div><h3>Daily Streak</h3><p>Tracks how many consecutive days you've visited.</p></div>
              <OnOffBadge on={showStreak} />
            </div>
            <div className="settings-card-body">
              <ul className="settings-list">
                <li>Displays your current login streak</li>
                <li>Motivational prompt to return tomorrow</li>
              </ul>
            </div>
          </div>

          <div className="settings-card">
            <div className="settings-card-header">
              <div><h3>Tip of the Day</h3><p>A daily career or resume tip shown on your dashboard.</p></div>
              <OnOffBadge on={showTip} />
            </div>
            <div className="settings-card-body">
              <ul className="settings-list">
                <li>Rotates daily based on the current date</li>
                <li>Covers resume writing, ATS, and portfolio advice</li>
              </ul>
            </div>
          </div>
        </div>
        <div className="settings-footer">
          <button className="settings-button settings-button-refresh" onClick={fetchCurrentConfiguration} disabled={currentConfigLoading} type="button">
            Refresh System Config
          </button>
        </div>
      </div>
    );
  }

  function renderAccountSection() {
            {/* GitHub Username Card */}
            <div className="settings-card">
              <div className="settings-card-header"><div><h3>GitHub Username</h3><p>Set or update your GitHub username for contributor features.</p></div></div>
              <form className="settings-form" onSubmit={handleGithubUsernameSave}>
                <label className="settings-label">GitHub Username
                  <input
                    className="settings-input"
                    type="text"
                    value={githubUsername}
                    onChange={e => setGithubUsername(e.target.value)}
                    placeholder="e.g. octocat"
                    disabled={githubUsernameLoading || !currentUser}
                    autoComplete="off"
                  />
                </label>
                <div className="settings-card-actions">
                  <button
                    className="settings-button settings-button-primary"
                    type="submit"
                    disabled={githubUsernameLoading || !currentUser}
                  >{githubUsernameLoading ? "Saving..." : "Save Username"}</button>
                </div>
                {(githubUsernameMessage || githubUsernameError) && (
                  <div className="settings-alerts">
                    {githubUsernameMessage && <div className="settings-alert settings-alert-success">{githubUsernameMessage}</div>}
                    {githubUsernameError && <div className="settings-alert settings-alert-error">{githubUsernameError}</div>}
                  </div>
                )}
              </form>
            </div>
    return (
      <div className="settings-section-panel">
        <h2>Account Settings</h2>
        <p className="settings-section-description">Manage your profile picture and account.</p>
        {(accountMessage || accountError) && (
          <div className="settings-alerts">
            {accountMessage && <div className="settings-alert settings-alert-success">{accountMessage}</div>}
            {accountError && <div className="settings-alert settings-alert-error">{accountError}</div>}
          </div>
        )}

        {/* Avatar picker — only when logged in */}
        {currentUser && (
          <div className="settings-avatar-row">
            <div
              className={`settings-avatar-pick${avatarDrag ? " drag-over" : ""}`}
              style={avatar ? { backgroundImage: `url(${avatar})`, backgroundSize: "cover", backgroundPosition: "center" } : {}}
              onDragOver={e => { e.preventDefault(); setAvatarDrag(true); }}
              onDragLeave={() => setAvatarDrag(false)}
              onDrop={e => { e.preventDefault(); setAvatarDrag(false); handleImageFile(e.dataTransfer.files[0]); }}
              onClick={() => avatarInputRef.current?.click()}
              title="Click or drop to set profile picture"
            >
              {!avatar && <span className="settings-avatar-placeholder">👤</span>}
              {avatar && <div className="settings-avatar-overlay">✎</div>}
              <input ref={avatarInputRef} type="file" accept="image/*" style={{ display: "none" }}
                onChange={e => handleImageFile(e.target.files[0])} />
            </div>
            <div className="settings-avatar-info">
              <p>Profile picture</p>
              <p className="settings-avatar-hint">Drag & drop or click to upload. Shows in the navbar.</p>
              {avatar && <button className="settings-button settings-button-secondary" style={{ marginTop: 8 }} onClick={removeAvatar}>Remove</button>}
            </div>
          </div>
        )}

        <div className="settings-content-grid">
          {!currentUser && (
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
          )}

          {!currentUser && (
          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Login</h3><p>Sign in to your account.</p></div></div>
            <form className="settings-form" onSubmit={handleLogin}>
              <label className="settings-label">Email<input className="settings-input" type="email" name="email" value={loginForm.email} onChange={handleLoginChange} required /></label>
              <label className="settings-label">Password<input className="settings-input" type="password" name="password" value={loginForm.password} onChange={handleLoginChange} required /></label>
              <div className="settings-card-actions">
                <button className="settings-button settings-button-primary" type="submit" disabled={authLoading}>{authLoading ? "Submitting..." : "Log In"}</button>
              </div>
            </form>
          </div>
          )}

          {/* GitHub Username Card (now row 2) */}
          <div className="settings-card">
            <div className="settings-card-header"><div><h3>GitHub Username</h3><p>Set or update your GitHub username for contributor features.</p></div></div>
            <form className="settings-form" onSubmit={handleGithubUsernameSave}>
              <label className="settings-label">GitHub Username
                <input
                  className="settings-input"
                  type="text"
                  value={githubUsername}
                  onChange={e => setGithubUsername(e.target.value)}
                  placeholder="e.g. octocat"
                  disabled={githubUsernameLoading || !currentUser}
                  autoComplete="off"
                />
              </label>
              <div className="settings-card-actions">
                <button
                  className="settings-button settings-button-primary"
                  type="submit"
                  disabled={githubUsernameLoading || !currentUser}
                >{githubUsernameLoading ? "Saving..." : "Save Username"}</button>
              </div>
              {(githubUsernameMessage || githubUsernameError) && (
                <div className="settings-alerts">
                  {githubUsernameMessage && <div className="settings-alert settings-alert-success">{githubUsernameMessage}</div>}
                  {githubUsernameError && <div className="settings-alert settings-alert-error">{githubUsernameError}</div>}
                </div>
              )}
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
              {currentUser && <button className="settings-button settings-button-secondary" type="button" onClick={handleLogout}>Log Out</button>}
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderGuideSection() {
    const shortcutGroups = [
      {
        title: "🔍 Search Palette",
        shortcuts: [
          { keys: "⌘K / Ctrl+K", desc: "Open the search palette" },
          { keys: "↑ / ↓", desc: "Navigate results" },
          { keys: "Enter", desc: "Select a result" },
          { keys: "Esc", desc: "Close the palette" },
        ],
      },
      {
        title: "📄 Resume",
        shortcuts: [
          { keys: "⌘S / Ctrl+S", desc: "Save your resume" },
        ],
      },
    ];
    const pages = [
      { icon: "📁", name: "Projects", desc: "View, filter, and manage all your uploaded projects." },
      { icon: "⚡", name: "Skills", desc: "See all skills extracted from your projects over time." },
      { icon: "🎨", name: "Portfolio", desc: "Your ranked master portfolio with stats and visualisations." },
      { icon: "📄", name: "Resume", desc: "Auto-generate a resume from your projects and skills." },
      { icon: "🔬", name: "Analysis", desc: "Run AI analysis to extract descriptions, skills, and scores." },
      { icon: "🏅", name: "Evidence", desc: "Add metrics, feedback, and achievements to each project." },
      { icon: "🎤", name: "Interview Prep", desc: "Generate personalised STAR-format interview answers from your projects." },
      { icon: "🌐", name: "Web Showcase", desc: "A public-facing showcase page you can share with employers." },
    ];
    
    function resetWalkthroughs() {
      [
        'dashboard_walkthrough_seen',
        'upload_walkthrough_seen',
        'resumes_walkthrough_seen',
        'analysis_walkthrough_seen',
        'interview_walkthrough_seen',
        'settings_walkthrough_seen',
        'skills_walkthrough_seen',
        'projects_walkthrough_seen',
        'portfolio_walkthrough_seen',
        'projects_page_walkthrough_seen',
      ].forEach(key => localStorage.removeItem(key));
      window.alert('All walkthroughs have been reset. Reload a page to see its tour again.');
    }
    
    // ...existing code...
    // Render the original guide section, then add the reset button below it
    return (
      <>
        <div className="settings-section-panel">
          <h2>How to Use the App</h2>
          <p className="settings-section-description">A quick guide to getting the most out of NovaHire.</p>

          <div className="settings-card" style={{ marginBottom: 24 }}>
            <div className="settings-card-header"><div><h3>Getting Started</h3></div></div>
            <div className="settings-card-body">
              <ol style={{ paddingLeft: 20, lineHeight: 2, margin: 0 }}>
                <li>Upload a project from the <strong>Projects</strong> page (zip file, text doc, or media).</li>
                <li>Go to <strong>Analysis</strong> and run AI Analysis to generate a description and extract skills.</li>
                <li>Visit <strong>Portfolio</strong> and click <strong>↻ Regenerate</strong> to build your ranked portfolio.</li>
                <li>Head to <strong>Resume</strong> to auto-generate a resume from your data.</li>
                <li>Use <strong>Interview Prep</strong> to get STAR-format answers tailored to your target role.</li>
              </ol>
            </div>
          </div>

          <div className="settings-card" style={{ marginBottom: 24 }}>
            <div className="settings-card-header"><div><h3>Pages Overview</h3></div></div>
            <div className="settings-card-body">
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {pages.map(p => (
                  <div key={p.name} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                    <span style={{ fontSize: "1.2rem", flexShrink: 0 }}>{p.icon}</span>
                    <div>
                      <strong>{p.name}</strong>
                      <p className="text-muted" style={{ margin: 0, fontSize: "0.85rem" }}>{p.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Keyboard Shortcuts</h3></div></div>
            <div className="settings-card-body">
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {shortcutGroups.map(group => (
                  <div key={group.title}>
                    <p style={{ fontWeight: 700, marginBottom: 10, fontSize: "0.88rem" }}>{group.title}</p>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {group.shortcuts.map(s => (
                        <div key={s.keys} style={{ display: "flex", alignItems: "center", gap: 16 }}>
                          <kbd style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 6, padding: "3px 10px", fontSize: "0.82rem", fontFamily: "monospace", color: "#a5b4fc", whiteSpace: "nowrap", flexShrink: 0 }}>{s.keys}</kbd>
                          <span style={{ fontSize: "0.88rem" }}>{s.desc}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <button
          className="settings-button settings-button-secondary"
          style={{ margin: '24px 0 0 0' }}
          onClick={resetWalkthroughs}
        >
          Reset All Walkthroughs
        </button>
      </>
    );
  }
    // The guide section is rendered via guideContent, so remove this duplicate return.

  function renderDashboardSection() {
    function dispatchDashSettings() {
      window.dispatchEvent(new Event("dash-settings-updated"));
    }
    function toggleEmojis() {
      const next = !showEmojis;
      setShowEmojis(next);
      localStorage.setItem("dash_show_emojis", String(next));
      window.dispatchEvent(new Event("dash-emojis-updated"));
      dispatchDashSettings();
    }
    function toggleStreak() {
      const next = !showStreak;
      setShowStreak(next);
      localStorage.setItem("dash_show_streak", String(next));
      dispatchDashSettings();
    }
    function toggleTip() {
      const next = !showTip;
      setShowTip(next);
      localStorage.setItem("dash_show_tip", String(next));
      dispatchDashSettings();
    }

    const checkboxStyle = { width: 18, height: 18, accentColor: "#6366f1" };
    const rowStyle = { display: "flex", alignItems: "center", gap: 12, cursor: "pointer", marginBottom: 12 };

    return (
      <div className="settings-section-panel">
        <h2>Dashboard Settings</h2>
        <p className="settings-section-description">Customise how your dashboard looks and feels.</p>
        <div className="settings-card">
          <div className="settings-card-header">
            <div>
              <h3>Display Options</h3>
              <p>Choose which elements appear on your dashboard.</p>
            </div>
          </div>
          <div className="settings-card-body">
            <label style={rowStyle}>
              <input type="checkbox" checked={showEmojis} onChange={toggleEmojis} style={checkboxStyle} />
              <span>Show emojis</span>
            </label>
            <label style={{ ...rowStyle, marginBottom: 0 }}>
              <input type="checkbox" checked={showStreak} onChange={toggleStreak} style={checkboxStyle} />
              <span>Show daily streak</span>
            </label>
            <label style={{ ...rowStyle, marginBottom: 0, marginTop: 12 }}>
              <input type="checkbox" checked={showTip} onChange={toggleTip} style={checkboxStyle} />
              <span>Show tip of the day</span>
            </label>
          </div>
        </div>
      </div>
    );
  }

  function renderAboutSection() {
    const TECH = [
      { name: "React 19", role: "Frontend UI" },
      { name: "React Router 7", role: "Client-side routing" },
      { name: "Recharts", role: "Data visualizations" },
      { name: "FastAPI", role: "Backend API" },
      { name: "SQLAlchemy", role: "Database ORM" },
      { name: "SQLite", role: "Local database" },
      { name: "Python 3", role: "Backend language" },
      { name: "Vite", role: "Frontend build tool" },
    ];

    const FEATURES = [
      { icon: "📁", title: "Project Upload", desc: "Upload ZIP archives, single files, or entire folders. The system extracts metadata, languages, and structure automatically." },
      { icon: "🔬", title: "AI Analysis", desc: "Run AI-powered analysis to generate project overviews, identify skills, measure technical depth, and track skill growth over time." },
      { icon: "⚡", title: "Skills Tracking", desc: "Automatically detect and aggregate skills across all your projects. See how your expertise has grown over time." },
      { icon: "🎨", title: "Portfolio Builder", desc: "Curate your best projects into a shareable portfolio with custom descriptions, thumbnails, and importance rankings." },
      { icon: "📄", title: "Resume Generator", desc: "Generate tailored resume bullet points from your projects and export them as PDF or DOCX." },
      { icon: "🔒", title: "Privacy First", desc: "All data is stored locally. Nothing is sent to external services without your explicit AI consent." },
    ];

    return (
      <div className="settings-section-panel">
        <div style={{ textAlign: "center", padding: "8px 0 24px" }}>
          <h2 style={{ marginBottom: 8 }}>NovaHire</h2>
          <p className="settings-section-description" style={{ maxWidth: 520, margin: "0 auto 16px" }}>
            A local-first tool for analyzing your projects, discovering your skills,
            and building professional portfolios and resumes, powered by AI.
          </p>
          <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
            <span className="tag accent">v1.0</span>
            <span className="tag">COSC 499 Capstone</span>
            <span className="tag">UBCO, Team 13</span>
          </div>
        </div>

        <div className="settings-content-grid">
          <div className="settings-card">
            <div className="settings-card-header"><div><h3>What it does</h3></div></div>
            <div className="settings-card-body">
              <p className="about-body-text" style={{ lineHeight: 1.7, margin: "0 0 10px" }}>
                NovaHire helps students and developers turn their collection of
                project files into a structured portfolio. Upload any project - code, documents,
                images, or media - and the system automatically extracts metadata, detects
                languages and frameworks, and uses AI to generate descriptions and surface
                demonstrable skills.
              </p>
              <p className="about-body-text" style={{ lineHeight: 1.7, margin: 0 }}>
                The result is a living record of your work that you can draw on to build
                targeted resumes, curate portfolio showcases, and track how your skills
                have grown across projects.
              </p>
            </div>
          </div>

          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Key Features</h3></div></div>
            <div className="settings-card-body">
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {FEATURES.map(f => (
                  <div key={f.title} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                    <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>{f.icon}</span>
                    <div>
                      <div className="about-feature-title" style={{ fontWeight: 600, fontSize: "0.88rem", marginBottom: 2 }}>{f.title}</div>
                      <div className="about-body-text" style={{ fontSize: "0.8rem", lineHeight: 1.55 }}>{f.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Tech Stack</h3></div></div>
            <div className="settings-card-body">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: 8 }}>
                {TECH.map(t => (
                  <div key={t.name} style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(107,114,244,0.2)", borderRadius: 8, padding: "8px 10px" }}>
                    <div className="about-tech-name" style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 2 }}>{t.name}</div>
                    <div className="about-tech-role" style={{ fontSize: "0.72rem" }}>{t.role}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="settings-card">
            <div className="settings-card-header"><div><h3>Privacy and Data</h3></div></div>
            <div className="settings-card-body">
              <p className="about-body-text" style={{ lineHeight: 1.7, margin: "0 0 10px" }}>
                All project files and analysis results are stored in a local SQLite database
                on your machine. No data is uploaded to external servers without your explicit
                consent. AI features require a separately configured AI service and will only
                activate after you grant AI consent in Settings.
              </p>
              <p className="about-body-text" style={{ lineHeight: 1.7, margin: 0 }}>
                You can revoke consent, exclude specific folders or file types, and permanently
                delete any project at any time from the Consent, Privacy, and Deletion Manager sections.
              </p>
            </div>
          </div>
        </div>

        <p style={{ textAlign: "center", color: "#6b7a99", fontSize: "0.8rem", marginTop: 24 }}>
          Built as a capstone project for COSC 499 at the University of British Columbia Okanagan.
          Team 13, 2025-26.
        </p>
      </div>
    );
  }

  function renderCommunitySection() {
    return (
      <div className="settings-section-panel">
        <h2>Community Portfolios</h2>
        <p className="settings-section-description">
          Browse portfolios that other users have chosen to make public. No account required.
        </p>
        <div className="settings-content-grid">
          <div className="settings-card">
            <div className="settings-card-header">
              <div>
                <h3>Browse Public Portfolios</h3>
                <p>See the work of other users who have opted in to public visibility.</p>
              </div>
            </div>
            <div className="settings-card-body">
              <Link
                to="/public-portfolios"
                className="settings-button settings-button-primary"
                style={{ display: "inline-block", textDecoration: "none", marginTop: 8 }}
              >
                View Public Portfolios →
              </Link>
            </div>
          </div>
          {currentUser && (
            <div className="settings-card">
              <div className="settings-card-header">
                <div>
                  <h3>Your Portfolio Visibility</h3>
                  <p>Control whether your portfolio appears in the public listing. Manage this from your Portfolio page.</p>
                </div>
              </div>
              <div className="settings-card-body">
                <a
                  href="/portfolio"
                  className="settings-button settings-button-secondary"
                  style={{ display: "inline-block", textDecoration: "none", marginTop: 8 }}
                >
                  Go to My Portfolio →
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  function renderSectionContent() {
    if (activeSection === "account") return renderAccountSection();
    if (activeSection === "currentConfig") return renderCurrentConfigSection();
    if (activeSection === "guide") return renderGuideSection();
    if (activeSection === "dashboard") return renderDashboardSection();
    if (activeSection === "about") return renderAboutSection();
    if (activeSection === "community") return renderCommunitySection();

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
    <>
      <Joyride
        steps={walkthroughSteps}
        run={runWalkthrough}
        continuous
        showSkipButton
        showProgress
        styles={{
          options: {
            zIndex: 10000,
            primaryColor: 'var(--accent, #6366f1)',
            backgroundColor: 'var(--card-bg, #181a2a)',
            textColor: 'var(--text, #e0e7ff)',
            arrowColor: 'var(--card-bg, #181a2a)',
            overlayColor: 'rgba(30, 34, 54, 0.7)',
            spotlightShadow: '0 0 0 2px var(--accent, #6366f1), 0 1px 8px 0 rgba(99,102,241,0.10)',
          },
          close: {
            color: 'var(--text-muted, #a5b4fc)',
            top: 10,
            right: 10,
          },
        }}
        disableScrolling={true}
        callback={(data) => {
          if (data.status === 'finished' || data.status === 'skipped') {
            localStorage.setItem('settings_walkthrough_seen', '1');
            setRunWalkthrough(false);
          }
        }}
      />
      <div className="settings-page">
      <div className="settings-layout">
        <aside className="settings-sidebar">
          <div className="settings-sidebar-header">
            <h1>Settings</h1>
            <p>Choose a section</p>
            <div className="settings-theme-cards">
              <button
                className={`settings-theme-card settings-theme-card-dark ${theme === "dark" ? "active" : ""}`}
                onClick={() => setTheme("dark")}
                title="Dark mode"
              >
                <span className="theme-card-preview theme-card-dark-preview" />
                <span>Dark</span>
              </button>
              <button
                className={`settings-theme-card settings-theme-card-light ${theme === "light" ? "active" : ""}`}
                onClick={() => setTheme("light")}
                title="Light mode"
              >
                <span className="theme-card-preview theme-card-light-preview" />
                <span>Light</span>
              </button>
            </div>
          </div>
          <nav className="settings-nav">
            {[
              ["account", "Account Settings"],
              ["consent", "Consent"],
              ["privacy", "Privacy"],
              ["dashboard", "Dashboard Settings"],
              ["currentConfig", "Current Configuration"],
              ["community", "Community Portfolios"],
              ["guide", "How to Use"],
              ["about", "About"],
            ].map(([key, label]) => (
              <button key={key} className={`settings-nav-item ${activeSection === key ? "active" : ""}`} onClick={() => setActiveSection(key)}>{label}</button>
            ))}
          </nav>
        </aside>
        <main className="settings-main">{renderSectionContent()}</main>
      </div>
    </div>
  </>);
}