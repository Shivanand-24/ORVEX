import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, Database, MessageSquare, Search, Workflow, X } from "lucide-react";
import { agentRepository } from "../../services/agentRepository";
import { assistantRepository } from "../../services/assistantRepository";
import { knowledgeRepository } from "../../services/knowledgeRepository";
import { workflowRepository } from "../../services/workflowRepository";

type GlobalSearchModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

type SearchResultItem = {
  id: string;
  category: "Knowledge" | "Agents" | "Workflows" | "Assistant";
  title: string;
  subtitle: string;
  path: string;
  icon: typeof Search;
};

function GlobalSearchModal({ isOpen, onClose }: GlobalSearchModalProps) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else setQuery("");
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const normalized = query.trim().toLowerCase();

  const docs = knowledgeRepository.listDocuments();
  const agents = agentRepository.list();
  const workflows = workflowRepository.list();
  const chats = assistantRepository.getConversations();

  const results: SearchResultItem[] = [];

  if (normalized.length > 0) {
    // Search docs
    docs.forEach((doc) => {
      if (`${doc.name} ${doc.summary} ${doc.type}`.toLowerCase().includes(normalized)) {
        results.push({
          id: `doc-${doc.id}`,
          category: "Knowledge",
          title: doc.name,
          subtitle: `${doc.type} • Status: ${doc.status} • RAG: ${doc.readiness}`,
          path: "/knowledge",
          icon: Database,
        });
      }
    });

    // Search agents
    agents.forEach((agent) => {
      if (`${agent.name} ${agent.description} ${agent.domain}`.toLowerCase().includes(normalized)) {
        results.push({
          id: `agent-${agent.id}`,
          category: "Agents",
          title: agent.name,
          subtitle: `${agent.domain} • ${agent.status} • ${agent.executions} runs`,
          path: "/agents",
          icon: Bot,
        });
      }
    });

    // Search workflows
    workflows.forEach((wf) => {
      if (`${wf.name} ${wf.description} ${wf.trigger}`.toLowerCase().includes(normalized)) {
        results.push({
          id: `wf-${wf.id}`,
          category: "Workflows",
          title: wf.name,
          subtitle: `Trigger: ${wf.trigger} • ${wf.status}`,
          path: "/workflows",
          icon: Workflow,
        });
      }
    });

    // Search assistant chats
    chats.forEach((chat) => {
      if (chat.title.toLowerCase().includes(normalized)) {
        results.push({
          id: `chat-${chat.id}`,
          category: "Assistant",
          title: chat.title,
          subtitle: `Conversation • Last updated ${chat.updatedAt}`,
          path: "/assistant",
          icon: MessageSquare,
        });
      }
    });
  }

  const handleSelect = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <div className="global-search-backdrop" onClick={onClose}>
      <div className="global-search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="global-search-input-wrapper">
          <Search size={18} className="search-icon" />
          <input
            autoFocus
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across Knowledge, Agents, Workflows, and Assistant..."
            aria-label="Search ORVEX enterprise platform"
          />
          <button className="search-close-button" type="button" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="global-search-results">
          {query.trim() === "" ? (
            <div className="search-hint">
              <p>Type keywords like <strong>"security"</strong>, <strong>"handbook"</strong>, <strong>"sync"</strong>, or <strong>"agent"</strong></p>
            </div>
          ) : results.length > 0 ? (
            results.map((item) => {
              const ItemIcon = item.icon;
              return (
                <div
                  key={item.id}
                  className="search-result-item"
                  onClick={() => handleSelect(item.path)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="result-icon-badge">
                    <ItemIcon size={16} />
                  </div>
                  <div className="result-info">
                    <div className="result-header">
                      <strong>{item.title}</strong>
                      <span className="result-category">{item.category}</span>
                    </div>
                    <span>{item.subtitle}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="search-empty">
              <p>No results found matching "<strong>{query}</strong>"</p>
            </div>
          )}
        </div>

        <div className="global-search-footer">
          <span>Navigate with mouse or click result • Press <kbd>ESC</kbd> to exit</span>
        </div>
      </div>
    </div>
  );
}

export default GlobalSearchModal;
