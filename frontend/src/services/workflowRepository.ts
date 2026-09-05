import type { Workflow } from "../types/workflow";

export interface WorkflowRepository {
  list(): readonly Workflow[];
}

const workflows: readonly Workflow[] = [
  {
    name: "Employee Data Sync",
    description: "Synchronize employee information across enterprise systems.",
    status: "Active",
    executions: 128,
    lastRun: "5 minutes ago",
  },
  {
    name: "Research Intelligence",
    description: "Analyze documents and generate structured research insights.",
    status: "Active",
    executions: 84,
    lastRun: "24 minutes ago",
  },
  {
    name: "Monthly Performance Report",
    description: "Generate automated employee performance reports.",
    status: "Draft",
    executions: 0,
    lastRun: "Not executed",
  },
];

export const workflowRepository: WorkflowRepository = {
  list: () => workflows,
};
