from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdate,
    KnowledgeSourceCreate,
    KnowledgeSourceResponse,
    KnowledgeSourceUpdate,
)
from app.services.knowledge_document_service import knowledge_document_service
from app.services.knowledge_source_service import knowledge_source_service

router = APIRouter()


# ==========================================
# Knowledge Sources Endpoints
# ==========================================

@router.post(
    "/sources",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Knowledge Source",
    description="Create a new knowledge source collection for an organization.",
)
async def create_knowledge_source(
    payload: KnowledgeSourceCreate,
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeSourceResponse:
    source = await knowledge_source_service.create_source(db, payload)
    return KnowledgeSourceResponse(
        id=source.id,
        organization_id=source.organization_id,
        name=source.name,
        description=source.description,
        created_at=source.created_at,
        updated_at=source.updated_at,
        document_count=0,
    )


@router.get(
    "/sources",
    response_model=List[KnowledgeSourceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Knowledge Sources",
    description="List knowledge sources, optionally filtered by organization ID.",
)
async def list_knowledge_sources(
    organization_id: UUID | None = Query(None, description="Filter sources by organization ID"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[KnowledgeSourceResponse]:
    return await knowledge_source_service.list_sources(
        db, organization_id=organization_id, skip=skip, limit=limit
    )


@router.get(
    "/sources/{source_id}",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Knowledge Source",
    description="Retrieve a single knowledge source by ID.",
)
async def get_knowledge_source(
    source_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeSourceResponse:
    return await knowledge_source_service.get_source(
        db, source_id, organization_id=organization_id
    )


@router.patch(
    "/sources/{source_id}",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Knowledge Source",
    description="Update a knowledge source's name or description.",
)
async def update_knowledge_source(
    source_id: UUID,
    payload: KnowledgeSourceUpdate,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeSourceResponse:
    return await knowledge_source_service.update_source(
        db, source_id, payload, organization_id=organization_id
    )


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Knowledge Source",
    description="Delete a knowledge source and cascade delete all its documents.",
)
async def delete_knowledge_source(
    source_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await knowledge_source_service.delete_source(
        db, source_id, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# Knowledge Documents Endpoints
# ==========================================

@router.post(
    "/sources/{source_id}/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Knowledge Document",
    description="Create document metadata under a specific knowledge source.",
)
async def create_knowledge_document(
    source_id: UUID,
    payload: KnowledgeDocumentCreate,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeDocumentResponse:
    document = await knowledge_document_service.create_document(
        db, source_id, payload, organization_id=organization_id
    )
    return KnowledgeDocumentResponse.model_validate(document)


@router.get(
    "/sources/{source_id}/documents",
    response_model=List[KnowledgeDocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Knowledge Documents for Source",
    description="Retrieve all documents belonging to a specific knowledge source.",
)
async def list_knowledge_documents(
    source_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[KnowledgeDocumentResponse]:
    docs = await knowledge_document_service.list_documents_by_source(
        db, source_id, organization_id=organization_id, skip=skip, limit=limit
    )
    return [KnowledgeDocumentResponse.model_validate(d) for d in docs]


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Knowledge Document",
    description="Retrieve a single knowledge document by ID.",
)
async def get_knowledge_document(
    document_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeDocumentResponse:
    doc = await knowledge_document_service.get_document(
        db, document_id, organization_id=organization_id
    )
    return KnowledgeDocumentResponse.model_validate(doc)


@router.patch(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Knowledge Document",
    description="Update a knowledge document's metadata or lifecycle status.",
)
async def update_knowledge_document(
    document_id: UUID,
    payload: KnowledgeDocumentUpdate,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeDocumentResponse:
    doc = await knowledge_document_service.update_document(
        db, document_id, payload, organization_id=organization_id
    )
    return KnowledgeDocumentResponse.model_validate(doc)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Knowledge Document",
    description="Delete a knowledge document.",
)
async def delete_knowledge_document(
    document_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await knowledge_document_service.delete_document(
        db, document_id, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
