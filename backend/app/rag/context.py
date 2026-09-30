from typing import List
from app.rag.schemas import RetrievalResult, RetrievedContext


class ContextBuilder:
    """Constructs provider-neutral structured context from retrieval results for downstream LLM prompts.

    Ensures:
    - Exact chunk ordering is preserved
    - Source, document, and chunk identifiers are explicitly tagged
    - Retrieved context is cleanly separated from the original user query
    - Output is deterministic and performs no LLM calls
    """

    def build(self, query: str, retrieval_result: RetrievalResult) -> RetrievedContext:
        """Transforms a query and RetrievalResult into a structured RetrievedContext."""
        if not retrieval_result.chunks:
            return RetrievedContext(
                query=query,
                formatted_context="",
                chunks=[],
                sources_used=[],
                documents_used=[],
                total_chunks=0,
            )

        context_blocks: List[str] = []
        sources_seen: dict = {}
        docs_seen: dict = {}

        for index, chunk in enumerate(retrieval_result.chunks, start=1):
            sources_seen[chunk.source_id] = None
            docs_seen[chunk.document_id] = None

            header = (
                f"[Context Chunk {index} | Document: {chunk.document_id} | "
                f"Source: {chunk.source_id} | Chunk: {chunk.chunk_id}]"
            )
            block = f"{header}\n{chunk.content}"
            context_blocks.append(block)

        formatted_context = "\n\n".join(context_blocks)

        return RetrievedContext(
            query=query,
            formatted_context=formatted_context,
            chunks=list(retrieval_result.chunks),
            sources_used=list(sources_seen.keys()),
            documents_used=list(docs_seen.keys()),
            total_chunks=len(retrieval_result.chunks),
        )


def build_retrieved_context(query: str, retrieval_result: RetrievalResult) -> RetrievedContext:
    """Convenience functional wrapper around ContextBuilder."""
    return ContextBuilder().build(query=query, retrieval_result=retrieval_result)
