import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.knowledge import KnowledgeSource


class AgentKnowledgeSource(Base):
    """Junction table mapping Agents to Knowledge Sources."""

    __tablename__ = "agent_knowledge_sources"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        primary_key=True,
    )


class AgentTool(Base):
    """Junction table mapping Agents to application tool registry identifiers."""

    __tablename__ = "agent_tools"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tool_name: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )


class Agent(Base, TimestampMixin):
    """AI Agent configuration entity."""

    __tablename__ = "agents"

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
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Active"
    )
    system_instructions: Mapped[str] = mapped_column(Text, nullable=False)
    require_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="agents")
    creator: Mapped["User"] = relationship("User")
    knowledge_sources: Mapped[List["KnowledgeSource"]] = relationship(
        "KnowledgeSource", secondary="agent_knowledge_sources"
    )
    tools: Mapped[List["AgentTool"]] = relationship(
        "AgentTool", cascade="all, delete-orphan"
    )
