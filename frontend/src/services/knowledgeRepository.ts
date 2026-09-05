import type {
  KnowledgeDocument,
  KnowledgeSource,
} from "../types/knowledge";

export interface KnowledgeRepository {
  listDocuments(): readonly KnowledgeDocument[];
  listSources(): readonly KnowledgeSource[];
}

const sources: readonly KnowledgeSource[] = [
  {
    id: "company-handbook",
    name: "Company Handbook",
    description: "Policies, benefits, and employee guidance.",
  },
  {
    id: "product-docs",
    name: "Product Documentation",
    description: "Product specifications and release information.",
  },
  {
    id: "operations",
    name: "Operations",
    description: "Runbooks, procedures, and operational reports.",
  },
];

const documents: readonly KnowledgeDocument[] = [
  {
    id: "employee-handbook-2026",
    name: "Employee Handbook 2026",
    type: "PDF",
    sourceId: "company-handbook",
    sizeBytes: 2_400_000,
    status: "Ready",
    updatedAt: "Sep 5, 2026",
    summary: "The current employee handbook covering policies, benefits, and workplace standards.",
  },
  {
    id: "remote-work-policy",
    name: "Remote Work Policy",
    type: "DOCX",
    sourceId: "company-handbook",
    sizeBytes: 860_000,
    status: "Ready",
    updatedAt: "Sep 3, 2026",
    summary: "Guidance for eligibility, collaboration expectations, and remote-work security requirements.",
  },
  {
    id: "orvex-product-overview",
    name: "ORVEX Product Overview",
    type: "PDF",
    sourceId: "product-docs",
    sizeBytes: 1_700_000,
    status: "Ready",
    updatedAt: "Sep 2, 2026",
    summary: "A product-level overview of ORVEX capabilities, users, and platform direction.",
  },
  {
    id: "workflow-operations-runbook",
    name: "Workflow Operations Runbook",
    type: "DOCX",
    sourceId: "operations",
    sizeBytes: 1_120_000,
    status: "Processing",
    updatedAt: "Sep 1, 2026",
    summary: "Operational steps for monitoring, triaging, and maintaining workflow executions.",
  },
  {
    id: "monthly-operations-report",
    name: "Monthly Operations Report",
    type: "XLSX",
    sourceId: "operations",
    sizeBytes: 3_600_000,
    status: "Ready",
    updatedAt: "Aug 30, 2026",
    summary: "Monthly operating metrics, service trends, and cross-team action items.",
  },
];

export const knowledgeRepository: KnowledgeRepository = {
  listDocuments: () => documents,
  listSources: () => sources,
};
