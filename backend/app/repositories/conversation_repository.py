from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant import AssistantMessage, Conversation


class ConversationRepository:
    """Encapsulates database access for Conversation entities."""

    async def create(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        title: str,
    ) -> Conversation:
        conversation = Conversation(
            organization_id=organization_id,
            user_id=user_id,
            title=title,
        )
        db.add(conversation)
        await db.flush()
        return conversation

    async def list(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        stmt = select(Conversation)
        if organization_id is not None:
            stmt = stmt.where(Conversation.organization_id == organization_id)
        stmt = stmt.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self, db: AsyncSession, conversation_id: UUID
    ) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        conversation: Conversation,
        title: str | None = None,
        touch_updated_at: bool = False,
    ) -> Conversation:
        if title is not None:
            conversation.title = title
        if touch_updated_at:
            conversation.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return conversation

    async def delete(self, db: AsyncSession, conversation: Conversation) -> None:
        await db.delete(conversation)
        await db.flush()

    async def count_messages(self, db: AsyncSession, conversation_id: UUID) -> int:
        stmt = select(func.count(AssistantMessage.id)).where(
            AssistantMessage.conversation_id == conversation_id
        )
        result = await db.execute(stmt)
        return result.scalar_one() or 0


conversation_repository = ConversationRepository()
