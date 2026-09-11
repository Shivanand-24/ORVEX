import type { Agent } from "../types/agent";
import { notificationService } from "./notificationService";

export interface AgentRepository {
  list(): readonly Agent[];
  get(id: string): Agent | undefined;
  create(agentData: Omit<Agent, "id" | "executions" | "successRate" | "lastRun">): Agent;
  toggleStatus(id: string): Agent | undefined;
  runAgent(id: string): Promise<boolean>;
  subscribe(listener: () => void): () => void;
}

let agents: Agent[] = [
  {
    id: "agent-research",
    name: "Research Agent",
    description: "Researches and summarizes enterprise knowledge documents with deep citations.",
    status: "Active",
    domain: "Research",
    owner: "Shivanand (Admin)",
    tools: ["Document Parser", "RAG Retrieval", "Summarizer"],
    knowledgeSources: ["Company Handbook", "Product Documentation"],
    systemInstructions:
      "Analyze provided documents, pull relevant knowledge citations, and create structured executive summaries.",
    requireApproval: false,
    executions: 248,
    successRate: "99.2%",
    lastRun: "2 minutes ago",
  },
  {
    id: "agent-data-analyst",
    name: "Data Analyst Agent",
    description: "Analyzes enterprise operational datasets, calculates trends, and flags anomalies.",
    status: "Active",
    domain: "Data Analytics",
    owner: "Data Engineering",
    tools: ["Metric Tracker", "SQL Query Tool", "Chart Generator"],
    knowledgeSources: ["Operations Runbooks"],
    systemInstructions:
      "Query operational metrics, calculate daily/weekly trends, and flag metric anomalies.",
    requireApproval: false,
    executions: 184,
    successRate: "98.5%",
    lastRun: "12 minutes ago",
  },
  {
    id: "agent-hr-intelligence",
    name: "HR Intelligence Agent",
    description: "Assists employees with workplace policy guidance, benefits, and onboarding tasks.",
    status: "Active",
    domain: "Human Resources",
    owner: "HR Operations",
    tools: ["Policy Lookup", "Onboarding Checklist"],
    knowledgeSources: ["Company Handbook"],
    systemInstructions:
      "Answer employee queries regarding workplace policies, benefits, remote-work requirements, and onboarding procedures.",
    requireApproval: true,
    executions: 96,
    successRate: "97.9%",
    lastRun: "28 minutes ago",
  },
  {
    id: "agent-operations",
    name: "Operations Agent",
    description: "Automates routine infrastructure triage, health checks, and runbook procedures.",
    status: "Active",
    domain: "Operations",
    owner: "DevOps Team",
    tools: ["System Health Check", "Incident Triage", "Alert Dispatcher"],
    knowledgeSources: ["Operations Runbooks"],
    systemInstructions:
      "Monitor system health alerts, run diagnostic checks, and initiate triage procedures when anomalies are detected.",
    requireApproval: true,
    executions: 142,
    successRate: "99.6%",
    lastRun: "1 hour ago",
  },
  {
    id: "agent-security-review",
    name: "Security Review Agent",
    description: "Audits access permissions, monitors compliance policies, and flags vulnerabilities.",
    status: "Active",
    domain: "Security",
    owner: "InfoSec Team",
    tools: ["Vulnerability Audit", "Access Control Analyzer", "Compliance Check"],
    knowledgeSources: ["Company Handbook", "Operations Runbooks"],
    systemInstructions:
      "Perform automated security compliance scans against access policies and flag elevated privilege exceptions.",
    requireApproval: true,
    executions: 73,
    successRate: "100%",
    lastRun: "3 hours ago",
  },
];

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export const agentRepository: AgentRepository = {
  list: () => agents,

  get: (id: string) => agents.find((a) => a.id === id),

  create: (agentData) => {
    const newAgent: Agent = {
      ...agentData,
      id: `agent-${Date.now()}`,
      executions: 0,
      successRate: "100%",
      lastRun: "Never",
    };
    agents = [newAgent, ...agents];
    notificationService.addNotification({
      type: "agent",
      title: "New Agent Created",
      message: `Agent "${newAgent.name}" was registered in ${newAgent.domain}.`,
      link: "/agents",
    });
    notify();
    return newAgent;
  },

  toggleStatus: (id: string) => {
    const agent = agents.find((a) => a.id === id);
    if (!agent) return undefined;

    const updated: Agent = {
      ...agent,
      status: agent.status === "Active" ? "Paused" : "Active",
    };
    agents = agents.map((a) => (a.id === id ? updated : a));
    notify();
    return updated;
  },

  runAgent: async (id: string) => {
    const agent = agents.find((a) => a.id === id);
    if (!agent) return false;

    // Increment execution count & update last run
    const updated: Agent = {
      ...agent,
      executions: agent.executions + 1,
      lastRun: "Just now",
    };

    agents = agents.map((a) => (a.id === id ? updated : a));
    notify();

    notificationService.addNotification({
      type: "agent",
      title: "Agent Execution Completed",
      message: `Agent "${agent.name}" executed successfully.`,
      link: "/agents",
    });

    return true;
  },

  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
