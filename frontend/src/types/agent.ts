export type AgentStatus = "Active" | "Paused";

export type AgentDomain =
  | "Security"
  | "Research"
  | "Data Analytics"
  | "Human Resources"
  | "Operations";

export type Agent = {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  domain: AgentDomain;
  owner: string;
  tools: string[];
  knowledgeSources: string[];
  systemInstructions: string;
  requireApproval: boolean;
  executions: number;
  successRate: string;
  lastRun: string;
};
