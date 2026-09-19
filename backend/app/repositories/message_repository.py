from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assistant import AssistantMessage


class MessageRepository:
    """Encapsulates database access for AssistantMessage entities."""

    async def create(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        role: str,
        content: str,
        tokens_used: int = 0,
        latency_ms: int = 0,
    ) -> AssistantMessage:
        message = AssistantMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        db.add(message)
        await db.flush()
        return message

    async def list_by_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AssistantMessage]:
        stmt = (
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation_id)
            .order_by(AssistantMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self, db: AsyncSession, message_id: UUID
    ) -> AssistantMessage | None:
        stmt = (
            select(AssistantMessage)
            .options(selectinload(AssistantMessage.conversation))
            .where(AssistantMessage.id == message_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, message: AssistantMessage) -> None:
        await db.delete(message)
        await db.flush()


message_repository = MessageRepository()
