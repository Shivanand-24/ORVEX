import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Chunk(BaseModel):
    """Represents a discrete text segment produced by the chunking engine."""

    chunk_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique chunk identifier")
    content: str = Field(..., min_length=1, description="Raw text content of the chunk")
    character_start: int = Field(..., ge=0, description="Start character offset in source text")
    character_end: int = Field(..., ge=0, description="End character offset in source text")
    chunk_index: int = Field(..., ge=0, description="Zero-based sequence index within the document")

    model_config = ConfigDict(extra="ignore")


class RetrievalChunk(BaseModel):
    """Represents an indexed chunk candidate evaluated or returned during retrieval."""

    chunk_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique chunk identifier")
    document_id: uuid.UUID = Field(..., description="ID of parent KnowledgeDocument")
    source_id: uuid.UUID = Field(..., description="ID of parent KnowledgeSource")
    organization_id: uuid.UUID = Field(..., description="Tenant organization ID for strict isolation")
    content: str = Field(..., min_length=1, description="Chunk text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary chunk metadata")
    score: float = Field(0.0, ge=0.0, description="Relevance score (higher values indicate greater relevance)")

    model_config = ConfigDict(extra="ignore")


class RetrievalRequest(BaseModel):
    """Normalized query parameters and scope filters for retrieval."""

    organization_id: uuid.UUID = Field(..., description="Tenant organization ID enforcing isolation")
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(5, ge=1, le=100, description="Maximum number of chunks to return")
    source_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional filter by source IDs")
    document_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional filter by document IDs")

    model_config = ConfigDict(extra="ignore")


class RetrievalResult(BaseModel):
    """Normalized result returned by a retriever."""

    chunks: List[RetrievalChunk] = Field(default_factory=list, description="Retrieved chunks ordered by score")
    query: str = Field(..., description="Original search query")
    retrieval_count: int = Field(0, ge=0, description="Number of retrieved chunks")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def sync_retrieval_count(self) -> "RetrievalResult":
        if self.retrieval_count == 0 and self.chunks:
            self.retrieval_count = len(self.chunks)
        return self


class RetrievedContext(BaseModel):
    """Provider-neutral context constructed from retrieval results for downstream LLM prompts."""

    query: str = Field(..., description="Original user query")
    formatted_context: str = Field(..., description="Deterministic formatted context text")
    chunks: List[RetrievalChunk] = Field(default_factory=list, description="Referenced chunks in preserved order")
    sources_used: List[uuid.UUID] = Field(default_factory=list, description="Unique source IDs referenced")
    documents_used: List[uuid.UUID] = Field(default_factory=list, description="Unique document IDs referenced")
    total_chunks: int = Field(0, ge=0, description="Total number of chunks included in context")

    model_config = ConfigDict(extra="ignore")
