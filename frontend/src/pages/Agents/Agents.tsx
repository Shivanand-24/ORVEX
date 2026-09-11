import { useEffect, useState } from "react";
import {
  Activity,
  Bot,
  CheckCircle2,
  Database,
  Play,
  Plus,
  Search,
  Wrench,
} from "lucide-react";
import Modal from "../../components/common/Modal";
import StatusBadge from "../../components/common/StatusBadge";
import { agentRepository } from "../../services/agentRepository";
import { toastService } from "../../services/toastService";
import type { Agent, AgentDomain } from "../../types/agent";

const DOMAINS: AgentDomain[] = [
  "Security",
  "Research",
  "Data Analytics",
  "Human Resources",
  "Operations",
];

const AVAILABLE_TOOLS = [
  "Document Parser",
  "RAG Retrieval",
  "Summarizer",
  "Metric Tracker",
  "SQL Query Tool",
  "Chart Generator",
  "Policy Lookup",
  "System Health Check",
  "Incident Triage",
  "Vulnerability Audit",
];

function Agents() {
  const [agents, setAgents] = useState(() => agentRepository.list());
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [domainFilter, setDomainFilter] = useState<string>("all");

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [runningAgentId, setRunningAgentId] = useState<string | null>(null);

  // Form states for Create Agent
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState<AgentDomain>("Research");
  const [instructions, setInstructions] = useState("");
  const [selectedTools, setSelectedTools] = useState<string[]>(["Document Parser", "RAG Retrieval"]);
  const [requireApproval, setRequireApproval] = useState(false);

  useEffect(() => {
    return agentRepository.subscribe(() => {
      setAgents(agentRepository.list());
    });
  }, []);

  const activeAgents = agents.filter((agent) => agent.status === "Active");
  const totalExecutions = agents.reduce((total, agent) => total + agent.executions, 0);

  const filteredAgents = agents.filter((agent) => {
    const matchesSearch = `${agent.name} ${agent.description} ${agent.domain}`
      .toLowerCase()
      .includes(searchQuery.trim().toLowerCase());

    const matchesStatus =
      statusFilter === "all"
        ? true
        : agent.status.toLowerCase() === statusFilter.toLowerCase();

    const matchesDomain =
      domainFilter === "all" ? true : agent.domain === domainFilter;

    return matchesSearch && matchesStatus && matchesDomain;
  });

  const handleRunAgent = async (agent: Agent) => {
    setRunningAgentId(agent.id);
    toastService.show("Agent Executing", `Running "${agent.name}" task...`, "info");

    await new Promise((resolve) => setTimeout(resolve, 800));
    await agentRepository.runAgent(agent.id);

    setRunningAgentId(null);
    toastService.show("Execution Completed", `"${agent.name}" finished execution successfully.`, "success");
  };

  const handleToggleStatus = (agent: Agent) => {
    agentRepository.toggleStatus(agent.id);
    const newStatus = agent.status === "Active" ? "Paused" : "Active";
    toastService.show("Status Updated", `Agent "${agent.name}" is now ${newStatus}.`, "info");
  };

  const handleCreateAgent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    agentRepository.create({
      name: name.trim(),
      description: description.trim() || "Autonomous enterprise agent.",
      status: "Active",
      domain,
      owner: "Shivanand (Admin)",
      tools: selectedTools,
      knowledgeSources: ["Company Handbook", "Product Documentation"],
      systemInstructions: instructions.trim() || "Execute domain tasks intelligently.",
      requireApproval,
    });

    toastService.show("Agent Created", `Agent "${name.trim()}" registered in ${domain}.`, "success");

    setName("");
    setDescription("");
    setInstructions("");
    setIsCreateOpen(false);
  };

  const toggleToolSelection = (tool: string) => {
    setSelectedTools((prev) =>
      prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool]
    );
  };

  return (
    <div className="agents-page">
      <div className="page-header">
        <div>
          <h1>AI Agents Workforce</h1>
          <p>Autonomous and semi-autonomous AI workers executing intelligent enterprise tasks.</p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => setIsCreateOpen(true)}
        >
          <Plus size={16} /> Create Agent
        </button>
      </div>

      {/* Summary Stat Cards */}
      <div className="agent-summary">
        <div className="agent-summary-card">
          <div className="summary-icon">
            <Bot size={20} />
          </div>
          <div>
            <span>Total Agents</span>
            <strong>{agents.length}</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <Activity size={20} />
          </div>
          <div>
            <span>Active Workforce</span>
            <strong>{activeAgents.length}</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <Play size={20} />
          </div>
          <div>
            <span>Total Executions</span>
            <strong>{totalExecutions.toLocaleString()}</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <span>Success Rate</span>
            <strong>99.1%</strong>
          </div>
        </div>
      </div>

      {/* Toolbar Filters */}
      <div className="agents-toolbar" style={{ display: "flex", gap: "16px", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
        <div className="topbar-search" style={{ width: "320px", background: "var(--orvex-surface)" }}>
          <Search size={17} />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents by name, domain, or tools..."
          />
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <select
            className="agent-filter"
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
          >
            <option value="all">All Domains</option>
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <select
            className="agent-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
          </select>
        </div>
      </div>

      {/* Agent Roster Grid */}
      <div className="agents-grid" style={{ marginTop: "24px" }}>
        {filteredAgents.map((agent) => (
          <div className="agent-card" key={agent.id}>
            <div className="agent-card-header">
              <div className="agent-identity">
                <div className="agent-avatar">
                  <Bot size={21} />
                </div>

                <div>
                  <h3>{agent.name}</h3>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
                    <StatusBadge status={agent.status} type="agent" />
                    <span style={{ fontSize: "11px", color: "var(--orvex-text-muted)" }}>{agent.domain}</span>
                  </div>
                </div>
              </div>

              <button
                className="secondary-button"
                type="button"
                onClick={() => handleToggleStatus(agent)}
                style={{ fontSize: "11px", padding: "4px 8px", height: "28px" }}
              >
                {agent.status === "Active" ? "Pause" : "Activate"}
              </button>
            </div>

            <p className="agent-description">{agent.description}</p>

            <div style={{ margin: "12px 0", display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {agent.tools.map((tool) => (
                <span
                  key={tool}
                  style={{
                    fontSize: "11px",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#0d1017",
                    border: "1px solid var(--orvex-border)",
                    color: "var(--orvex-text-secondary)",
                  }}
                >
                  <Wrench size={10} style={{ marginRight: "4px" }} />
                  {tool}
                </span>
              ))}
            </div>

            <div className="agent-metrics">
              <div>
                <span>Executions</span>
                <strong>{agent.executions}</strong>
              </div>
              <div>
                <span>Success</span>
                <strong>{agent.successRate}</strong>
              </div>
              <div>
                <span>Last Run</span>
                <strong>{agent.lastRun}</strong>
              </div>
            </div>

            <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
              <button
                className="primary-button"
                type="button"
                onClick={() => handleRunAgent(agent)}
                disabled={runningAgentId === agent.id || agent.status === "Paused"}
                style={{ flex: 1, height: "36px", fontSize: "13px" }}
              >
                <Play size={14} />
                {runningAgentId === agent.id ? "Executing..." : "Run Agent"}
              </button>

              <button
                className="secondary-button"
                type="button"
                onClick={() => setSelectedAgent(agent)}
                style={{ height: "36px", fontSize: "13px", padding: "0 12px" }}
              >
                Inspect
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Inspect Agent Detail Modal */}
      {selectedAgent && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedAgent(null)}
          title={selectedAgent.name}
          subtitle={`Domain: ${selectedAgent.domain} • Owner: ${selectedAgent.owner}`}
        >
          <div className="settings-section">
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <StatusBadge status={selectedAgent.status} type="agent" />
              <span style={{ fontSize: "12px", color: "var(--orvex-text-secondary)" }}>
                Approval Required: <strong>{selectedAgent.requireApproval ? "Yes" : "No"}</strong>
              </span>
            </div>

            <div className="form-group">
              <label>System Instructions & Purpose</label>
              <textarea
                readOnly
                rows={3}
                value={selectedAgent.systemInstructions}
                style={{ background: "#0d1017" }}
              />
            </div>

            <div className="form-group">
              <label>Assigned Tools ({selectedAgent.tools.length})</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {selectedAgent.tools.map((t) => (
                  <span
                    key={t}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "6px",
                      background: "#0d1017",
                      border: "1px solid var(--orvex-border)",
                      fontSize: "12px",
                      color: "var(--orvex-text)",
                    }}
                  >
                    <Wrench size={12} style={{ marginRight: "6px" }} />
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Connected Knowledge Sources</label>
              <div style={{ display: "flex", gap: "8px" }}>
                {selectedAgent.knowledgeSources.map((k) => (
                  <span
                    key={k}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "6px",
                      background: "rgba(139, 92, 246, 0.1)",
                      border: "1px solid rgba(139, 92, 246, 0.3)",
                      fontSize: "12px",
                      color: "var(--orvex-accent-hover)",
                    }}
                  >
                    <Database size={12} style={{ marginRight: "6px" }} />
                    {k}
                  </span>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "24px" }}>
              <button
                className="secondary-button"
                type="button"
                onClick={() => setSelectedAgent(null)}
              >
                Close
              </button>
              <button
                className="primary-button"
                type="button"
                onClick={() => {
                  handleRunAgent(selectedAgent);
                  setSelectedAgent(null);
                }}
              >
                <Play size={14} /> Run Agent Now
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Create Agent Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New AI Agent"
        subtitle="Configure an autonomous digital worker for your workspace."
      >
        <form className="settings-form" onSubmit={handleCreateAgent}>
          <div className="form-group">
            <label htmlFor="agent-name">Agent Name</label>
            <input
              id="agent-name"
              type="text"
              required
              placeholder="e.g. Compliance Sentinel"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="agent-domain">Operational Domain</label>
            <select
              id="agent-domain"
              value={domain}
              onChange={(e) => setDomain(e.target.value as AgentDomain)}
            >
              {DOMAINS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="agent-desc">Agent Description</label>
            <input
              id="agent-desc"
              type="text"
              placeholder="Brief summary of agent responsibilities..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="agent-instructions">System Instructions & Prompt</label>
            <textarea
              id="agent-instructions"
              rows={3}
              placeholder="Define agent behavior, rules, and output standards..."
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Select Agent Tools</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px" }}>
              {AVAILABLE_TOOLS.map((t) => {
                const selected = selectedTools.includes(t);
                return (
                  <button
                    key={t}
                    type="button"
                    className={`secondary-button ${selected ? "active" : ""}`}
                    onClick={() => toggleToolSelection(t)}
                    style={{
                      fontSize: "12px",
                      justifyContent: "flex-start",
                      background: selected ? "rgba(139, 92, 246, 0.15)" : "#0d1017",
                      borderColor: selected ? "var(--orvex-accent)" : "var(--orvex-border)",
                    }}
                  >
                    <Wrench size={12} /> {t}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="toggle-group" style={{ marginTop: "16px" }}>
            <div>
              <strong>Require Human Sign-off</strong>
              <p>Pause execution for admin approval before performing critical actions.</p>
            </div>
            <input
              type="checkbox"
              checked={requireApproval}
              onChange={(e) => setRequireApproval(e.target.checked)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "24px" }}>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </button>
            <button className="primary-button" type="submit">
              Register Agent
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default Agents;
