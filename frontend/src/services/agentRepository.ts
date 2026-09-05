import type { Agent } from "../types/agent";

export interface AgentRepository {
  list(): readonly Agent[];
}

const agents: readonly Agent[] = [
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

export const agentRepository: AgentRepository = {
  list: () => agents,
};
