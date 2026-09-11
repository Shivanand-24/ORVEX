export type WorkflowStatus = "Active" | "Draft" | "Paused";

export type WorkflowStepType =
  | "Trigger"
  | "AI Agent"
  | "Knowledge Retrieval"
  | "Action"
  | "Condition"
  | "Human Approval";

export type WorkflowStepConfig = {
  agent?: string;
  task?: string;
  trigger?: string;
  action?: string;
  condition?: string;
  sourceId?: string;
  approverRole?: string;
};

export type WorkflowStep = {
  id: number;
  type: WorkflowStepType;
  title: string;
  description: string;
  config: WorkflowStepConfig;
};

export type Workflow = {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  trigger: string;
  executions: number;
  successRate: string;
  lastRun: string;
  updatedAt: string;
  steps: WorkflowStep[];
};
