from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.assistant import Conversation
from app.repositories.conversation_repository import conversation_repository
from app.repositories.membership_repository import membership_repository
from app.repositories.organization_repository import organization_repository
from app.repositories.user_repository import user_repository
from app.schemas.assistant import ConversationCreate, ConversationResponse, ConversationUpdate


class AssistantConversationService:
    """Business logic, tenant isolation, and transaction boundaries for Conversations."""

    async def create_conversation(
        self, db: AsyncSession, schema: ConversationCreate
    ) -> ConversationResponse:
        # Validate organization existence
        org = await organization_repository.get_by_id(db, schema.organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{schema.organization_id}' not found.")

        # Resolve or validate user_id
        user_id = schema.user_id
        if user_id is not None:
            user = await user_repository.get_by_id(db, user_id)
            if not user:
                raise NotFoundError(f"User with ID '{user_id}' not found.")
        else:
            # Fallback to first member of organization
            members = await membership_repository.list_by_organization(db, schema.organization_id, limit=1)
            if members:
                user_id = members[0].user_id
            else:
                # Fallback to any registered user
                users = await user_repository.list(db, limit=1)
                if users:
                    user_id = users[0].id
                else:
                    raise BadRequestError(
                        "user_id is required to create a conversation when no registered user exists."
                    )

        title = schema.title.strip() if schema.title else "New Conversation"
        if not title:
            raise BadRequestError("Conversation title cannot be empty.")

        conversation = await conversation_repository.create(
            db=db,
            organization_id=schema.organization_id,
            user_id=user_id,
            title=title,
        )
        await db.commit()
        await db.refresh(conversation)

        return ConversationResponse(
            id=conversation.id,
            organization_id=conversation.organization_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,
        )

    async def list_conversations(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ConversationResponse]:
        if organization_id is not None:
            org = await organization_repository.get_by_id(db, organization_id)
            if not org:
                raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        conversations = await conversation_repository.list(
            db, organization_id=organization_id, skip=skip, limit=limit
        )

        responses: list[ConversationResponse] = []
        for c in conversations:
            count = await conversation_repository.count_messages(db, c.id)
            responses.append(
                ConversationResponse(
                    id=c.id,
                    organization_id=c.organization_id,
                    user_id=c.user_id,
                    title=c.title,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=count,
                )
            )
        return responses

    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID | None = None,
    ) -> ConversationResponse:
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        # Enforce tenant isolation
        if organization_id is not None and conversation.organization_id != organization_id:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        count = await conversation_repository.count_messages(db, conversation.id)
        return ConversationResponse(
            id=conversation.id,
            organization_id=conversation.organization_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=count,
        )

    async def update_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        schema: ConversationUpdate,
        organization_id: UUID | None = None,
    ) -> ConversationResponse:
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        # Enforce tenant isolation
        if organization_id is not None and conversation.organization_id != organization_id:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        new_title = schema.title.strip() if schema.title is not None else None
        if schema.title is not None and not new_title:
            raise BadRequestError("Conversation title cannot be empty.")

        updated_conv = await conversation_repository.update(
            db, conversation, title=new_title
        )
        await db.commit()
        await db.refresh(updated_conv)

        count = await conversation_repository.count_messages(db, updated_conv.id)
        return ConversationResponse(
            id=updated_conv.id,
            organization_id=updated_conv.organization_id,
            user_id=updated_conv.user_id,
            title=updated_conv.title,
            created_at=updated_conv.created_at,
            updated_at=updated_conv.updated_at,
            message_count=count,
        )

    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID | None = None,
    ) -> None:
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        # Enforce tenant isolation
        if organization_id is not None and conversation.organization_id != organization_id:
            raise NotFoundError(f"Conversation with ID '{conversation_id}' not found.")

        await conversation_repository.delete(db, conversation)
        await db.commit()


assistant_conversation_service = AssistantConversationService()
