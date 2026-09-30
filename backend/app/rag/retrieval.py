import re
from typing import List, Optional, Sequence
from app.rag.interfaces import BaseRetriever
from app.rag.schemas import RetrievalChunk, RetrievalRequest, RetrievalResult


class MockRetriever(BaseRetriever):
    """In-memory mock retriever for deterministic testing and foundation development.

    NOTE: This retriever performs deterministic lexical matching in memory.
    This is a temporary foundation utility that will be superseded by embedding-based
    dense vector retrieval (pgvector / external vector store) in subsequent milestones.
    """

    def __init__(self, chunks: Optional[Sequence[RetrievalChunk]] = None) -> None:
        self._chunks: List[RetrievalChunk] = list(chunks) if chunks else []

    def index_chunk(self, chunk: RetrievalChunk) -> None:
        """Add a single chunk to the in-memory index."""
        self._chunks.append(chunk)

    def index_chunks(self, chunks: Sequence[RetrievalChunk]) -> None:
        """Add multiple chunks to the in-memory index."""
        self._chunks.extend(chunks)

    def clear(self) -> None:
        """Clear all indexed chunks."""
        self._chunks.clear()

    @property
    def chunks(self) -> List[RetrievalChunk]:
        """Return a copy of all indexed chunks."""
        return list(self._chunks)

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Retrieve relevant chunks matching the request criteria.

        Enforces:
        - Strict tenant isolation by organization_id (never returns cross-tenant data)
        - Optional source_ids and document_ids scoping
        - Empty query safety (returns 0 chunks)
        - Deterministic lexical scoring and ordering (highest score first)
        - top_k truncation
        """
        trimmed_query = request.query.strip()
        if not trimmed_query:
            return RetrievalResult(chunks=[], query=request.query, retrieval_count=0)

        query_tokens = [w.lower() for w in re.findall(r"\w+", trimmed_query) if w.strip()]
        if not query_tokens:
            return RetrievalResult(chunks=[], query=request.query, retrieval_count=0)

        query_terms_set = set(query_tokens)
        source_filter_set = set(request.source_ids) if request.source_ids else None
        document_filter_set = set(request.document_ids) if request.document_ids else None

        scored_candidates: List[RetrievalChunk] = []

        for chunk in self._chunks:
            # 1. Enforce strict tenant isolation
            if chunk.organization_id != request.organization_id:
                continue

            # 2. Scope filters
            if source_filter_set and chunk.source_id not in source_filter_set:
                continue
            if document_filter_set and chunk.document_id not in document_filter_set:
                continue

            # 3. Lexical matching and scoring
            content_tokens = [w.lower() for w in re.findall(r"\w+", chunk.content) if w.strip()]
            if not content_tokens:
                continue

            matched_terms = query_terms_set.intersection(set(content_tokens))
            if not matched_terms:
                continue

            term_coverage = len(matched_terms) / len(query_terms_set)
            term_frequency = sum(content_tokens.count(term) for term in matched_terms)
            score = round((term_coverage * 0.7) + min(0.3, term_frequency * 0.05), 4)

            if score > 0.0:
                scored_candidates.append(
                    chunk.model_copy(update={"score": score})
                )

        # 4. Sort descending by score, deterministic secondary sort by chunk_id
        scored_candidates.sort(key=lambda c: (-c.score, str(c.chunk_id)))

        # 5. Apply top_k limit
        top_chunks = scored_candidates[: request.top_k]

        return RetrievalResult(
            chunks=top_chunks,
            query=request.query,
            retrieval_count=len(top_chunks),
        )
