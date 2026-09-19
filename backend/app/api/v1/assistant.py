from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.assistant import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.services.assistant_conversation_service import assistant_conversation_service
from app.services.assistant_message_service import assistant_message_service

router = APIRouter()


# ==========================================
# Conversation Endpoints
# ==========================================

@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation",
    description="Create a new assistant conversation session for an organization.",
)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    return await assistant_conversation_service.create_conversation(db, payload)


@router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Conversations",
    description="List assistant conversations, optionally filtered by organization ID.",
)
async def list_conversations(
    organization_id: UUID | None = Query(None, description="Filter conversations by organization ID"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[ConversationResponse]:
    return await assistant_conversation_service.list_conversations(
        db, organization_id=organization_id, skip=skip, limit=limit
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Conversation",
    description="Retrieve a conversation session by UUID.",
)
async def get_conversation(
    conversation_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    return await assistant_conversation_service.get_conversation(
        db, conversation_id, organization_id=organization_id
    )


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Conversation",
    description="Update a conversation's title.",
)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> ConversationResponse:
    return await assistant_conversation_service.update_conversation(
        db, conversation_id, payload, organization_id=organization_id
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Conversation",
    description="Delete a conversation and cascade delete all its messages.",
)
async def delete_conversation(
    conversation_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await assistant_conversation_service.delete_conversation(
        db, conversation_id, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# Message Endpoints
# ==========================================

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Message",
    description="Persist a new message inside a conversation (without AI response generation).",
)
async def create_message(
    conversation_id: UUID,
    payload: MessageCreate,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    message = await assistant_message_service.create_message(
        db, conversation_id, payload, organization_id=organization_id
    )
    return MessageResponse.model_validate(message)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="List Conversation Messages",
    description="Retrieve all messages belonging to a conversation ordered chronologically.",
)
async def list_messages(
    conversation_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[MessageResponse]:
    messages = await assistant_message_service.list_messages(
        db, conversation_id, organization_id=organization_id, skip=skip, limit=limit
    )
    return [MessageResponse.model_validate(m) for m in messages]


@router.get(
    "/messages/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Message",
    description="Retrieve a single message by UUID.",
)
async def get_message(
    message_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    message = await assistant_message_service.get_message(
        db, message_id, organization_id=organization_id
    )
    return MessageResponse.model_validate(message)
