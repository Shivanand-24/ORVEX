export type DocumentStatus =
  | "Pending"
  | "Processing"
  | "Processed"
  | "Failed";

export type KnowledgeReadiness =
  | "NotIndexed"
  | "Indexing"
  | "Indexed"
  | "IndexFailed";

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
  readiness: KnowledgeReadiness;
  updatedAt: string;
  summary: string;
};
