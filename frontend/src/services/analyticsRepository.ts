import { agentRepository } from "./agentRepository";
import { knowledgeRepository } from "./knowledgeRepository";
import { workflowRepository } from "./workflowRepository";

export type TimeRange = "7d" | "30d" | "90d";

export interface AnalyticsSummary {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  successRate: string;
  activeAgents: number;
  activeWorkflows: number;
  ragReadyDocuments: number;
  avgLatencyMs: number;
}

export interface ExecutionTrendPoint {
  date: string;
  executions: number;
  successes: number;
  failures: number;
}

export interface AnalyticsRepository {
  getSummary(range?: TimeRange): AnalyticsSummary;
  getTrends(range?: TimeRange): ExecutionTrendPoint[];
  subscribe(listener: () => void): () => void;
}

export const analyticsRepository: AnalyticsRepository = {
  getSummary: (_range = "30d") => {
    const agents = agentRepository.list();
    const workflows = workflowRepository.list();
    const docs = knowledgeRepository.listDocuments();

    const totalAgentExecutions = agents.reduce((sum, a) => sum + a.executions, 0);
    const totalWorkflowExecutions = workflows.reduce((sum, w) => sum + w.executions, 0);
    const totalExecutions = totalAgentExecutions + totalWorkflowExecutions + 1420;

    const successfulExecutions = Math.round(totalExecutions * 0.988);
    const failedExecutions = totalExecutions - successfulExecutions;

    const activeAgents = agents.filter((a) => a.status === "Active").length;
    const activeWorkflows = workflows.filter((w) => w.status === "Active").length;
    const ragReadyDocuments = docs.filter((d) => d.readiness === "Indexed").length;

    return {
      totalExecutions,
      successfulExecutions,
      failedExecutions,
      successRate: "98.8%",
      activeAgents,
      activeWorkflows,
      ragReadyDocuments,
      avgLatencyMs: 340,
    };
  },

  getTrends: (range = "30d") => {
    if (range === "7d") {
      return [
        { date: "Mon", executions: 320, successes: 318, failures: 2 },
        { date: "Tue", executions: 450, successes: 445, failures: 5 },
        { date: "Wed", executions: 410, successes: 405, failures: 5 },
        { date: "Thu", executions: 580, successes: 574, failures: 6 },
        { date: "Fri", executions: 620, successes: 615, failures: 5 },
        { date: "Sat", executions: 240, successes: 239, failures: 1 },
        { date: "Sun", executions: 290, successes: 288, failures: 2 },
      ];
    }

    if (range === "90d") {
      return [
        { date: "Month 1", executions: 8400, successes: 8300, failures: 100 },
        { date: "Month 2", executions: 11200, successes: 11050, failures: 150 },
        { date: "Month 3", executions: 14800, successes: 14620, failures: 180 },
      ];
    }

    // Default 30d (4 weeks)
    return [
      { date: "Week 1", executions: 2100, successes: 2075, failures: 25 },
      { date: "Week 2", executions: 2850, successes: 2820, failures: 30 },
      { date: "Week 3", executions: 3400, successes: 3360, failures: 40 },
      { date: "Week 4", executions: 4100, successes: 4055, failures: 45 },
    ];
  },

  subscribe: (listener: () => void) => {
    const unsubAgent = agentRepository.subscribe(listener);
    const unsubWf = workflowRepository.subscribe(listener);
    const unsubKb = knowledgeRepository.subscribe(listener);

    return () => {
      unsubAgent();
      unsubWf();
      unsubKb();
    };
  },
};
