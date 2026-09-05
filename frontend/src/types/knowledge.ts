export type DocumentStatus =
  | "Pending"
  | "Processing"
  | "Processed"
  | "Failed";

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
