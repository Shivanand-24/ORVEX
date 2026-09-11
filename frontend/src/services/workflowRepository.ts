import type { Workflow } from "../types/workflow";
import { notificationService } from "./notificationService";

export interface WorkflowRepository {
  list(): readonly Workflow[];
  get(id: string): Workflow | undefined;
  create(workflowData: Omit<Workflow, "id" | "executions" | "successRate" | "lastRun" | "updatedAt">): Workflow;
  toggleStatus(id: string): Workflow | undefined;
  runWorkflow(id: string): Promise<boolean>;
  subscribe(listener: () => void): () => void;
}

let workflows: Workflow[] = [
  {
    id: "wf-employee-sync",
    name: "Employee Data Sync",
    description: "Synchronize employee information across enterprise HR and security systems.",
    status: "Active",
    trigger: "Schedule (Daily 02:00 UTC)",
    executions: 128,
    successRate: "99.1%",
    lastRun: "5 minutes ago",
    updatedAt: "Sep 9, 2026",
    steps: [
      {
        id: 1,
        type: "Trigger",
        title: "Daily Cron Trigger",
        description: "Runs automatically every day at 02:00 UTC.",
        config: { trigger: "Schedule" },
      },
      {
        id: 2,
        type: "AI Agent",
        title: "HR Intelligence Agent",
        description: "Cross-checks HR records against workplace policies.",
        config: { agent: "HR Intelligence Agent", task: "Verify active employee rosters" },
      },
      {
        id: 3,
        type: "Action",
        title: "Update Enterprise Database",
        description: "Syncs validated records into main directory.",
        config: { action: "Update Database" },
      },
    ],
  },
  {
    id: "wf-research-intel",
    name: "Research Intelligence Pipeline",
    description: "Analyze ingested documents, extract knowledge snippets, and build structured summaries.",
    status: "Active",
    trigger: "Knowledge Ingest Event",
    executions: 84,
    successRate: "98.8%",
    lastRun: "24 minutes ago",
    updatedAt: "Sep 8, 2026",
    steps: [
      {
        id: 1,
        type: "Trigger",
        title: "Document Ingestion Event",
        description: "Fires whenever a new PDF or DOCX is uploaded.",
        config: { trigger: "Event" },
      },
      {
        id: 2,
        type: "Knowledge Retrieval",
        title: "Retrieve Document Content",
        description: "Extract text sections and index for RAG query.",
        config: { sourceId: "company-handbook" },
      },
      {
        id: 3,
        type: "AI Agent",
        title: "Research Agent",
        description: "Generates document summaries and tags key metadata.",
        config: { agent: "Research Agent", task: "Extract key policies and summaries" },
      },
      {
        id: 4,
        type: "Action",
        title: "Generate Executive Report",
        description: "Publishes summary digest for workspace members.",
        config: { action: "Generate Report" },
      },
    ],
  },
  {
    id: "wf-security-response",
    name: "Security Incident Response",
    description: "Triage infrastructure security alerts, run compliance audits, and request admin approval.",
    status: "Active",
    trigger: "Webhook / Alert Event",
    executions: 42,
    successRate: "100%",
    lastRun: "2 hours ago",
    updatedAt: "Sep 7, 2026",
    steps: [
      {
        id: 1,
        type: "Trigger",
        title: "Alert Webhook",
        description: "Receives alert payloads from security monitors.",
        config: { trigger: "Webhook" },
      },
      {
        id: 2,
        type: "AI Agent",
        title: "Security Review Agent",
        description: "Analyzes threat level and checks compliance runbooks.",
        config: { agent: "Security Review Agent", task: "Audit alert severity" },
      },
      {
        id: 3,
        type: "Human Approval",
        title: "Security Officer Sign-off",
        description: "Requires explicit admin approval before remediation action.",
        config: { approverRole: "Security Officer" },
      },
      {
        id: 4,
        type: "Action",
        title: "Send Incident Alert",
        description: "Notifies SecOps team via email.",
        config: { action: "Send Email" },
      },
    ],
  },
  {
    id: "wf-performance-report",
    name: "Monthly Performance Report",
    description: "Automate monthly aggregation of department metrics and performance analytics.",
    status: "Draft",
    trigger: "Schedule (Monthly 1st)",
    executions: 0,
    successRate: "—",
    lastRun: "Not executed",
    updatedAt: "Sep 5, 2026",
    steps: [
      {
        id: 1,
        type: "Trigger",
        title: "Monthly Trigger",
        description: "Triggers on 1st of every month.",
        config: { trigger: "Schedule" },
      },
      {
        id: 2,
        type: "AI Agent",
        title: "Data Analyst Agent",
        description: "Aggregates workspace metrics.",
        config: { agent: "Data Analyst Agent", task: "Calculate monthly operational metrics" },
      },
      {
        id: 3,
        type: "Action",
        title: "Dispatch Digest Email",
        description: "Sends report to stakeholders.",
        config: { action: "Send Email" },
      },
    ],
  },
];

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export const workflowRepository: WorkflowRepository = {
  list: () => workflows,

  get: (id: string) => workflows.find((w) => w.id === id),

  create: (workflowData) => {
    const newWorkflow: Workflow = {
      ...workflowData,
      id: `wf-${Date.now()}`,
      executions: 0,
      successRate: "100%",
      lastRun: "Never",
      updatedAt: "Just now",
    };
    workflows = [newWorkflow, ...workflows];

    notificationService.addNotification({
      type: "workflow",
      title: "New Workflow Created",
      message: `Workflow "${newWorkflow.name}" was successfully configured.`,
      link: "/workflows",
    });

    notify();
    return newWorkflow;
  },

  toggleStatus: (id: string) => {
    const wf = workflows.find((w) => w.id === id);
    if (!wf) return undefined;

    const updated: Workflow = {
      ...wf,
      status: wf.status === "Active" ? "Paused" : "Active",
      updatedAt: "Just now",
    };
    workflows = workflows.map((w) => (w.id === id ? updated : w));
    notify();
    return updated;
  },

  runWorkflow: async (id: string) => {
    const wf = workflows.find((w) => w.id === id);
    if (!wf) return false;

    const updated: Workflow = {
      ...wf,
      executions: wf.executions + 1,
      lastRun: "Just now",
      updatedAt: "Just now",
    };
    workflows = workflows.map((w) => (w.id === id ? updated : w));
    notify();

    notificationService.addNotification({
      type: "workflow",
      title: "Workflow Run Succeeded",
      message: `Workflow "${wf.name}" completed all ${wf.steps.length} steps.`,
      link: "/workflows",
    });

    return true;
  },

  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
