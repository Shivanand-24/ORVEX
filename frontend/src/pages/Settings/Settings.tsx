import { useState } from "react";
import {
  Bell,
  Building2,
  Check,
  Key,
  Globe,
  Sliders,
  Shield,
  Palette,
} from "lucide-react";
import { toastService } from "../../services/toastService";

type SettingsTab =
  | "general"
  | "workspace"
  | "ai"
  | "security"
  | "notifications"
  | "appearance";

function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [workspaceName, setWorkspaceName] = useState("Enterprise Workspace");
  const [description, setDescription] = useState(
    "Primary intelligence and automation hub for cross-department operations."
  );
  const [aiModel, setAiModel] = useState("orvex-v4.2-pro");
  const [strictRag, setStrictRag] = useState(true);
  const [auditLogging, setAuditLogging] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [compactMode, setCompactMode] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    toastService.show(
      "Settings Saved",
      "Your workspace preferences have been updated successfully.",
      "success"
    );
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Configure platform preferences, security rules, and AI parameters.</p>
        </div>

        <button className="primary-button" type="button" onClick={handleSave}>
          <Check size={16} />
          Save Changes
        </button>
      </div>

      <div className="settings-layout">
        {/* Sub Navigation Tabs */}
        <div className="settings-tabs">
          <button
            className={`settings-tab-button ${activeTab === "general" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveTab("general")}
          >
            <Globe size={16} />
            <span>General</span>
          </button>

          <button
            className={`settings-tab-button ${activeTab === "workspace" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveTab("workspace")}
          >
            <Building2 size={16} />
            <span>Workspace & Plan</span>
          </button>

          <button
            className={`settings-tab-button ${activeTab === "ai" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveTab("ai")}
          >
            <Sliders size={16} />
            <span>AI & Copilot</span>
          </button>

          <button
            className={`settings-tab-button ${activeTab === "security" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveTab("security")}
          >
            <Shield size={16} />
            <span>Security & Access</span>
          </button>

          <button
            className={`settings-tab-button ${activeTab === "notifications" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveTab("notifications")}
          >
            <Bell size={16} />
            <span>Notifications</span>
          </button>

          <button
            className={`settings-tab-button ${activeTab === "appearance" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveTab("appearance")}
          >
            <Palette size={16} />
            <span>Appearance</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="settings-content-card">
          {activeTab === "general" && (
            <form className="settings-form" onSubmit={handleSave}>
              <h2>General Settings</h2>
              <p>Basic organization details and localized options.</p>

              <div className="form-group">
                <label htmlFor="ws-name">Workspace Name</label>
                <input
                  id="ws-name"
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="ws-desc">Workspace Description</label>
                <textarea
                  id="ws-desc"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="ws-timezone">System Timezone</label>
                <select id="ws-timezone" defaultValue="UTC">
                  <option value="UTC">UTC (Coordinated Universal Time)</option>
                  <option value="EST">EST (US Eastern Standard Time)</option>
                  <option value="PST">PST (US Pacific Standard Time)</option>
                </select>
              </div>
            </form>
          )}

          {activeTab === "workspace" && (
            <div className="settings-section">
              <h2>Workspace & Plan Details</h2>
              <p>Manage subscription tier, assigned seats, and usage quotas.</p>

              <div className="settings-info-grid">
                <div className="info-card">
                  <span>Current Plan</span>
                  <strong>ORVEX Enterprise</strong>
                  <small>Unlimited execution nodes & priority support</small>
                </div>
                <div className="info-card">
                  <span>Assigned Seats</span>
                  <strong>24 / 50 Seats</strong>
                  <small>26 seats available for invite</small>
                </div>
                <div className="info-card">
                  <span>Execution Quota</span>
                  <strong>1,482,000 / Unlimited</strong>
                  <small>Monthly reset in 18 days</small>
                </div>
              </div>
            </div>
          )}

          {activeTab === "ai" && (
            <div className="settings-section">
              <h2>AI Assistant & Copilot Controls</h2>
              <p>Configure model routing, confidence thresholds, and knowledge search boundaries.</p>

              <div className="form-group">
                <label htmlFor="model-select">Default AI Router Engine</label>
                <select
                  id="model-select"
                  value={aiModel}
                  onChange={(e) => setAiModel(e.target.value)}
                >
                  <option value="orvex-v4.2-pro">ORVEX Intelligence v4.2 Pro (High Accuracy)</option>
                  <option value="orvex-v4.0-fast">ORVEX Speed v4.0 (Low Latency)</option>
                </select>
              </div>

              <div className="toggle-group">
                <div>
                  <strong>Strict RAG Boundary Enforcement</strong>
                  <p>Restrict AI Assistant responses strictly to workspace knowledge sources.</p>
                </div>
                <input
                  type="checkbox"
                  checked={strictRag}
                  onChange={(e) => setStrictRag(e.target.checked)}
                />
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="settings-section">
              <h2>Security & Access Control</h2>
              <p>API keys, audit logging, and single sign-on parameters.</p>

              <div className="form-group">
                <label>Production API Key</label>
                <div className="api-key-box">
                  <code>orvex_live_9f8a2c14b7e381009a2f</code>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() =>
                      toastService.show("API Key Copied", "Key copied to clipboard.", "info")
                    }
                  >
                    <Key size={14} /> Copy Key
                  </button>
                </div>
              </div>

              <div className="toggle-group">
                <div>
                  <strong>Real-time Compliance Audit Logging</strong>
                  <p>Log all agent executions and document queries to the security audit trail.</p>
                </div>
                <input
                  type="checkbox"
                  checked={auditLogging}
                  onChange={(e) => setAuditLogging(e.target.checked)}
                />
              </div>
            </div>
          )}

          {activeTab === "notifications" && (
            <div className="settings-section">
              <h2>Notification Preferences</h2>
              <p>Configure automated alerts for execution failures and system events.</p>

              <div className="toggle-group">
                <div>
                  <strong>Email Digest Alerts</strong>
                  <p>Receive daily executive summaries of agent activity and execution rates.</p>
                </div>
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                />
              </div>
            </div>
          )}

          {activeTab === "appearance" && (
            <div className="settings-section">
              <h2>Appearance & Interface Density</h2>
              <p>Customize layout preferences for ORVEX Pearl Enterprise theme.</p>

              <div className="toggle-group">
                <div>
                  <strong>Compact Data Tables & Cards</strong>
                  <p>Reduce padding in tables and lists for dense monitoring view.</p>
                </div>
                <input
                  type="checkbox"
                  checked={compactMode}
                  onChange={(e) => setCompactMode(e.target.checked)}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;
