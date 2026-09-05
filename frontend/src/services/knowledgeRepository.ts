import type {
  KnowledgeDocument,
  KnowledgeSource,
} from "../types/knowledge";

export interface KnowledgeRepository {
  listDocuments(): readonly KnowledgeDocument[];
  listSources(): readonly KnowledgeSource[];
  startProcessing(documentId: string): KnowledgeDocument | undefined;
  completeProcessing(documentId: string): KnowledgeDocument | undefined;
  failProcessing(documentId: string): KnowledgeDocument | undefined;
  startIndexing(documentId: string): KnowledgeDocument | undefined;
  completeIndexing(documentId: string): KnowledgeDocument | undefined;
  failIndexing(documentId: string): KnowledgeDocument | undefined;
  subscribe(listener: () => void): () => void;
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

let documents: readonly KnowledgeDocument[] = [
  {
    id: "employee-handbook-2026",
    name: "Employee Handbook 2026",
    type: "PDF",
    sourceId: "company-handbook",
    sizeBytes: 2_400_000,
    status: "Processed",
    readiness: "Indexed",
    updatedAt: "Sep 5, 2026",
    summary: "The current employee handbook covering policies, benefits, and workplace standards.",
  },
  {
    id: "remote-work-policy",
    name: "Remote Work Policy",
    type: "DOCX",
    sourceId: "company-handbook",
    sizeBytes: 860_000,
    status: "Processed",
    readiness: "NotIndexed",
    updatedAt: "Sep 3, 2026",
    summary: "Guidance for eligibility, collaboration expectations, and remote-work security requirements.",
  },
  {
    id: "orvex-product-overview",
    name: "ORVEX Product Overview",
    type: "PDF",
    sourceId: "product-docs",
    sizeBytes: 1_700_000,
    status: "Pending",
    readiness: "NotIndexed",
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
    readiness: "NotIndexed",
    updatedAt: "Sep 1, 2026",
    summary: "Operational steps for monitoring, triaging, and maintaining workflow executions.",
  },
  {
    id: "monthly-operations-report",
    name: "Monthly Operations Report",
    type: "XLSX",
    sourceId: "operations",
    sizeBytes: 3_600_000,
    status: "Failed",
    readiness: "NotIndexed",
    updatedAt: "Aug 30, 2026",
    summary: "Monthly operating metrics, service trends, and cross-team action items.",
  },
];

const listeners = new Set<() => void>();

function updateDocumentStatus(
  documentId: string,
  expectedStatus: KnowledgeDocument["status"] | null,
  status: KnowledgeDocument["status"],
) {
  const document = documents.find((item) => item.id === documentId);

  if (!document || (expectedStatus !== null && document.status !== expectedStatus)) {
    return undefined;
  }

  const updatedDocument: KnowledgeDocument = {
    ...document,
    status,
    updatedAt: "Just now",
  };

  documents = documents.map((item) =>
    item.id === documentId ? updatedDocument : item,
  );
  listeners.forEach((listener) => listener());

  return updatedDocument;
}

function updateDocumentReadiness(
  documentId: string,
  expectedReadiness: KnowledgeDocument["readiness"],
  readiness: KnowledgeDocument["readiness"],
) {
  const document = documents.find((item) => item.id === documentId);

  if (!document || document.readiness !== expectedReadiness) {
    return undefined;
  }

  const updatedDocument: KnowledgeDocument = {
    ...document,
    readiness,
    updatedAt: "Just now",
  };

  documents = documents.map((item) =>
    item.id === documentId ? updatedDocument : item,
  );
  listeners.forEach((listener) => listener());

  return updatedDocument;
}

export const knowledgeRepository: KnowledgeRepository = {
  listDocuments: () => documents,
  listSources: () => sources,
  startProcessing: (documentId) => {
    const document = documents.find((item) => item.id === documentId);

    if (!document || !["Pending", "Failed", "Processed"].includes(document.status)) {
      return undefined;
    }

    return updateDocumentStatus(documentId, null, "Processing");
  },
  completeProcessing: (documentId) =>
    updateDocumentStatus(documentId, "Processing", "Processed"),
  failProcessing: (documentId) =>
    updateDocumentStatus(documentId, "Processing", "Failed"),
  startIndexing: (documentId) => {
    const document = documents.find((item) => item.id === documentId);

    if (
      !document ||
      document.status !== "Processed" ||
      !["NotIndexed", "IndexFailed"].includes(document.readiness)
    ) {
      return undefined;
    }

    return updateDocumentReadiness(documentId, document.readiness, "Indexing");
  },
  completeIndexing: (documentId) =>
    updateDocumentReadiness(documentId, "Indexing", "Indexed"),
  failIndexing: (documentId) =>
    updateDocumentReadiness(documentId, "Indexing", "IndexFailed"),
  subscribe: (listener) => {
    listeners.add(listener);

    return () => listeners.delete(listener);
  },
};
