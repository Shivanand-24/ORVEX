from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.knowledge import KnowledgeSource
from app.repositories.knowledge_source_repository import knowledge_source_repository
from app.repositories.organization_repository import organization_repository
from app.schemas.knowledge import KnowledgeSourceCreate, KnowledgeSourceResponse, KnowledgeSourceUpdate


class KnowledgeSourceService:
    """Business logic and transaction boundaries for Knowledge Source management."""

    async def create_source(
        self, db: AsyncSession, schema: KnowledgeSourceCreate
    ) -> KnowledgeSource:
        # Validate organization existence
        org = await organization_repository.get_by_id(db, schema.organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{schema.organization_id}' not found.")

        name = schema.name.strip()
        if not name:
            raise BadRequestError("Knowledge source name cannot be empty.")

        source = await knowledge_source_repository.create(
            db=db,
            organization_id=schema.organization_id,
            name=name,
            description=schema.description.strip() if schema.description else None,
        )
        await db.commit()
        await db.refresh(source)
        return source

    async def list_sources(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[KnowledgeSourceResponse]:
        if organization_id is not None:
            org = await organization_repository.get_by_id(db, organization_id)
            if not org:
                raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        sources = await knowledge_source_repository.list(
            db, organization_id=organization_id, skip=skip, limit=limit
        )

        responses: list[KnowledgeSourceResponse] = []
        for s in sources:
            doc_count = await knowledge_source_repository.count_documents(db, s.id)
            responses.append(
                KnowledgeSourceResponse(
                    id=s.id,
                    organization_id=s.organization_id,
                    name=s.name,
                    description=s.description,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    document_count=doc_count,
                )
            )
        return responses

    async def get_source(
        self,
        db: AsyncSession,
        source_id: UUID,
        organization_id: UUID | None = None,
    ) -> KnowledgeSourceResponse:
        source = await knowledge_source_repository.get_by_id(db, source_id)
        if not source:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        # Enforce organization isolation
        if organization_id is not None and source.organization_id != organization_id:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        doc_count = await knowledge_source_repository.count_documents(db, source.id)
        return KnowledgeSourceResponse(
            id=source.id,
            organization_id=source.organization_id,
            name=source.name,
            description=source.description,
            created_at=source.created_at,
            updated_at=source.updated_at,
            document_count=doc_count,
        )

    async def update_source(
        self,
        db: AsyncSession,
        source_id: UUID,
        schema: KnowledgeSourceUpdate,
        organization_id: UUID | None = None,
    ) -> KnowledgeSourceResponse:
        source = await knowledge_source_repository.get_by_id(db, source_id)
        if not source:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        # Enforce organization isolation
        if organization_id is not None and source.organization_id != organization_id:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        new_name = schema.name.strip() if schema.name is not None else None
        if schema.name is not None and not new_name:
            raise BadRequestError("Knowledge source name cannot be empty.")

        new_desc = schema.description.strip() if schema.description is not None else None

        updated_source = await knowledge_source_repository.update(
            db, source, name=new_name, description=new_desc
        )
        await db.commit()
        await db.refresh(updated_source)

        doc_count = await knowledge_source_repository.count_documents(db, updated_source.id)
        return KnowledgeSourceResponse(
            id=updated_source.id,
            organization_id=updated_source.organization_id,
            name=updated_source.name,
            description=updated_source.description,
            created_at=updated_source.created_at,
            updated_at=updated_source.updated_at,
            document_count=doc_count,
        )

    async def delete_source(
        self,
        db: AsyncSession,
        source_id: UUID,
        organization_id: UUID | None = None,
    ) -> None:
        source = await knowledge_source_repository.get_by_id(db, source_id)
        if not source:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        # Enforce organization isolation
        if organization_id is not None and source.organization_id != organization_id:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        await knowledge_source_repository.delete(db, source)
        await db.commit()


knowledge_source_service = KnowledgeSourceService()
