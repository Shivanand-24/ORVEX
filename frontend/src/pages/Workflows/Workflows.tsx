import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Play,
  Plus,
  Workflow as WorkflowIcon,
} from "lucide-react";
import Modal from "../../components/common/Modal";
import StatusBadge from "../../components/common/StatusBadge";
import { workflowRepository } from "../../services/workflowRepository";
import { toastService } from "../../services/toastService";
import type { Workflow } from "../../types/workflow";

type StatusTab = "all" | "active" | "draft" | "paused";

function Workflows() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState(() => workflowRepository.list());
  const [statusTab, setStatusTab] = useState<StatusTab>("all");
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [runningWfId, setRunningWfId] = useState<string | null>(null);

  useEffect(() => {
    return workflowRepository.subscribe(() => {
      setWorkflows(workflowRepository.list());
    });
  }, []);

  const activeWorkflows = workflows.filter((w) => w.status === "Active");
  const totalExecutions = workflows.reduce((sum, w) => sum + w.executions, 0);

  const filteredWorkflows = workflows.filter((w) => {
    if (statusTab === "all") return true;
    return w.status.toLowerCase() === statusTab;
  });

  const handleRunWorkflow = async (wf: Workflow) => {
    setRunningWfId(wf.id);
    toastService.show("Workflow Running", `Executing "${wf.name}" pipeline...`, "info");

    await new Promise((resolve) => setTimeout(resolve, 800));
    await workflowRepository.runWorkflow(wf.id);

    setRunningWfId(null);
    toastService.show(
      "Execution Succeeded",
      `Workflow "${wf.name}" completed all ${wf.steps.length} steps.`,
      "success"
    );
  };

  const handleToggleStatus = (wf: Workflow) => {
    workflowRepository.toggleStatus(wf.id);
    const newStatus = wf.status === "Active" ? "Paused" : "Active";
    toastService.show("Workflow Updated", `Workflow "${wf.name}" is now ${newStatus}.`, "info");
  };

  return (
    <div className="workflows-page">
      <div className="page-header">
        <div>
          <h1>Workflows Automation</h1>
          <p>Design, automate, and orchestrate intelligent enterprise workflows.</p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => navigate("/create-workflow")}
        >
          <Plus size={16} /> Create Workflow
        </button>
      </div>

      {/* Workflow Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Workflows</span>
          <strong>{workflows.length}</strong>
          <small>Across your workspace</small>
        </div>

        <div className="stat-card">
          <span>Active Pipelines</span>
          <strong>{activeWorkflows.length}</strong>
          <small>Running on trigger</small>
        </div>

        <div className="stat-card">
          <span>Total Executions</span>
          <strong>{totalExecutions.toLocaleString()}</strong>
          <small>Workflow step runs</small>
        </div>

        <div className="stat-card">
          <span>Reliability</span>
          <strong>99.3%</strong>
          <small>Success rate</small>
        </div>
      </div>

      {/* Workflow List Section */}
      <section className="dashboard-card workflow-section">
        <div className="card-header">
          <div>
            <h2>Your Workflows</h2>
            <p>Manage and monitor your enterprise automation pipelines.</p>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            {(["all", "active", "draft", "paused"] as StatusTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                className={`secondary-button ${statusTab === tab ? "active" : ""}`}
                onClick={() => setStatusTab(tab)}
                style={{
                  fontSize: "12px",
                  padding: "4px 10px",
                  height: "30px",
                  textTransform: "capitalize",
                  background: statusTab === tab ? "var(--orvex-surface-2)" : "transparent",
                  borderColor: statusTab === tab ? "var(--orvex-accent)" : "transparent",
                }}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div className="workflow-list">
          {filteredWorkflows.map((wf) => (
            <div className="workflow-item" key={wf.id}>
              <div className="workflow-main">
                <div className="workflow-icon">
                  <WorkflowIcon size={20} />
                </div>

                <div className="workflow-info">
                  <h3>{wf.name}</h3>
                  <p>{wf.description}</p>

                  <div className="workflow-meta">
                    <StatusBadge status={wf.status} type="workflow" />
                    <span>Trigger: {wf.trigger}</span>
                    <span>{wf.steps.length} steps</span>
                    <span>{wf.executions} executions</span>
                    <span>Last run: {wf.lastRun}</span>
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setSelectedWorkflow(wf)}
                  style={{ fontSize: "12px", padding: "4px 10px", height: "34px" }}
                >
                  Inspect Steps
                </button>

                <button
                  className="primary-button"
                  type="button"
                  onClick={() => handleRunWorkflow(wf)}
                  disabled={runningWfId === wf.id || wf.status === "Paused"}
                  style={{ fontSize: "12px", padding: "4px 12px", height: "34px" }}
                >
                  <Play size={14} />
                  {runningWfId === wf.id ? "Running..." : "Run Now"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Inspect Workflow Steps Modal */}
      {selectedWorkflow && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedWorkflow(null)}
          title={selectedWorkflow.name}
          subtitle={`Trigger: ${selectedWorkflow.trigger} • ${selectedWorkflow.steps.length} configured steps`}
        >
          <div className="settings-section">
            <p style={{ fontSize: "13px", color: "var(--orvex-text-secondary)", marginBottom: "20px" }}>
              {selectedWorkflow.description}
            </p>

            <div className="workflow-steps">
              {selectedWorkflow.steps.map((step, idx) => (
                <div key={step.id} style={{ marginBottom: "12px" }}>
                  <div className="workflow-step" style={{ background: "#f6f7f9", border: "1px solid #dde1e7" }}>
                    <div className="step-number">{idx + 1}</div>
                    <div className="step-content">
                      <strong>{step.title}</strong>
                      <span>{step.description}</span>
                    </div>
                    <span className="step-type">{step.type}</span>
                  </div>
                  {idx < selectedWorkflow.steps.length - 1 && (
                    <div className="workflow-connector" />
                  )}
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "24px" }}>
              <button
                className="secondary-button"
                type="button"
                onClick={() => handleToggleStatus(selectedWorkflow)}
              >
                {selectedWorkflow.status === "Active" ? "Pause Workflow" : "Activate Workflow"}
              </button>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setSelectedWorkflow(null)}
                >
                  Close
                </button>
                <button
                  className="primary-button"
                  type="button"
                  onClick={() => {
                    handleRunWorkflow(selectedWorkflow);
                    setSelectedWorkflow(null);
                  }}
                >
                  <Play size={14} /> Run Workflow
                </button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default Workflows;
