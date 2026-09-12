import { useEffect, useState } from "react";
import { Database, FileText, Plus, Search } from "lucide-react";
import Modal from "../../components/common/Modal";
import StatusBadge from "../../components/common/StatusBadge";
import { knowledgeRepository } from "../../services/knowledgeRepository";
import { toastService } from "../../services/toastService";
import type { KnowledgeDocument } from "../../types/knowledge";

const sources = knowledgeRepository.listSources();

function formatFileSize(sizeBytes: number) {
  return `${(sizeBytes / 1_000_000).toFixed(1)} MB`;
}

type FilterTab = "all" | "rag-ready" | "processing" | "indexing" | "failed";

function Knowledge() {
  const [documents, setDocuments] = useState(() => knowledgeRepository.listDocuments());
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTab, setFilterTab] = useState<FilterTab>("all");
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(
    documents[0]?.id ?? null
  );

  // Ingest Modal state
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [newDocName, setNewDocName] = useState("");
  const [newDocSource, setNewDocSource] = useState(sources[0]?.id ?? "company-handbook");
  const [newDocType, setNewDocType] = useState("PDF");

  useEffect(() => {
    return knowledgeRepository.subscribe(() => {
      setDocuments(knowledgeRepository.listDocuments());
    });
  }, []);

  const normalizedQuery = searchQuery.trim().toLowerCase();

  const filteredDocuments = documents.filter((doc) => {
    const source = sources.find((s) => s.id === doc.sourceId);
    const matchesSearch = `${doc.name} ${doc.type} ${source?.name ?? ""}`
      .toLowerCase()
      .includes(normalizedQuery);

    if (!matchesSearch) return false;

    if (filterTab === "rag-ready") return doc.readiness === "Indexed";
    if (filterTab === "processing") return doc.status === "Processing";
    if (filterTab === "indexing") return doc.readiness === "Indexing";
    if (filterTab === "failed") return doc.status === "Failed" || doc.readiness === "IndexFailed";

    return true;
  });

  const selectedDocument = documents.find((doc) => doc.id === selectedDocumentId);
  const processingDocuments = documents.filter((doc) => doc.status === "Processing");
  const indexedDocuments = documents.filter((doc) => doc.readiness === "Indexed");
  const indexingDocuments = documents.filter((doc) => doc.readiness === "Indexing");

  const getSourceName = (doc: KnowledgeDocument) =>
    sources.find((source) => source.id === doc.sourceId)?.name ?? "Unknown source";

  const handleDemoAction = (action: "start" | "complete" | "fail") => {
    if (!selectedDocument) return;

    if (action === "start") {
      knowledgeRepository.startProcessing(selectedDocument.id);
      toastService.show("Processing Started", `Document "${selectedDocument.name}" is now processing.`, "info");
      return;
    }

    if (action === "complete") {
      knowledgeRepository.completeProcessing(selectedDocument.id);
      toastService.show("Processing Complete", `Document "${selectedDocument.name}" processed successfully.`, "success");
      return;
    }

    knowledgeRepository.failProcessing(selectedDocument.id);
    toastService.show("Processing Failed", `Document "${selectedDocument.name}" marked as failed.`, "error");
  };

  const handleIndexingDemoAction = (action: "start" | "complete" | "fail") => {
    if (!selectedDocument) return;

    if (action === "start") {
      knowledgeRepository.startIndexing(selectedDocument.id);
      toastService.show("Indexing Started", `Vector indexing initiated for "${selectedDocument.name}".`, "info");
      return;
    }

    if (action === "complete") {
      knowledgeRepository.completeIndexing(selectedDocument.id);
      toastService.show("RAG Ready", `Document "${selectedDocument.name}" is now RAG-indexed!`, "success");
      return;
    }

    knowledgeRepository.failIndexing(selectedDocument.id);
    toastService.show("Indexing Failed", `Vector indexing failed for "${selectedDocument.name}".`, "error");
  };

  const handleIngestDocument = (e: React.FormEvent) => {
    e.preventDefault();
    const title = newDocName.trim();
    if (!title) return;

    toastService.show(
      "Document Ingested",
      `"${title}" (${newDocType}) added to workspace ingestion queue.`,
      "success"
    );

    setNewDocName("");
    setIsIngestOpen(false);
  };

  return (
    <div className="knowledge-page">
      <div className="page-header">
        <div>
          <h1>Knowledge Management</h1>
          <p>Organize, process, and index enterprise information available to ORVEX.</p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => setIsIngestOpen(true)}
        >
          <Plus size={16} /> Ingest Document
        </button>
      </div>

      {/* KPI Stats */}
      <div className="stats-grid knowledge-stats">
        <div className="stat-card">
          <span>Knowledge Documents</span>
          <strong>{documents.length}</strong>
          <small>Across your workspace</small>
        </div>
        <div className="stat-card">
          <span>Knowledge Sources</span>
          <strong>{sources.length}</strong>
          <small>Connected collections</small>
        </div>
        <div className="stat-card">
          <span>RAG Ready</span>
          <strong>{indexedDocuments.length}</strong>
          <small>Indexed for retrieval</small>
        </div>
        <div className="stat-card knowledge-processing-stat">
          <span>Pipeline Active</span>
          <strong>{processingDocuments.length + indexingDocuments.length}</strong>
          <small>Processing or indexing</small>
        </div>
      </div>

      {/* Sources Grid */}
      <section className="knowledge-section" aria-labelledby="knowledge-sources-title">
        <div className="knowledge-section-header">
          <div className="orvex-rail-header">
            <div>
              <h2 id="knowledge-sources-title">Knowledge Sources</h2>
              <p>Collections organizing information for your workspace.</p>
            </div>
          </div>
        </div>

        <div className="knowledge-source-grid">
          {sources.map((source) => {
            const sourceDocCount = documents.filter((doc) => doc.sourceId === source.id).length;
            return (
              <article className="knowledge-source-card" key={source.id}>
                <div className="knowledge-source-icon" style={{ background: "#E4F1EF", color: "#0E6B63" }}>
                  <Database size={20} />
                </div>
                <div>
                  <h3>{source.name}</h3>
                  <p>{source.description}</p>
                </div>
                <span>{sourceDocCount} documents</span>
              </article>
            );
          })}
        </div>
      </section>

      {/* Document Management Section */}
      <div className="knowledge-content-grid">
        <section className="dashboard-card knowledge-documents-card" aria-labelledby="knowledge-documents-title">
          <div className="knowledge-documents-header">
            <div className="orvex-rail-header">
              <div>
                <h2 id="knowledge-documents-title">Document Directory</h2>
                <p>Filter and inspect document readiness status.</p>
              </div>
            </div>

            <label className="knowledge-search" htmlFor="knowledge-search-input">
              <Search size={17} />
              <input
                id="knowledge-search-input"
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents"
              />
            </label>
          </div>

          {/* Filter Bar */}
          <div style={{ display: "flex", gap: "8px", padding: "0 20px 16px 20px", borderBottom: "1px solid var(--orvex-border)" }}>
            {(["all", "rag-ready", "processing", "indexing", "failed"] as FilterTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                className={`secondary-button ${filterTab === tab ? "active" : ""}`}
                onClick={() => setFilterTab(tab)}
                style={{
                  fontSize: "12px",
                  padding: "4px 10px",
                  height: "30px",
                  textTransform: "capitalize",
                  background: filterTab === tab ? "#E4F1EF" : "transparent",
                  borderColor: filterTab === tab ? "#0E6B63" : "transparent",
                  color: filterTab === tab ? "#0E6B63" : "var(--orvex-text-secondary)",
                }}
              >
                {tab.replace("-", " ")}
              </button>
            ))}
          </div>

          <div className="knowledge-table-scroll">
            <table className="knowledge-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Type</th>
                  <th scope="col">Source</th>
                  <th scope="col">Size</th>
                  <th scope="col">Status</th>
                  <th scope="col">RAG Readiness</th>
                  <th scope="col">Updated</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocuments.map((doc) => (
                  <tr
                    className={doc.id === selectedDocumentId ? "selected" : ""}
                    key={doc.id}
                    onClick={() => setSelectedDocumentId(doc.id)}
                    role="button"
                    tabIndex={0}
                    aria-selected={doc.id === selectedDocumentId}
                  >
                    <td>
                      <span className="knowledge-document-name">
                        <FileText size={16} style={{ color: "#0E6B63" }} />
                        {doc.name}
                      </span>
                    </td>
                    <td>{doc.type}</td>
                    <td>{getSourceName(doc)}</td>
                    <td>{formatFileSize(doc.sizeBytes)}</td>
                    <td>
                      <StatusBadge status={doc.status} type="knowledge" />
                    </td>
                    <td>
                      <StatusBadge status={doc.readiness} type="knowledge" />
                    </td>
                    <td>{doc.updatedAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredDocuments.length === 0 && (
            <p className="knowledge-empty-state">No documents match your filter.</p>
          )}
        </section>

        {/* Side Detail Panel */}
        <aside className="dashboard-card knowledge-detail-panel" aria-live="polite">
          {selectedDocument ? (
            <>
              <div className="knowledge-detail-icon" style={{ background: "#E4F1EF", color: "#0E6B63" }}>
                <FileText size={22} />
              </div>
              <p className="knowledge-detail-eyebrow">Document Details</p>
              <h2>{selectedDocument.name}</h2>
              <p className="knowledge-detail-summary">{selectedDocument.summary}</p>

              <dl className="knowledge-detail-list">
                <div>
                  <dt>Type</dt>
                  <dd>{selectedDocument.type}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>{getSourceName(selectedDocument)}</dd>
                </div>
                <div>
                  <dt>Size</dt>
                  <dd>{formatFileSize(selectedDocument.sizeBytes)}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>
                    <StatusBadge status={selectedDocument.status} type="knowledge" />
                  </dd>
                </div>
                <div>
                  <dt>RAG State</dt>
                  <dd>
                    <StatusBadge status={selectedDocument.readiness} type="knowledge" />
                  </dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{selectedDocument.updatedAt}</dd>
                </div>
              </dl>

              {/* Demo Action Controls */}
              <div className="knowledge-demo-controls">
                <p>Processing Control</p>
                {selectedDocument.status !== "Processing" ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => handleDemoAction("start")}
                  >
                    {selectedDocument.status === "Failed" ? "Retry Processing" : "Start Processing"}
                  </button>
                ) : (
                  <div className="knowledge-demo-actions">
                    <button
                      className="primary-button"
                      type="button"
                      onClick={() => handleDemoAction("complete")}
                    >
                      Complete Processing
                    </button>
                    <button
                      className="secondary-button knowledge-failure-button"
                      type="button"
                      onClick={() => handleDemoAction("fail")}
                    >
                      Simulate Failure
                    </button>
                  </div>
                )}
              </div>

              {selectedDocument.status === "Processed" && (
                <div className="knowledge-demo-controls">
                  <p>RAG Vector Indexing</p>
                  {selectedDocument.readiness === "NotIndexed" ||
                  selectedDocument.readiness === "IndexFailed" ? (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => handleIndexingDemoAction("start")}
                    >
                      {selectedDocument.readiness === "IndexFailed"
                        ? "Retry Indexing"
                        : "Start Vector Indexing"}
                    </button>
                  ) : selectedDocument.readiness === "Indexing" ? (
                    <div className="knowledge-demo-actions">
                      <button
                        className="primary-button"
                        type="button"
                        onClick={() => handleIndexingDemoAction("complete")}
                      >
                        Complete Indexing
                      </button>
                      <button
                        className="secondary-button knowledge-failure-button"
                        type="button"
                        onClick={() => handleIndexingDemoAction("fail")}
                      >
                        Simulate Index Failure
                      </button>
                    </div>
                  ) : (
                    <p style={{ color: "#16745B", fontSize: "13px", fontWeight: 600 }}>✓ RAG-Indexed & Ready for Assistant queries</p>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="knowledge-detail-empty">
              <FileText size={22} />
              <p>Select a document to view details.</p>
            </div>
          )}
        </aside>
      </div>

      {/* Ingest Document Modal */}
      <Modal
        isOpen={isIngestOpen}
        onClose={() => setIsIngestOpen(false)}
        title="Ingest Enterprise Document"
        subtitle="Add a new file to the ORVEX knowledge pipeline."
      >
        <form className="settings-form" onSubmit={handleIngestDocument}>
          <div className="form-group">
            <label htmlFor="ingest-name">Document Title</label>
            <input
              id="ingest-name"
              type="text"
              required
              placeholder="e.g. 2026 Security Architecture Guide"
              value={newDocName}
              onChange={(e) => setNewDocName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="ingest-source">Target Knowledge Source</label>
            <select
              id="ingest-source"
              value={newDocSource}
              onChange={(e) => setNewDocSource(e.target.value)}
            >
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="ingest-type">Document Format</label>
            <select
              id="ingest-type"
              value={newDocType}
              onChange={(e) => setNewDocType(e.target.value)}
            >
              <option value="PDF">PDF Document</option>
              <option value="DOCX">Word Document (.docx)</option>
              <option value="XLSX">Excel Spreadsheet (.xlsx)</option>
              <option value="MARKDOWN">Markdown (.md)</option>
            </select>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px" }}>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setIsIngestOpen(false)}
            >
              Cancel
            </button>
            <button className="primary-button" type="submit">
              Ingest Document
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default Knowledge;
