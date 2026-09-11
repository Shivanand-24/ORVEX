import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bot,
  GitBranch,
  Play,
  Plus,
  Settings2,
  Trash2,
  X,
  Zap,
} from "lucide-react";
import type {
  WorkflowStep,
  WorkflowStepConfig,
  WorkflowStepType,
} from "../../types/workflow";
import { workflowRepository } from "../../services/workflowRepository";
import { toastService } from "../../services/toastService";

const stepTemplates: Record<
  WorkflowStepType,
  {
    title: string;
    description: string;
  }
> = {
  Trigger: {
    title: "Trigger",
    description: "Define what starts this workflow.",
  },
  "AI Agent": {
    title: "AI Agent",
    description: "Let an ORVEX AI agent process and analyze information.",
  },
  "Knowledge Retrieval": {
    title: "Knowledge Retrieval",
    description: "Query indexed enterprise knowledge documents.",
  },
  Action: {
    title: "Action",
    description: "Define what should happen after the AI completes its task.",
  },
  Condition: {
    title: "Condition",
    description: "Evaluate information and decide which workflow path to follow.",
  },
  "Human Approval": {
    title: "Human Approval",
    description: "Pause execution for admin sign-off.",
  },
};

function CreateWorkflow() {
  const navigate = useNavigate();

  const [workflowName, setWorkflowName] = useState("");
  const [description, setDescription] = useState("");

  const [steps, setSteps] = useState<WorkflowStep[]>([
    {
      id: 1,
      type: "Trigger",
      title: "Trigger",
      description: "Define what starts this workflow.",
      config: {
        trigger: "Manual",
      },
    },
    {
      id: 2,
      type: "AI Agent",
      title: "AI Agent",
      description: "Let an ORVEX AI agent process and analyze information.",
      config: {
        agent: "Research Agent",
        task: "",
      },
    },
    {
      id: 3,
      type: "Action",
      title: "Action",
      description: "Define what should happen after the AI completes its task.",
      config: {
        action: "Send Notification",
      },
    },
  ]);

  const [showStepMenu, setShowStepMenu] = useState(false);
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);

  const selectedStep = steps.find((step) => step.id === selectedStepId);

  const handleCancel = () => {
    navigate("/workflows");
  };

  const handleSaveWorkflow = () => {
    const title = workflowName.trim() || "Custom Automation Workflow";
    const wfDescription = description.trim() || "Automated enterprise workflow.";
    const firstTrigger = steps.find((s) => s.type === "Trigger")?.config.trigger || "Manual Trigger";

    workflowRepository.create({
      name: title,
      description: wfDescription,
      status: "Active",
      trigger: firstTrigger,
      steps,
    });

    toastService.show(
      "Workflow Saved",
      `Workflow "${title}" was created with ${steps.length} steps.`,
      "success"
    );

    navigate("/workflows");
  };

  const handleAddStep = (type: WorkflowStepType) => {
    const template = stepTemplates[type];

    const newStep: WorkflowStep = {
      id: Date.now(),
      type,
      title: template.title,
      description: template.description,
      config: {},
    };

    setSteps((currentSteps) => [...currentSteps, newStep]);
    setShowStepMenu(false);
  };

  const handleRemoveStep = (id: number) => {
    setSteps((currentSteps) => currentSteps.filter((step) => step.id !== id));
    if (selectedStepId === id) {
      setSelectedStepId(null);
    }
  };

  const updateStepConfig = (key: keyof WorkflowStepConfig, value: string) => {
    if (selectedStepId === null) {
      return;
    }

    setSteps((currentSteps) =>
      currentSteps.map((step) =>
        step.id === selectedStepId
          ? {
              ...step,
              config: {
                ...step.config,
                [key]: value,
              },
            }
          : step
      )
    );
  };

  const getStepIcon = (type: WorkflowStepType) => {
    switch (type) {
      case "Trigger":
        return <Zap size={17} />;
      case "AI Agent":
        return <Bot size={17} />;
      case "Action":
        return <Play size={17} />;
      case "Condition":
        return <GitBranch size={17} />;
      default:
        return <Zap size={17} />;
    }
  };

  const getConfigurationTitle = () => {
    if (!selectedStep) {
      return "Configure Step";
    }
    return `Configure ${selectedStep.type}`;
  };

  return (
    <div className="create-workflow-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Create Workflow</h1>
          <p>Build an intelligent workflow to automate enterprise operations.</p>
        </div>

        <div className="workflow-header-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={handleCancel}
          >
            Cancel
          </button>

          <button
            className="primary-button"
            type="button"
            onClick={handleSaveWorkflow}
          >
            Save Workflow
          </button>
        </div>
      </div>

      {/* Workflow Details */}
      <section className="dashboard-card workflow-builder-card">
        <div className="card-header">
          <div>
            <h2>Workflow Details</h2>
            <p>Define the basic information for your workflow.</p>
          </div>
        </div>

        <div className="workflow-form">
          <div className="form-group">
            <label htmlFor="workflow-name">Workflow Name</label>
            <input
              id="workflow-name"
              type="text"
              value={workflowName}
              onChange={(event) => setWorkflowName(event.target.value)}
              placeholder="e.g. Employee Performance Analysis"
            />
          </div>

          <div className="form-group">
            <label htmlFor="workflow-description">Description</label>
            <textarea
              id="workflow-description"
              rows={4}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Describe what this workflow should accomplish..."
            />
          </div>
        </div>
      </section>

      {/* Workflow Steps */}
      <section className="dashboard-card workflow-builder-card">
        <div className="card-header">
          <div>
            <h2>Workflow Steps</h2>
            <p>Define how ORVEX should execute this workflow.</p>
          </div>
        </div>

        <div className="workflow-steps">
          {steps.map((step, index) => (
            <div key={step.id}>
              <div
                className={`workflow-step ${
                  selectedStepId === step.id ? "workflow-step-selected" : ""
                }`}
                onClick={() => setSelectedStepId(step.id)}
              >
                <div className="step-number">{index + 1}</div>
                <div className="step-icon">{getStepIcon(step.type)}</div>

                <div className="step-content">
                  <strong>{step.title}</strong>
                  <span>{step.description}</span>
                </div>

                <span className="step-type">{step.type}</span>

                <button
                  className="step-config-button"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelectedStepId(step.id);
                  }}
                  aria-label={`Configure ${step.type}`}
                >
                  <Settings2 size={15} />
                </button>

                <button
                  className="step-delete-button"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleRemoveStep(step.id);
                  }}
                  aria-label={`Remove ${step.type} step`}
                >
                  <Trash2 size={15} />
                </button>
              </div>

              {index < steps.length - 1 && <div className="workflow-connector"></div>}
            </div>
          ))}
        </div>

        {/* Add Step Container */}
        <div className="add-step-container">
          {showStepMenu && (
            <div className="step-menu">
              <button type="button" onClick={() => handleAddStep("Trigger")}>
                <Zap size={16} />
                <span>Trigger</span>
              </button>

              <button type="button" onClick={() => handleAddStep("AI Agent")}>
                <Bot size={16} />
                <span>AI Agent</span>
              </button>

              <button type="button" onClick={() => handleAddStep("Action")}>
                <Play size={16} />
                <span>Action</span>
              </button>

              <button type="button" onClick={() => handleAddStep("Condition")}>
                <GitBranch size={16} />
                <span>Condition</span>
              </button>
            </div>
          )}

          <button
            className="add-step-button"
            type="button"
            onClick={() => setShowStepMenu((visible) => !visible)}
          >
            <Plus size={16} />
            {showStepMenu ? "Close" : "Add Step"}
          </button>
        </div>
      </section>

      {/* Configuration Panel */}
      {selectedStep && (
        <section className="dashboard-card workflow-config-card">
          <div className="config-header">
            <div>
              <div className="config-title">
                <div className="step-icon">{getStepIcon(selectedStep.type)}</div>
                <div>
                  <h2>{getConfigurationTitle()}</h2>
                  <p>Configure how this step behaves.</p>
                </div>
              </div>
            </div>

            <button
              className="config-close-button"
              type="button"
              onClick={() => setSelectedStepId(null)}
              aria-label="Close configuration"
            >
              <X size={18} />
            </button>
          </div>

          {selectedStep.type === "Trigger" && (
            <div className="workflow-form">
              <div className="form-group">
                <label htmlFor="trigger-type">Trigger Type</label>
                <select
                  id="trigger-type"
                  value={selectedStep.config.trigger || "Manual"}
                  onChange={(event) => updateStepConfig("trigger", event.target.value)}
                >
                  <option value="Manual">Manual Trigger</option>
                  <option value="Schedule">Scheduled Trigger</option>
                  <option value="Webhook">Webhook</option>
                  <option value="Event">Enterprise Event</option>
                </select>
              </div>
            </div>
          )}

          {selectedStep.type === "AI Agent" && (
            <div className="workflow-form">
              <div className="form-group">
                <label htmlFor="agent-select">AI Agent</label>
                <select
                  id="agent-select"
                  value={selectedStep.config.agent || "Research Agent"}
                  onChange={(event) => updateStepConfig("agent", event.target.value)}
                >
                  <option value="Research Agent">Research Agent</option>
                  <option value="Data Analyst">Data Analyst</option>
                  <option value="HR Intelligence Agent">HR Intelligence Agent</option>
                  <option value="Operations Agent">Operations Agent</option>
                  <option value="Security Review Agent">Security Review Agent</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="agent-task">Agent Task Prompt</label>
                <textarea
                  id="agent-task"
                  rows={4}
                  value={selectedStep.config.task || ""}
                  onChange={(event) => updateStepConfig("task", event.target.value)}
                  placeholder="Describe what the AI agent should analyze or accomplish..."
                />
              </div>
            </div>
          )}

          {selectedStep.type === "Condition" && (
            <div className="workflow-form">
              <div className="form-group">
                <label htmlFor="condition">Condition Expression</label>
                <textarea
                  id="condition"
                  rows={3}
                  value={selectedStep.config.condition || ""}
                  onChange={(event) => updateStepConfig("condition", event.target.value)}
                  placeholder="Example: Employee performance score is below 60"
                />
              </div>
            </div>
          )}

          {selectedStep.type === "Action" && (
            <div className="workflow-form">
              <div className="form-group">
                <label htmlFor="action-select">Action Type</label>
                <select
                  id="action-select"
                  value={selectedStep.config.action || "Send Notification"}
                  onChange={(event) => updateStepConfig("action", event.target.value)}
                >
                  <option value="Send Notification">Send Notification</option>
                  <option value="Send Email">Send Email</option>
                  <option value="Update Database">Update Database</option>
                  <option value="Generate Report">Generate Report</option>
                  <option value="Call API">Call External API</option>
                </select>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default CreateWorkflow;
