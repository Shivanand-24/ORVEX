from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


# Frontend & Backend status mappings
PROCESSING_STATUS_MAP: dict[str, str] = {
    "pending": "Pending",
    "processing": "Processing",
    "processed": "Processed",
    "failed": "Failed",
}

INDEXING_STATUS_MAP: dict[str, str] = {
    "not_indexed": "NotIndexed",
    "indexing": "Indexing",
    "indexed": "Indexed",
    "index_failed": "IndexFailed",
}

VALID_PROCESSING_STATUSES = {
    "pending", "processing", "processed", "failed",
    "Pending", "Processing", "Processed", "Failed",
}

VALID_INDEXING_STATUSES = {
    "not_indexed", "indexing", "indexed", "index_failed",
    "NotIndexed", "Indexing", "Indexed", "IndexFailed",
}


def normalize_processing_status(value: str | None) -> str:
    """Normalizes processing status string to backend storage format."""
    if not value:
        return "pending"
    cleaned = value.strip().lower()
    if cleaned not in PROCESSING_STATUS_MAP:
        raise ValueError(f"Invalid processing status: '{value}'. Valid options: {list(PROCESSING_STATUS_MAP.keys())}")
    return cleaned


def normalize_indexing_status(value: str | None) -> str:
    """Normalizes indexing status string to backend storage format."""
    if not value:
        return "not_indexed"
    cleaned = value.strip().lower()
    # Support camel/pascal casing like "notindexed" or "indexfailed"
    aliases = {
        "notindexed": "not_indexed",
        "indexfailed": "index_failed",
    }
    cleaned = aliases.get(cleaned, cleaned)
    if cleaned not in INDEXING_STATUS_MAP:
        raise ValueError(f"Invalid indexing status: '{value}'. Valid options: {list(INDEXING_STATUS_MAP.keys())}")
    return cleaned


# ==========================================
# Knowledge Source Schemas
# ==========================================

class KnowledgeSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: str | None = Field(None, description="Optional collection description")


class KnowledgeSourceCreate(KnowledgeSourceBase):
    organization_id: UUID = Field(..., description="Target organization ID")


class KnowledgeSourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255, description="Updated name")
    description: str | None = Field(None, description="Updated description")


class KnowledgeSourceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Knowledge Document Schemas
# ==========================================

class KnowledgeDocumentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Document display name or filename")
    file_type: str = Field("pdf", max_length=50, description="File type/extension (e.g. PDF, DOCX, TXT)")
    storage_path: str | None = Field(None, max_length=512, description="Storage location path or URL")
    size_bytes: int = Field(0, ge=0, description="File size in bytes")
    summary: str | None = Field(None, description="Document summary text")


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    organization_id: UUID | None = Field(None, description="Optional explicit organization ID (validated against source)")
    processing_status: str | None = Field(None, description="Initial processing status ('pending', 'processing', 'processed', 'failed')")
    indexing_status: str | None = Field(None, description="Initial indexing readiness ('not_indexed', 'indexing', 'indexed', 'index_failed')")
    status: str | None = Field(None, description="Frontend alias for processing_status ('Pending', etc.)")
    readiness: str | None = Field(None, description="Frontend alias for indexing_status ('NotIndexed', etc.)")

    @model_validator(mode="after")
    def resolve_aliases_and_normalize(self) -> "KnowledgeDocumentCreate":
        # Resolve status alias
        raw_proc = self.status or self.processing_status
        self.processing_status = normalize_processing_status(raw_proc)

        # Resolve readiness alias
        raw_idx = self.readiness or self.indexing_status
        self.indexing_status = normalize_indexing_status(raw_idx)
        return self


class KnowledgeDocumentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    file_type: str | None = Field(None, max_length=50)
    storage_path: str | None = Field(None, max_length=512)
    size_bytes: int | None = Field(None, ge=0)
    summary: str | None = None
    processing_status: str | None = None
    indexing_status: str | None = None
    status: str | None = None
    readiness: str | None = None

    @model_validator(mode="after")
    def resolve_aliases_and_normalize(self) -> "KnowledgeDocumentUpdate":
        raw_proc = self.status or self.processing_status
        if raw_proc is not None:
            self.processing_status = normalize_processing_status(raw_proc)

        raw_idx = self.readiness or self.indexing_status
        if raw_idx is not None:
            self.indexing_status = normalize_indexing_status(raw_idx)
        return self


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    source_id: UUID
    name: str
    file_type: str
    storage_path: str
    size_bytes: int
    processing_status: str
    indexing_status: str
    status: str = ""
    readiness: str = ""
    summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_frontend_aliases(self) -> "KnowledgeDocumentResponse":
        self.status = PROCESSING_STATUS_MAP.get(self.processing_status, self.processing_status.capitalize())
        self.readiness = INDEXING_STATUS_MAP.get(self.indexing_status, self.indexing_status.capitalize())
        return self
