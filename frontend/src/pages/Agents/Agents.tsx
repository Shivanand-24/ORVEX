import {
  Bot,
  MoreVertical,
  Play,
  Activity,
  Clock,
} from "lucide-react";
import { agentRepository } from "../../services/agentRepository";

function Agents() {
  const agents = agentRepository.list();
  const activeAgents = agents.filter((agent) => agent.status === "Active");
  const totalExecutions = agents.reduce(
    (total, agent) => total + agent.executions,
    0,
  );

  return (
    <div className="agents-page">
      <div className="page-header">
        <div>
          <h1>Agents</h1>
          <p>
            AI-powered workers that execute intelligent enterprise tasks.
          </p>
        </div>

        <button
          className="primary-button"
          type="button"
          disabled
          title="Agent creation is not available yet"
        >
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
            <strong>{agents.length}</strong>
          </div>
        </div>

        <div className="agent-summary-card">
          <div className="summary-icon">
            <Activity size={20} />
          </div>

          <div>
            <span>Active Agents</span>
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
            <Clock size={20} />
          </div>

          <div>
            <span>Success Rate</span>
            <strong>—</strong>
          </div>
        </div>
      </div>

      <div className="agents-toolbar">
        <div>
          <h2>Your Agents</h2>
          <p>Manage and monitor your AI workforce.</p>
        </div>

        <select
          className="agent-filter"
          defaultValue="all"
          disabled
          title="Filtering is not available yet"
        >
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
                disabled
                title="Agent options are not available yet"
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

            <button
              className="agent-view-button"
              type="button"
              disabled
              title="Agent details are not available yet"
            >
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
