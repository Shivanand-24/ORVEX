import { useNavigate } from "react-router-dom";
import { workflowRepository } from "../../services/workflowRepository";

function Workflows() {
  const navigate = useNavigate();
  const workflows = workflowRepository.list();

  const handleCreateWorkflow = () => {
    navigate("/create-workflow");
  };
   

  return (
    <div className="workflows-page">
      {/* Page Header */}

      <div className="page-header">
        <div>
          <h1>Workflows</h1>

          <p>
            Design, automate, and manage intelligent enterprise workflows.
          </p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={handleCreateWorkflow}
        >
          + Create Workflow
        </button>
      </div>

      {/* Workflow Statistics */}

      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Workflows</span>
          <strong>28</strong>
          <small>Across your workspace</small>
        </div>

        <div className="stat-card">
          <span>Active</span>
          <strong>21</strong>
          <small>Currently running</small>
        </div>

        <div className="stat-card">
          <span>Executions</span>
          <strong>1,284</strong>
          <small>Total workflow executions</small>
        </div>

        <div className="stat-card">
          <span>Success Rate</span>
          <strong>98.7%</strong>
          <small>Workflow reliability</small>
        </div>
      </div>

      {/* Workflow List */}

      <section className="dashboard-card workflow-section">
        <div className="card-header">
          <div>
            <h2>Your Workflows</h2>

            <p>
              Manage and monitor your enterprise automation workflows.
            </p>
          </div>
        </div>

        <div className="workflow-list">
          {workflows.map((workflow) => (
            <div className="workflow-item" key={workflow.name}>
              <div className="workflow-main">
                <div className="workflow-icon">
                  WF
                </div>

                <div className="workflow-info">
                  <h3>{workflow.name}</h3>

                  <p>{workflow.description}</p>

                  <div className="workflow-meta">
                    <span
                      className={`workflow-status ${
                        workflow.status === "Active"
                          ? "active"
                          : "draft"
                      }`}
                    >
                      <span className="status-dot"></span>

                      {workflow.status}
                    </span>

                    <span>
                      {workflow.executions} executions
                    </span>

                    <span>
                      Last run: {workflow.lastRun}
                    </span>
                  </div>
                </div>
              </div>

              <button
                className="workflow-action"
                type="button"
                disabled
                title="Opening saved workflows is not available yet"
              >
                Open
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Workflows;
