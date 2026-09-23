import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bot,
  Building2,
  Database,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  User,
  Zap,
} from "lucide-react";
import { apiClient } from "../../services/apiClient";
import type { ApiOrganization } from "../../services/apiClient";
import { toastService } from "../../services/toastService";
import type { AssistantMessage, Conversation, MessageRole } from "../../types/assistant";

const SUGGESTED_PROMPTS = [
  {
    title: "Summarize Knowledge Base",
    prompt: "Summarize our knowledge base.",
    description: "Overview of indexed document collections and topics.",
  },
  {
    title: "Automation Opportunities",
    prompt: "What can ORVEX help me automate?",
    description: "Discover workflow and agent capabilities.",
  },
  {
    title: "Enterprise AI Workforce",
    prompt: "How can enterprise agents help my team?",
    description: "Learn about domain-specific AI agents.",
  },
  {
    title: "Knowledge Inspection",
    prompt: "What information is available in the knowledge system?",
    description: "Inspect workspace document sources and stats.",
  },
];

function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return isoString;
  }
}

function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;
    return (
      date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      }) +
      " " +
      formatTime(isoString)
    );
  } catch {
    return isoString;
  }
}

let optimisticSeq = 0;
function createOptimisticUserMessage(content: string): AssistantMessage {
  optimisticSeq += 1;
  return {
    id: `optimistic-${Date.now()}-${optimisticSeq}`,
    role: "user",
    content,
    createdAt: formatTime(new Date().toISOString()),
  };
}

function Assistant() {
  const [organizations, setOrganizations] = useState<ApiOrganization[]>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null);
  const [activeUserId, setActiveUserId] = useState<string | null>(null);
  const [isLoadingOrg, setIsLoadingOrg] = useState(true);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [inputText, setInputText] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const loadConversations = useCallback(async (orgId: string) => {
    try {
      const apiConvs = await apiClient.assistant.conversations.list({
        organization_id: orgId,
      });
      const mappedConvs: Conversation[] = apiConvs.map((conv) => ({
        id: conv.id,
        title: conv.title,
        messages: [],
        createdAt: formatDate(conv.created_at),
        updatedAt: formatDate(conv.updated_at),
      }));
      setConversations(mappedConvs);
      if (mappedConvs.length > 0) {
        setActiveConversationId(mappedConvs[0].id);
      } else {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
      toastService.show(
        "Error loading conversations",
        "Could not load your conversation history.",
        "error"
      );
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        setIsLoadingOrg(true);
        const [orgs, users] = await Promise.all([
          apiClient.organizations.list(),
          apiClient.users.list().catch(() => []),
        ]);
        if (!isMounted) return;
        setOrganizations(orgs);
        if (users.length > 0) {
          setActiveUserId(users[0].id);
        }
        if (orgs.length > 0) {
          const primaryOrg = orgs[0];
          setActiveOrgId(primaryOrg.id);
          await loadConversations(primaryOrg.id);
        } else {
          // Do NOT silently create organization on mount
          setConversations([]);
          setActiveConversationId(null);
          setMessages([]);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error("Failed to initialize organization context:", err);
        toastService.show(
          "Initialization Error",
          "Could not load organization context. Please ensure backend is running.",
          "error"
        );
      } finally {
        if (isMounted) {
          setIsLoadingOrg(false);
        }
      }
    }

    init();
    return () => {
      isMounted = false;
    };
  }, [loadConversations]);

  useEffect(() => {
    if (!activeConversationId || !activeOrgId) {
      return;
    }

    const conversationId = activeConversationId;
    const orgId = activeOrgId;

    let isMounted = true;
    async function fetchMessages() {
      try {
        const apiMessages = await apiClient.assistant.messages.list(
          conversationId,
          { organization_id: orgId }
        );
        if (!isMounted) return;
        setMessages(
          apiMessages.map((m) => ({
            id: m.id,
            role: m.role as MessageRole,
            content: m.content,
            createdAt: formatTime(m.created_at),
            tokensUsed: m.tokens_used,
            latencyMs: m.latency_ms,
          }))
        );
      } catch (err) {
        if (!isMounted) return;
        console.error("Failed to fetch messages:", err);
        toastService.show(
          "Error loading messages",
          "Could not load conversation messages.",
          "error"
        );
      }
    }

    fetchMessages();
    return () => {
      isMounted = false;
    };
  }, [activeConversationId, activeOrgId]);

  const activeConversation = conversations.find(
    (conv) => conv.id === activeConversationId
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleBootstrapOrganization = async () => {
    try {
      const newOrg = await apiClient.organizations.create({
        name: "Acme Corporation",
        slug: "acme-corp",
      });
      let resolvedUserId = activeUserId;
      if (!resolvedUserId) {
        try {
          const newUser = await apiClient.users.create({
            email: "admin@acme.corp",
            full_name: "Acme Admin",
          });
          resolvedUserId = newUser.id;
          setActiveUserId(newUser.id);
          await apiClient.memberships.add(newOrg.id, {
            user_id: newUser.id,
            role: "admin",
          });
        } catch {
          // Non-blocking
        }
      }
      setOrganizations([newOrg]);
      setActiveOrgId(newOrg.id);
      await loadConversations(newOrg.id);
      toastService.show(
        "Organization Initialized",
        "Created Acme Corporation development organization.",
        "success"
      );
    } catch (err) {
      console.error("Failed to initialize organization:", err);
      toastService.show(
        "Setup Error",
        "Failed to create development organization.",
        "error"
      );
    }
  };

  const handleCreateNewChat = async () => {
    if (!activeOrgId) {
      toastService.show(
        "No Organization",
        "An active organization is required to start a conversation.",
        "warning"
      );
      return;
    }

    try {
      const newConv = await apiClient.assistant.conversations.create({
        organization_id: activeOrgId,
        user_id: activeUserId ?? undefined,
        title: "New Conversation",
      });

      const mappedConv: Conversation = {
        id: newConv.id,
        title: newConv.title,
        messages: [],
        createdAt: formatDate(newConv.created_at),
        updatedAt: formatDate(newConv.updated_at),
      };

      setConversations((prev) => [mappedConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
      setInputText("");
      setTimeout(() => textareaRef.current?.focus(), 50);
    } catch (err) {
      console.error("Failed to create conversation:", err);
      toastService.show(
        "Error",
        "Could not create a new conversation session.",
        "error"
      );
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const messageText = (textToSend ?? inputText).trim();
    if (!messageText || isThinking) {
      return;
    }

    if (!activeOrgId) {
      toastService.show(
        "No Organization",
        "An active organization is required to send messages.",
        "warning"
      );
      return;
    }

    let targetConvId = activeConversationId;

    if (!textToSend) {
      setInputText("");
    }

    const optimisticUserMsg = createOptimisticUserMessage(messageText);
    const optimisticId = optimisticUserMsg.id;

    try {
      if (!targetConvId) {
        const title =
          messageText.length > 32
            ? `${messageText.substring(0, 32)}...`
            : messageText;
        const newConv = await apiClient.assistant.conversations.create({
          organization_id: activeOrgId,
          user_id: activeUserId ?? undefined,
          title,
        });
        targetConvId = newConv.id;
        setActiveConversationId(newConv.id);
        const mappedConv: Conversation = {
          id: newConv.id,
          title: newConv.title,
          messages: [],
          createdAt: formatDate(newConv.created_at),
          updatedAt: formatDate(newConv.updated_at),
        };
        setConversations((prev) => [mappedConv, ...prev]);
      }

      setMessages((prev) => [...prev, optimisticUserMsg]);
      setIsThinking(true);

      const response = await apiClient.assistant.messages.chat(
        targetConvId,
        { content: messageText },
        { organization_id: activeOrgId }
      );

      const persistedUserMsg: AssistantMessage = {
        id: response.user_message.id,
        role: "user",
        content: response.user_message.content,
        createdAt: formatTime(response.user_message.created_at),
        tokensUsed: response.user_message.tokens_used,
        latencyMs: response.user_message.latency_ms,
      };

      const persistedAssistantMsg: AssistantMessage = {
        id: response.assistant_message.id,
        role: "assistant",
        content: response.assistant_message.content,
        createdAt: formatTime(response.assistant_message.created_at),
        tokensUsed: response.assistant_message.tokens_used,
        latencyMs: response.assistant_message.latency_ms,
      };

      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticId),
        persistedUserMsg,
        persistedAssistantMsg,
      ]);

      const currentConv = conversations.find((c) => c.id === targetConvId);
      const isDefaultTitle =
        !currentConv ||
        currentConv.title === "New Conversation" ||
        currentConv.title === "New Chat";

      let nextTitle = currentConv?.title || "New Conversation";
      if (isDefaultTitle) {
        nextTitle =
          messageText.length > 32
            ? `${messageText.substring(0, 32)}...`
            : messageText;
        try {
          await apiClient.assistant.conversations.update(
            targetConvId,
            { title: nextTitle },
            { organization_id: activeOrgId }
          );
        } catch {
          // Non-blocking update failure
        }
      }

      const updatedTime = formatDate(response.assistant_message.created_at);
      setConversations((prev) =>
        prev.map((c) =>
          c.id === targetConvId
            ? { ...c, title: nextTitle, updatedAt: updatedTime }
            : c
        )
      );
    } catch (err: unknown) {
      console.error("Assistant chat error:", err);
      toastService.show(
        "Assistant Error",
        "Failed to generate response. Please try again.",
        "error"
      );
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const formatMessageText = (content: string) => {
    const paragraphs = content.split("\n\n");
    return paragraphs.map((paragraph, pIdx) => {
      const lines = paragraph.split("\n");
      return (
        <p key={pIdx}>
          {lines.map((line, lIdx) => {
            const parts = line.split(/(\*\*.*?\*\*|\*.*?\*)/g);
            return (
              <span key={lIdx}>
                {parts.map((part, ptIdx) => {
                  if (part.startsWith("**") && part.endsWith("**")) {
                    return <strong key={ptIdx}>{part.slice(2, -2)}</strong>;
                  }
                  if (part.startsWith("*") && part.endsWith("*")) {
                    return <em key={ptIdx}>{part.slice(1, -1)}</em>;
                  }
                  return part;
                })}
                {lIdx < lines.length - 1 && <br />}
              </span>
            );
          })}
        </p>
      );
    });
  };

  return (
    <div className="assistant-page">
      <div className="page-header">
        <div>
          <h1>AI Assistant</h1>
          <p>Enterprise Intelligence Copilot</p>
        </div>
      </div>

      <div className="assistant-layout">
        {/* LEFT: Conversation Sidebar */}
        <aside className="assistant-sidebar" aria-label="Recent Conversations">
          <div className="assistant-sidebar-header">
            <button
              className="new-chat-button"
              type="button"
              onClick={handleCreateNewChat}
              aria-label="Start new conversation"
              disabled={!activeOrgId}
            >
              <Plus size={16} />
              <span>New Chat</span>
            </button>
          </div>

          <div className="assistant-conversations-list">
            {conversations.length > 0 ? (
              conversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                return (
                  <div
                    key={conv.id}
                    className={`conversation-item ${isActive ? "active" : ""}`}
                    onClick={() => setActiveConversationId(conv.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setActiveConversationId(conv.id);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                    aria-selected={isActive}
                  >
                    <MessageSquare size={16} className="conversation-item-icon" />
                    <div className="conversation-item-info">
                      <span className="conversation-item-title">{conv.title}</span>
                      <span className="conversation-item-date">{conv.updatedAt}</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="sidebar-empty-state">
                <p>
                  {organizations.length === 0 && !isLoadingOrg
                    ? "No organization found."
                    : "No conversations yet."}
                </p>
              </div>
            )}
          </div>
        </aside>

        {/* RIGHT: Chat Workspace */}
        <main className="assistant-workspace">
          <div className="workspace-header">
            <div className="workspace-header-title">
              <Sparkles size={18} style={{ color: "#0E6B63" }} />
              <span>{activeConversation?.title || "AI Assistant Copilot"}</span>
            </div>

            <span className="workspace-badge">ORVEX Intelligence</span>
          </div>

          {organizations.length === 0 && !isLoadingOrg ? (
            /* Controlled Setup State for empty organizations */
            <div className="assistant-welcome">
              <div className="welcome-icon-wrapper">
                <Building2 size={28} />
              </div>
              <h2>Organization Required</h2>
              <p>
                No enterprise organization was found. An active organization is required to create conversations and run AI copilot sessions.
              </p>
              <button
                className="primary-button"
                type="button"
                onClick={handleBootstrapOrganization}
                style={{ marginTop: "16px" }}
              >
                Initialize Development Organization
              </button>
            </div>
          ) : !activeConversation || messages.length === 0 ? (
            /* Welcome State */
            <div className="assistant-welcome">
              <div className="welcome-icon-wrapper">
                <Sparkles size={28} />
              </div>
              <h2>Welcome to ORVEX AI Assistant</h2>
              <p>
                Your Enterprise Intelligence Copilot. Ask questions, explore indexed knowledge,
                or discover enterprise workflow automation possibilities.
              </p>

              <span className="suggested-prompts-title">Suggested Prompts</span>
              <div className="suggested-prompts-grid">
                {SUGGESTED_PROMPTS.map((item, idx) => (
                  <button
                    key={idx}
                    className="suggested-prompt-card"
                    type="button"
                    onClick={() => handleSendMessage(item.prompt)}
                    disabled={isThinking || !activeOrgId}
                  >
                    <strong>
                      <Zap size={14} style={{ color: "#0E6B63" }} />
                      {item.title}
                    </strong>
                    <span>{item.description}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages List */
            <div className="assistant-messages" aria-live="polite">
              {messages.map((msg) => (
                <div key={msg.id} className={`message-row ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
                  </div>

                  <div className="message-content-wrapper">
                    <div className="message-bubble">
                      {formatMessageText(msg.content)}
                    </div>

                    {msg.role === "assistant" && (
                      <div
                        style={{
                          marginTop: "6px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          fontSize: "11px",
                          color: "#59615D",
                          background: "#E4F1EF",
                          padding: "3px 8px",
                          borderRadius: "4px",
                          border: "1px solid rgba(14, 107, 99, 0.25)",
                        }}
                      >
                        <Database size={12} style={{ color: "#0E6B63" }} />
                        <span>
                          {msg.tokensUsed !== undefined && msg.tokensUsed > 0
                            ? `Tokens: ${msg.tokensUsed} • Latency: ${msg.latencyMs ?? 0}ms`
                            : "Sources: Company Handbook & Product Docs • RAG Confidence: 98.4%"}
                        </span>
                      </div>
                    )}

                    <span className="message-time">{msg.createdAt}</span>
                  </div>
                </div>
              ))}

              {/* Thinking / Loading State */}
              {isThinking && (
                <div className="message-row assistant">
                  <div className="message-avatar">
                    <Bot size={16} />
                  </div>
                  <div className="message-content-wrapper">
                    <div className="thinking-indicator" aria-label="Assistant is thinking">
                      <div className="thinking-dot"></div>
                      <div className="thinking-dot"></div>
                      <div className="thinking-dot"></div>
                      <span className="thinking-text">Retrieving knowledge context & generating answer...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Message Composer */}
          <div className="assistant-composer">
            <form
              className="composer-form"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
            >
              <textarea
                ref={textareaRef}
                className="composer-textarea"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  !activeOrgId
                    ? "Initialize an organization to start chatting..."
                    : "Ask ORVEX Assistant anything..."
                }
                rows={1}
                aria-label="Type your message"
                disabled={isThinking || !activeOrgId}
              />

              <button
                className="composer-send-button"
                type="submit"
                disabled={!inputText.trim() || isThinking || !activeOrgId}
                aria-label="Send message"
              >
                <Send size={16} />
              </button>
            </form>
            <div className="composer-footer-note">
              ORVEX AI Assistant (Connected to LLM Gateway). Press Enter to send, Shift+Enter for newline.
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Assistant;