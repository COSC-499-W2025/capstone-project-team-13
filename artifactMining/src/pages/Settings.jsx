import React, { useEffect, useState } from "react";
import "./Settings.css";

const API_BASE = "http://127.0.0.1:8000";

export default function Settings() {
  const [activeSection, setActiveSection] = useState("consent");

  const [basicConsent, setBasicConsent] = useState(false);
  const [aiConsent, setAiConsent] = useState(false);

  const [loadingBasic, setLoadingBasic] = useState(true);
  const [loadingAi, setLoadingAi] = useState(true);

  const [updatingBasic, setUpdatingBasic] = useState(false);
  const [updatingAi, setUpdatingAi] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeSection === "consent") {
      fetchConsentStatuses();
    }
  }, [activeSection]);

  async function fetchConsentStatuses() {
    setError("");
    setMessage("");

    await Promise.all([fetchBasicConsentStatus(), fetchAiConsentStatus()]);
  }

  async function fetchBasicConsentStatus() {
    try {
      setLoadingBasic(true);

      const response = await fetch(`${API_BASE}/consent/basic-consent-status`);
      if (!response.ok) {
        throw new Error("Failed to fetch basic consent status");
      }

      const data = await response.json();
      const granted =
        data.granted ??
        data.basic_consent_granted ??
        data.status ??
        false;

      setBasicConsent(Boolean(granted));
    } catch (err) {
      console.error(err);
      setError("Could not load basic consent status.");
    } finally {
      setLoadingBasic(false);
    }
  }

  async function fetchAiConsentStatus() {
    try {
      setLoadingAi(true);

      const response = await fetch(`${API_BASE}/consent/ai-consent-status`);
      if (!response.ok) {
        throw new Error("Failed to fetch AI consent status");
      }

      const data = await response.json();
      const granted =
        data.granted ??
        data.ai_consent_granted ??
        data.status ??
        false;

      setAiConsent(Boolean(granted));
    } catch (err) {
      console.error(err);
      setError("Could not load AI consent status.");
    } finally {
      setLoadingAi(false);
    }
  }

  async function grantBasicConsent() {
    try {
      setUpdatingBasic(true);
      setError("");
      setMessage("");

      const response = await fetch(`${API_BASE}/consent/basic-consent-grant`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to grant basic consent");
      }

      setBasicConsent(true);
      setMessage("Basic consent granted successfully.");
    } catch (err) {
      console.error(err);
      setError("Could not grant basic consent.");
    } finally {
      setUpdatingBasic(false);
    }
  }

  async function revokeBasicConsent() {
    try {
      setUpdatingBasic(true);
      setError("");
      setMessage("");

      const response = await fetch(`${API_BASE}/consent/basic-consent-revoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to revoke basic consent");
      }

      setBasicConsent(false);
      setMessage("Basic consent revoked successfully.");
    } catch (err) {
      console.error(err);
      setError("Could not revoke basic consent.");
    } finally {
      setUpdatingBasic(false);
    }
  }

  async function grantAiConsent() {
    try {
      setUpdatingAi(true);
      setError("");
      setMessage("");

      const response = await fetch(`${API_BASE}/consent/ai-consent-grant`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to grant AI consent");
      }

      setAiConsent(true);
      setMessage("AI consent granted successfully.");
    } catch (err) {
      console.error(err);
      setError("Could not grant AI consent.");
    } finally {
      setUpdatingAi(false);
    }
  }

  async function revokeAiConsent() {
    try {
      setUpdatingAi(true);
      setError("");
      setMessage("");

      const response = await fetch(`${API_BASE}/consent/ai-consent-revoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to revoke AI consent");
      }

      setAiConsent(false);
      setMessage("AI consent revoked successfully.");
    } catch (err) {
      console.error(err);
      setError("Could not revoke AI consent.");
    } finally {
      setUpdatingAi(false);
    }
  }

  function renderStatusBadge(isGranted, isLoading) {
    if (isLoading) {
      return (
        <span className="settings-badge settings-badge-loading">
          Loading...
        </span>
      );
    }

    return isGranted ? (
      <span className="settings-badge settings-badge-granted">Granted</span>
    ) : (
      <span className="settings-badge settings-badge-revoked">Not Granted</span>
    );
  }

  function renderSectionContent() {
    if (activeSection === "account") {
      return (
        <div className="settings-section-panel">
          <h2>Account Settings</h2>
          <p className="settings-section-description">
            Manage your account preferences here.
          </p>

          <div className="settings-placeholder-card">
            <h3>Profile Information</h3>
            <p>Name, email, username, and profile preferences can go here.</p>
          </div>

          <div className="settings-placeholder-card">
            <h3>Login & Security</h3>
            <p>Password reset, authentication settings, and security options can go here.</p>
          </div>
        </div>
      );
    }

    if (activeSection === "privacy") {
      return (
        <div className="settings-section-panel">
          <h2>Privacy Settings</h2>
          <p className="settings-section-description">
            Control how data is stored and managed.
          </p>

          <div className="settings-placeholder-card">
            <h3>Data Storage</h3>
            <p>Settings such as file storage, paths, contributor names, and anonymous mode can go here.</p>
          </div>

          <div className="settings-placeholder-card">
            <h3>Visibility</h3>
            <p>Future privacy controls and data preferences can be added here.</p>
          </div>
        </div>
      );
    }

    if (activeSection === "consent") {
      return (
        <div className="settings-section-panel">
          <h2>Consent Settings</h2>
          <p className="settings-section-description">
            Manage your file access and AI consent preferences.
          </p>

          {(message || error) && (
            <div className="settings-alerts">
              {message && (
                <div className="settings-alert settings-alert-success">
                  {message}
                </div>
              )}
              {error && (
                <div className="settings-alert settings-alert-error">
                  {error}
                </div>
              )}
            </div>
          )}

          <div className="settings-content-grid">
            <div className="settings-card">
              <div className="settings-card-header">
                <div>
                  <h3>Basic File Access Consent</h3>
                  <p>
                    Allows the application to access and analyze files you choose.
                  </p>
                </div>
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
                <button
                  className="settings-button settings-button-primary"
                  onClick={grantBasicConsent}
                  disabled={loadingBasic || updatingBasic || basicConsent}
                >
                  {updatingBasic && !basicConsent ? "Saving..." : "Grant Consent"}
                </button>

                <button
                  className="settings-button settings-button-secondary"
                  onClick={revokeBasicConsent}
                  disabled={loadingBasic || updatingBasic || !basicConsent}
                >
                  {updatingBasic && basicConsent ? "Saving..." : "Revoke Consent"}
                </button>
              </div>
            </div>

            <div className="settings-card">
              <div className="settings-card-header">
                <div>
                  <h3>AI Service Consent</h3>
                  <p>
                    Allows the application to use AI-powered features for enhanced analysis.
                  </p>
                </div>
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
                <button
                  className="settings-button settings-button-primary"
                  onClick={grantAiConsent}
                  disabled={loadingAi || updatingAi || aiConsent}
                >
                  {updatingAi && !aiConsent ? "Saving..." : "Grant Consent"}
                </button>

                <button
                  className="settings-button settings-button-secondary"
                  onClick={revokeAiConsent}
                  disabled={loadingAi || updatingAi || !aiConsent}
                >
                  {updatingAi && aiConsent ? "Saving..." : "Revoke Consent"}
                </button>
              </div>
            </div>
          </div>

          <div className="settings-footer">
            <button
              className="settings-button settings-button-refresh"
              onClick={fetchConsentStatuses}
              disabled={loadingBasic || loadingAi}
            >
              Refresh Status
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="settings-section-panel">
        <h2>Settings</h2>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-layout">
        <aside className="settings-sidebar">
          <div className="settings-sidebar-header">
            <h1>Settings</h1>
            <p>Choose a section</p>
          </div>

          <nav className="settings-nav">
            <button
              className={`settings-nav-item ${activeSection === "account" ? "active" : ""}`}
              onClick={() => setActiveSection("account")}
            >
              Account Settings
            </button>

            <button
              className={`settings-nav-item ${activeSection === "privacy" ? "active" : ""}`}
              onClick={() => setActiveSection("privacy")}
            >
              Privacy
            </button>

            <button
              className={`settings-nav-item ${activeSection === "consent" ? "active" : ""}`}
              onClick={() => setActiveSection("consent")}
            >
              Consent
            </button>
          </nav>
        </aside>

        <main className="settings-main">
          {renderSectionContent()}
        </main>
      </div>
    </div>
  );
}