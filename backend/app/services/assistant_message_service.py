from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.assistant import AssistantMessage
from app.repositories.conversation_repository import conversation_repository
from app.repositories.message_repository import message_repository
from app.schemas.assistant import MessageCreate


class AssistantMessageService:
    """Business logic, tenant isolation, and transaction boundaries for Assistant Messages."""

    async def create_message(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        schema: MessageCreate,
        organization_id: UUID | None = None,
    ) -> AssistantMessage:
        # Validate parent conversation exists
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        # Enforce tenant isolation
        if organization_id is not None and conversation.organization_id != organization_id:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        content = schema.content.strip()
        if not content:
            raise BadRequestError("Message content cannot be empty.")

        role = schema.role.strip().lower()
        if role not in ("user", "assistant", "system"):
            raise BadRequestError(f"Invalid message role '{schema.role}'. Valid roles: ['user', 'assistant', 'system']")

        message = await message_repository.create(
            db=db,
            conversation_id=conversation.id,
            role=role,
            content=content,
            tokens_used=schema.tokens_used,
            latency_ms=schema.latency_ms,
        )

        # Touch conversation updated_at
        await conversation_repository.update(db, conversation, touch_updated_at=True)

        await db.commit()
        await db.refresh(message)
        return message

    async def list_messages(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AssistantMessage]:
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        # Enforce tenant isolation
        if organization_id is not None and conversation.organization_id != organization_id:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        return await message_repository.list_by_conversation(
            db, conversation_id=conversation_id, skip=skip, limit=limit
        )

    async def get_message(
        self,
        db: AsyncSession,
        message_id: UUID,
        organization_id: UUID | None = None,
    ) -> AssistantMessage:
        message = await message_repository.get_by_id(db, message_id)
        if not message:
            raise NotFoundError(f"Message with ID '{message_id}' not found.")

        # Enforce tenant isolation through parent conversation
        if organization_id is not None:
            if not message.conversation or message.conversation.organization_id != organization_id:
                raise NotFoundError(f"Message with ID '{message_id}' not found.")

        return message


assistant_message_service = AssistantMessageService()
