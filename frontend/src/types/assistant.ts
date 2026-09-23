export type MessageRole = "user" | "assistant";

export type AssistantMessage = {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  tokensUsed?: number;
  latencyMs?: number;
};

export type Conversation = {
  id: string;
  title: string;
  messages: AssistantMessage[];
  createdAt: string;
  updatedAt: string;
};
