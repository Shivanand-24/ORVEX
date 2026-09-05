export type WorkflowStatus = "Active" | "Draft";

export type Workflow = {
  name: string;
  description: string;
  status: WorkflowStatus;
  executions: number;
  lastRun: string;
};

export type WorkflowStepType =
  | "Trigger"
  | "AI Agent"
  | "Action"
  | "Condition";

export type WorkflowStepConfig = {
  agent?: string;
  task?: string;
  trigger?: string;
  action?: string;
  condition?: string;
};

export type WorkflowStep = {
  id: number;
  type: WorkflowStepType;
  title: string;
  description: string;
  config: WorkflowStepConfig;
};
