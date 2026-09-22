from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.llm import LLMGateway, LLMMessage, LLMRequest, get_llm_gateway
from app.models.assistant import AssistantMessage
from app.repositories.conversation_repository import conversation_repository
from app.repositories.message_repository import message_repository
from app.schemas.assistant import (
    ChatPromptRequest,
    ChatResponse,
    MessageCreate,
    MessageResponse,
)


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

    async def generate_chat_turn(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        schema: ChatPromptRequest,
        organization_id: UUID | None = None,
        gateway: LLMGateway | None = None,
    ) -> ChatResponse:
        """Executes a full conversation turn: persists user message, queries LLM Gateway with history, and persists assistant reply."""
        # 1. Validate parent conversation exists
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        # 2. Enforce tenant isolation
        if organization_id is not None and conversation.organization_id != organization_id:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        prompt_content = schema.content.strip()
        if not prompt_content:
            raise BadRequestError("Prompt content cannot be empty.")

        # 3. Retrieve prior messages to assemble history
        existing_messages = await message_repository.list_by_conversation(
            db, conversation_id=conversation.id, skip=0, limit=50
        )

        # 4. Transaction 1: Persist user message and commit immediately
        user_message = await message_repository.create(
            db=db,
            conversation_id=conversation.id,
            role="user",
            content=prompt_content,
            tokens_used=0,
            latency_ms=0,
        )
        await conversation_repository.update(db, conversation, touch_updated_at=True)
        await db.commit()
        await db.refresh(user_message)

        # 5. Format messages for LLM request
        history_llm_messages = [
            LLMMessage(role=m.role, content=m.content) for m in existing_messages
        ]
        history_llm_messages.append(LLMMessage(role="user", content=prompt_content))

        llm_request = LLMRequest(
            messages=history_llm_messages,
            system_instruction=schema.system_instruction,
            model=schema.model,
            temperature=schema.temperature,
            max_tokens=schema.max_tokens,
            metadata={
                "conversation_id": str(conversation.id),
                "organization_id": str(conversation.organization_id),
            },
        )

        # 6. External LLM Call: NO active database transaction held
        active_gateway = gateway or get_llm_gateway()
        llm_response = await active_gateway.generate(llm_request)

        # 7. Transaction 2: Persist assistant reply and commit
        try:
            assistant_message = await message_repository.create(
                db=db,
                conversation_id=conversation.id,
                role="assistant",
                content=llm_response.content,
                tokens_used=llm_response.usage.total_tokens,
                latency_ms=llm_response.latency_ms,
            )
            await conversation_repository.update(db, conversation, touch_updated_at=True)
            await db.commit()
            await db.refresh(assistant_message)
        except Exception:
            await db.rollback()
            raise

        return ChatResponse(
            conversation_id=conversation.id,
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(assistant_message),
            provider=llm_response.provider,
            model=llm_response.model,
            finish_reason=llm_response.finish_reason,
        )


assistant_message_service = AssistantMessageService()
