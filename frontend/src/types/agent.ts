export type AgentStatus = "Active" | "Paused";

export type Agent = {
  name: string;
  description: string;
  status: AgentStatus;
  executions: number;
  lastRun: string;
};
