export type DocumentStatus = "Ready" | "Processing";

export type KnowledgeSource = {
  id: string;
  name: string;
  description: string;
};

export type KnowledgeDocument = {
  id: string;
  name: string;
  type: string;
  sourceId: string;
  sizeBytes: number;
  status: DocumentStatus;
  updatedAt: string;
  summary: string;
};
