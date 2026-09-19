import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.agent import Agent


class AgentExecution(Base, TimestampMixin):
    """Persisted record of an Agent execution run."""

    __tablename__ = "agent_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="direct_api",
    )
    # Generic UUID metadata reference (e.g. conversation_id or workflow_execution_id)
    # No direct foreign key constraint to preserve modular decoupling
    source_reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    input_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    require_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    output_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'waiting_for_approval', 'completed', 'failed', 'cancelled')",
            name="chk_agent_execution_status",
        ),
        CheckConstraint(
            "source IN ('direct_api', 'assistant_chat', 'workflow_step')",
            name="chk_agent_execution_source",
        ),
        Index("idx_agent_executions_org", "organization_id"),
        Index("idx_agent_executions_agent_started", "agent_id", "started_at"),
        Index("idx_agent_executions_status", "status"),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="executions")
    triggered_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[triggered_by_user_id]
    )
    approved_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[approved_by_user_id]
    )
