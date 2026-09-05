import { useState } from "react";
import { Database, FileText, Search } from "lucide-react";
import { knowledgeRepository } from "../../services/knowledgeRepository";
import type { KnowledgeDocument } from "../../types/knowledge";

const documents = knowledgeRepository.listDocuments();
const sources = knowledgeRepository.listSources();

function formatFileSize(sizeBytes: number) {
  return `${(sizeBytes / 1_000_000).toFixed(1)} MB`;
}

function Knowledge() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(
    documents[0]?.id ?? null,
  );

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredDocuments = documents.filter((document) => {
    const source = sources.find((item) => item.id === document.sourceId);
    const searchableText = `${document.name} ${document.type} ${source?.name ?? ""}`;

    return searchableText.toLowerCase().includes(normalizedQuery);
  });
  const selectedDocument = documents.find(
    (document) => document.id === selectedDocumentId,
  );
  const readyDocuments = documents.filter(
    (document) => document.status === "Ready",
  );
  const processingDocuments = documents.filter(
    (document) => document.status === "Processing",
  );

  const getSourceName = (document: KnowledgeDocument) =>
    sources.find((source) => source.id === document.sourceId)?.name ?? "Unknown source";

  return (
    <div className="knowledge-page">
      <div className="page-header">
        <div>
          <h1>Knowledge</h1>
          <p>Organize the enterprise information available to ORVEX.</p>
        </div>
      </div>

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
          <span>Ready to Search</span>
          <strong>{readyDocuments.length}</strong>
          <small>Available to AI workflows</small>
        </div>
        <div className="stat-card knowledge-processing-stat">
          <span>Processing</span>
          <strong>{processingDocuments.length}</strong>
          <small>Preparing for retrieval</small>
        </div>
      </div>

      <section className="knowledge-section" aria-labelledby="knowledge-sources-title">
        <div className="knowledge-section-header">
          <div>
            <h2 id="knowledge-sources-title">Knowledge Sources</h2>
            <p>Collections that organize information for your workspace.</p>
          </div>
        </div>

        <div className="knowledge-source-grid">
          {sources.map((source) => {
            const sourceDocumentCount = documents.filter(
              (document) => document.sourceId === source.id,
            ).length;

            return (
              <article className="knowledge-source-card" key={source.id}>
                <div className="knowledge-source-icon">
                  <Database size={20} />
                </div>
                <div>
                  <h3>{source.name}</h3>
                  <p>{source.description}</p>
                </div>
                <span>{sourceDocumentCount} documents</span>
              </article>
            );
          })}
        </div>
      </section>

      <div className="knowledge-content-grid">
        <section className="dashboard-card knowledge-documents-card" aria-labelledby="knowledge-documents-title">
          <div className="knowledge-documents-header">
            <div>
              <h2 id="knowledge-documents-title">Documents</h2>
              <p>Select a document to inspect its knowledge record.</p>
            </div>

            <label className="knowledge-search" htmlFor="knowledge-search-input">
              <Search size={17} />
              <input
                id="knowledge-search-input"
                type="search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search documents"
              />
            </label>
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
                  <th scope="col">Updated</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocuments.map((document) => (
                  <tr
                    className={document.id === selectedDocumentId ? "selected" : ""}
                    key={document.id}
                    onClick={() => setSelectedDocumentId(document.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedDocumentId(document.id);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                    aria-selected={document.id === selectedDocumentId}
                  >
                    <td>
                      <span className="knowledge-document-name">
                        <FileText size={16} />
                        {document.name}
                      </span>
                    </td>
                    <td>{document.type}</td>
                    <td>{getSourceName(document)}</td>
                    <td>{formatFileSize(document.sizeBytes)}</td>
                    <td>
                      <span className={`knowledge-status ${document.status.toLowerCase()}`}>
                        <span></span>
                        {document.status}
                      </span>
                    </td>
                    <td>{document.updatedAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredDocuments.length === 0 && (
            <p className="knowledge-empty-state">No documents match your search.</p>
          )}
        </section>

        <aside className="dashboard-card knowledge-detail-panel" aria-live="polite">
          {selectedDocument ? (
            <>
              <div className="knowledge-detail-icon">
                <FileText size={22} />
              </div>
              <p className="knowledge-detail-eyebrow">Document details</p>
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
                  <dd>{selectedDocument.status}</dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{selectedDocument.updatedAt}</dd>
                </div>
              </dl>
            </>
          ) : (
            <div className="knowledge-detail-empty">
              <FileText size={22} />
              <p>Select a document to view its details.</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

export default Knowledge;
