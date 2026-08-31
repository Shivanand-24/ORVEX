import {
  Bot,
  MoreVertical,
  Play,
  Activity,
  Clock,
} from "lucide-react";

const agents = [
  {
    name: "Research Agent",
    description: "Researches and summarizes enterprise knowledge.",
    status: "Active",
    executions: 248,
    lastRun: "2 minutes ago",
  },
  {
    name: "Data Analyst",
    description: "Analyzes enterprise datasets and generates insights.",
    status: "Active",
    executions: 184,
    lastRun: "12 minutes ago",
  },
  {
    name: "HR Intelligence",
    description: "Analyzes employee information and HR-related data.",
    status: "Active",
    executions: 96,
    lastRun: "28 minutes ago",
  },
  {
    name: "Operations Agent",
    description: "Automates operational tasks and business processes.",
    status: "Paused",
    executions: 142,
    lastRun: "1 hour ago",
  },
];

function Agents() {
  return (
    <div className="agents-page">
      <div className="page-header">
        <div>
          <h1>Agents</h1>
          <p>
            AI-powered workers that execute intelligent enterprise tasks.
          </p>
        </div>

        <button className="primary-button" type="button">
          + Create Agent
        </button>
      </div>

      <div className="agent-summary">
        <div className="agent-summary-card">
          <div className="summary-icon">
            <Bot size={20} />
          </div>

          <div>
            <span>Total Agents</span>
            <strong>12</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <Activity size={20} />
          </div>

          <div>
            <span>Active Agents</span>
            <strong>9</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <Play size={20} />
          </div>

          <div>
            <span>Total Executions</span>
            <strong>1,284</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <Clock size={20} />
          </div>

          <div>
            <span>Success Rate</span>
            <strong>98.7%</strong>
          </div>
        </div>
      </div>

      <div className="agents-toolbar">
        <div>
          <h2>Your Agents</h2>
          <p>Manage and monitor your AI workforce.</p>
        </div>

        <select className="agent-filter" defaultValue="all">
          <option value="all">All Agents</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
        </select>
      </div>

      <div className="agents-grid">
        {agents.map((agent) => (
          <div className="agent-card" key={agent.name}>
            <div className="agent-card-header">
              <div className="agent-identity">
                <div className="agent-avatar">
                  <Bot size={21} />
                </div>

                <div>
                  <h3>{agent.name}</h3>

                  <span
                    className={
                      agent.status === "Active"
                        ? "agent-status active"
                        : "agent-status paused"
                    }
                  >
                    <span className="agent-status-dot"></span>
                    {agent.status}
                  </span>
                </div>
              </div>

              <button
                className="agent-menu-button"
                type="button"
                aria-label={`More options for ${agent.name}`}
              >
                <MoreVertical size={18} />
              </button>
            </div>

            <p className="agent-description">
              {agent.description}
            </p>

            <div className="agent-metrics">
              <div>
                <span>Executions</span>
                <strong>{agent.executions}</strong>
              </div>

              <div>
                <span>Last Run</span>
                <strong>{agent.lastRun}</strong>
              </div>
            </div>

            <button className="agent-view-button" type="button">
              View Agent
              <span>→</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Agents;