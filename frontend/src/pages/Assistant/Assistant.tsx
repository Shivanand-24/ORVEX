import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Database,
  MessageSquare,
  Plus,
  Send,
  Sparkles,
  User,
  Zap,
} from "lucide-react";
import { assistantRepository } from "../../services/assistantRepository";
import type { Conversation } from "../../types/assistant";

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

function Assistant() {
  const [conversations, setConversations] = useState<readonly Conversation[]>(() =>
    assistantRepository.getConversations()
  );
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    () => conversations[0]?.id ?? null
  );
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    return assistantRepository.subscribe(() => {
      const updatedList = assistantRepository.getConversations();
      setConversations(updatedList);
    });
  }, []);

  const activeConversation = conversations.find(
    (conv) => conv.id === activeConversationId
  );
  const isThinking = activeConversationId
    ? assistantRepository.isThinking(activeConversationId)
    : false;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages, isThinking]);

  const handleCreateNewChat = () => {
    const newConv = assistantRepository.createConversation();
    setActiveConversationId(newConv.id);
    setInputText("");
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const messageText = (textToSend ?? inputText).trim();
    if (!messageText || isThinking) {
      return;
    }

    let targetConvId = activeConversationId;

    if (!targetConvId) {
      const newConv = assistantRepository.createConversation();
      targetConvId = newConv.id;
      setActiveConversationId(newConv.id);
    }

    if (!textToSend) {
      setInputText("");
    }

    await assistantRepository.sendMessage(targetConvId, messageText);
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
                <p>No conversations yet.</p>
              </div>
            )}
          </div>
        </aside>

        {/* RIGHT: Chat Workspace */}
        <main className="assistant-workspace">
          <div className="workspace-header">
            <div className="workspace-header-title">
              <Sparkles size={18} style={{ color: "var(--orvex-accent-hover)" }} />
              <span>{activeConversation?.title || "AI Assistant Copilot"}</span>
            </div>

            <span className="workspace-badge">Frontend Demo</span>
          </div>

          {!activeConversation || activeConversation.messages.length === 0 ? (
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
                  >
                    <strong>
                      <Zap size={14} style={{ color: "var(--orvex-accent-hover)" }} />
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
              {activeConversation.messages.map((msg) => (
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
                          color: "var(--orvex-text-muted)",
                          background: "rgba(139, 92, 246, 0.08)",
                          padding: "3px 8px",
                          borderRadius: "6px",
                          border: "1px solid rgba(139, 92, 246, 0.2)",
                        }}
                      >
                        <Database size={12} style={{ color: "var(--orvex-accent-hover)" }} />
                        <span>Sources: Company Handbook & Product Docs • RAG Confidence: 98.4%</span>
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
                placeholder="Ask ORVEX Assistant anything..."
                rows={1}
                aria-label="Type your message"
                disabled={isThinking}
              />

              <button
                className="composer-send-button"
                type="submit"
                disabled={!inputText.trim() || isThinking}
                aria-label="Send message"
              >
                <Send size={16} />
              </button>
            </form>
            <div className="composer-footer-note">
              ORVEX AI Assistant (Milestone 4A Frontend Demo). Press Enter to send, Shift+Enter for newline.
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Assistant;