/**
 * ORVEX AI Assistant Repository
 *
 * NOTE: This is a frontend-only / in-memory demo implementation.
 * In future milestones, this service will be replaced by API calls to the
 * ORVEX FastAPI backend, AI Router, vector store, and LLM endpoints.
 */

import type { AssistantMessage, Conversation } from "../types/assistant";

export interface AssistantRepository {
  getConversations(): readonly Conversation[];
  getConversation(id: string): Conversation | undefined;
  createConversation(title?: string): Conversation;
  sendMessage(conversationId: string, content: string): Promise<AssistantMessage | undefined>;
  isThinking(conversationId: string): boolean;
  subscribe(listener: () => void): () => void;
}

let conversations: Conversation[] = [
  {
    id: "conv-welcome-demo",
    title: "Getting Started with ORVEX",
    createdAt: "Sep 9, 2026 10:00 AM",
    updatedAt: "Sep 9, 2026 10:01 AM",
    messages: [
      {
        id: "msg-welcome-1",
        role: "user",
        content: "What can ORVEX help me automate?",
        createdAt: "Sep 9, 2026 10:00 AM",
      },
      {
        id: "msg-welcome-2",
        role: "assistant",
        content:
          "ORVEX helps automate cross-departmental operations using intelligent workflows and autonomous AI agents. Key capabilities include automated document ingestion, operational anomaly alerts, customer ticket triage, and automated report generation.\n\n*Note: This is a frontend demonstration of the ORVEX AI Assistant (Milestone 4A). Real workflow and agent orchestration engines will be connected in a future backend milestone.*",
        createdAt: "Sep 9, 2026 10:01 AM",
      },
    ],
  },
  {
    id: "conv-knowledge-demo",
    title: "Knowledge Base Overview",
    createdAt: "Sep 8, 2026 04:15 PM",
    updatedAt: "Sep 8, 2026 04:16 PM",
    messages: [
      {
        id: "msg-kb-1",
        role: "user",
        content: "Summarize our knowledge base.",
        createdAt: "Sep 8, 2026 04:15 PM",
      },
      {
        id: "msg-kb-2",
        role: "assistant",
        content:
          "The ORVEX Knowledge System currently indexes key enterprise document collections including the **Company Handbook**, **Product Documentation**, and **Operations Runbooks**. Key topics include workplace policies, remote-work security, product specs, and incident management procedures.\n\n*Note: This is a frontend demonstration of the ORVEX AI Assistant (Milestone 4A). Real enterprise RAG vector search will be connected in a future backend milestone.*",
        createdAt: "Sep 8, 2026 04:16 PM",
      },
    ],
  },
];

const thinkingState = new Map<string, boolean>();
const listeners = new Set<() => void>();

function notifyListeners() {
  listeners.forEach((listener) => listener());
}

function generateMockResponse(prompt: string): string {
  const normalized = prompt.trim().toLowerCase();

  if (normalized.includes("summarize our knowledge base") || normalized.includes("summarize knowledge")) {
    return (
      "The ORVEX Knowledge System currently indexes key enterprise document collections including the **Company Handbook**, **Product Documentation**, and **Operations Runbooks**. Key topics include workplace policies, remote-work security, product specs, and incident management procedures.\n\n" +
      "*Note: This is a frontend demonstration of the ORVEX AI Assistant (Milestone 4A). Real enterprise RAG vector search will be connected in a future backend milestone.*"
    );
  }

  if (normalized.includes("what can orvex help me automate") || normalized.includes("automate")) {
    return (
      "ORVEX helps automate cross-departmental operations using intelligent workflows and autonomous AI agents. Key capabilities include automated document ingestion, operational anomaly alerts, customer ticket triage, and automated report generation.\n\n" +
      "*Note: This is a frontend demonstration of the ORVEX AI Assistant (Milestone 4A). Real workflow and agent orchestration engines will be connected in a future backend milestone.*"
    );
  }

  if (normalized.includes("how can enterprise agents help my team") || normalized.includes("agent")) {
    return (
      "ORVEX Enterprise Agents act as digital teammates configured for specific domains:\n" +
      "- **Research Agent**: Summarizes company documents and market intelligence.\n" +
      "- **Data Analyst**: Analyzes metric trends and generates executive summaries.\n" +
      "- **HR Intelligence**: Assists with policy queries and employee onboarding.\n" +
      "- **Operations Agent**: Automates routine business tasks and runbook execution.\n\n" +
      "*Note: This is a frontend demonstration of the ORVEX AI Assistant (Milestone 4A). Agent execution will be connected in a future backend milestone.*"
    );
  }

  if (normalized.includes("what information is available in the knowledge system") || normalized.includes("knowledge system") || normalized.includes("documents")) {
    return (
      "The ORVEX Knowledge System contains 5 workspace documents (such as Employee Handbook 2026, Remote Work Policy, and ORVEX Product Overview) across 3 connected sources (Company Handbook, Product Documentation, and Operations).\n\n" +
      "*Note: This is a frontend demonstration of the ORVEX AI Assistant (Milestone 4A). Vector store queries will be connected in a future backend milestone.*"
    );
  }

  // Fallback response for generic prompts
  const displayPrompt = prompt.length > 50 ? prompt.substring(0, 50) + "..." : prompt;
  return (
    `Thank you for asking about **"${displayPrompt}"**.\n\n` +
    "ORVEX AI Assistant is currently operating in frontend demonstration mode (Milestone 4A). In future milestones, this copilot will connect to the ORVEX AI Router, FastAPI backend, vector stores, and custom LLMs to provide real-time RAG answers across your enterprise data."
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(date: Date): string {
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) + " " + formatTime(date);
}

export const assistantRepository: AssistantRepository = {
  getConversations: () => conversations,

  getConversation: (id: string) => conversations.find((c) => c.id === id),

  createConversation: (title?: string) => {
    const now = new Date();
    const newConv: Conversation = {
      id: `conv-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      title: title || "New Conversation",
      messages: [],
      createdAt: formatDate(now),
      updatedAt: formatDate(now),
    };

    conversations = [newConv, ...conversations];
    notifyListeners();
    return newConv;
  },

  isThinking: (conversationId: string) => thinkingState.get(conversationId) === true,

  sendMessage: async (conversationId: string, content: string) => {
    const trimmed = content.trim();
    if (!trimmed) {
      return undefined;
    }

    const conversation = conversations.find((c) => c.id === conversationId);
    if (!conversation) {
      return undefined;
    }

    const now = new Date();
    const userMessage: AssistantMessage = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content: trimmed,
      createdAt: formatTime(now),
    };

    // Auto-update conversation title if it's currently a default "New Conversation"
    const isDefaultTitle = conversation.title === "New Conversation" || conversation.title === "New Chat";
    const updatedTitle = isDefaultTitle
      ? trimmed.length > 32
        ? `${trimmed.substring(0, 32)}...`
        : trimmed
      : conversation.title;

    // Update conversation with user message
    const updatedConversation: Conversation = {
      ...conversation,
      title: updatedTitle,
      messages: [...conversation.messages, userMessage],
      updatedAt: formatDate(now),
    };

    conversations = conversations.map((c) => (c.id === conversationId ? updatedConversation : c));
    thinkingState.set(conversationId, true);
    notifyListeners();

    // Simulate response delay (~750ms)
    await new Promise((resolve) => setTimeout(resolve, 750));

    const responseNow = new Date();
    const assistantMessage: AssistantMessage = {
      id: `msg-${Date.now()}-assistant`,
      role: "assistant",
      content: generateMockResponse(trimmed),
      createdAt: formatTime(responseNow),
    };

    const finalConversation: Conversation = {
      ...updatedConversation,
      messages: [...updatedConversation.messages, assistantMessage],
      updatedAt: formatDate(responseNow),
    };

    conversations = conversations.map((c) => (c.id === conversationId ? finalConversation : c));
    thinkingState.set(conversationId, false);
    notifyListeners();

    return assistantMessage;
  },

  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
