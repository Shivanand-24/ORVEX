import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class KnowledgeSource(Base, TimestampMixin):
    """Knowledge Source entity representing a document collection."""

    __tablename__ = "knowledge_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="knowledge_sources")
    documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="knowledge_source", cascade="all, delete-orphan"
    )


class KnowledgeDocument(Base, TimestampMixin):
    """Knowledge Document entity storing file metadata and processing lifecycle status."""

    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", server_default=text("'pending'")
    )
    indexing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="not_indexed", server_default=text("'not_indexed'")
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_documents_status", "source_id", "processing_status", "indexing_status"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="knowledge_documents")
    knowledge_source: Mapped["KnowledgeSource"] = relationship("KnowledgeSource", back_populates="documents")
