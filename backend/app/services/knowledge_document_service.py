from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.knowledge import KnowledgeDocument
from app.repositories.knowledge_document_repository import knowledge_document_repository
from app.repositories.knowledge_source_repository import knowledge_source_repository
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
)


class KnowledgeDocumentService:
    """Business logic, lifecycle validation, and transaction boundaries for Knowledge Documents."""

    async def create_document(
        self,
        db: AsyncSession,
        source_id: UUID,
        schema: KnowledgeDocumentCreate,
        organization_id: UUID | None = None,
    ) -> KnowledgeDocument:
        # Validate parent knowledge source exists
        source = await knowledge_source_repository.get_by_id(db, source_id)
        if not source:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        # Enforce organization boundary
        if organization_id is not None and source.organization_id != organization_id:
            raise BadRequestError(
                f"Knowledge source '{source_id}' does not belong to organization '{organization_id}'."
            )

        if schema.organization_id is not None and schema.organization_id != source.organization_id:
            raise BadRequestError(
                f"Document organization_id '{schema.organization_id}' mismatch: does not match source organization_id '{source.organization_id}'."
            )

        doc_name = schema.name.strip()
        if not doc_name:
            raise BadRequestError("Document name cannot be empty.")

        # Storage path fallback
        storage_path = (
            schema.storage_path.strip()
            if schema.storage_path
            else f"storage://sources/{source.id}/{doc_name}"
        )

        proc_status = schema.processing_status or "pending"
        idx_status = schema.indexing_status or "not_indexed"

        # Lifecycle rule: Cannot start indexing until processing is completed
        if idx_status in ("indexing", "indexed") and proc_status != "processed":
            raise BadRequestError(
                f"Document must be in 'processed' state before indexing (current processing status: '{proc_status}')."
            )

        document = await knowledge_document_repository.create(
            db=db,
            organization_id=source.organization_id,
            source_id=source.id,
            name=doc_name,
            file_type=schema.file_type.strip().upper(),
            storage_path=storage_path,
            size_bytes=schema.size_bytes,
            processing_status=proc_status,
            indexing_status=idx_status,
            summary=schema.summary.strip() if schema.summary else None,
        )
        await db.commit()
        await db.refresh(document)
        return document

    async def list_documents_by_source(
        self,
        db: AsyncSession,
        source_id: UUID,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[KnowledgeDocument]:
        source = await knowledge_source_repository.get_by_id(db, source_id)
        if not source:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        # Enforce organization isolation
        if organization_id is not None and source.organization_id != organization_id:
            raise NotFoundError(f"Knowledge source with ID '{source_id}' not found.")

        return await knowledge_document_repository.list_by_source(
            db, source_id=source_id, skip=skip, limit=limit
        )

    async def get_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        organization_id: UUID | None = None,
    ) -> KnowledgeDocument:
        doc = await knowledge_document_repository.get_by_id(db, document_id)
        if not doc:
            raise NotFoundError(f"Knowledge document with ID '{document_id}' not found.")

        # Enforce organization isolation
        if organization_id is not None and doc.organization_id != organization_id:
            raise NotFoundError(f"Knowledge document with ID '{document_id}' not found.")

        return doc

    async def update_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        schema: KnowledgeDocumentUpdate,
        organization_id: UUID | None = None,
    ) -> KnowledgeDocument:
        doc = await self.get_document(db, document_id, organization_id=organization_id)

        update_fields: dict = {}

        if schema.name is not None:
            name = schema.name.strip()
            if not name:
                raise BadRequestError("Document name cannot be empty.")
            update_fields["name"] = name

        if schema.file_type is not None:
            update_fields["file_type"] = schema.file_type.strip().upper()

        if schema.storage_path is not None:
            update_fields["storage_path"] = schema.storage_path.strip()

        if schema.size_bytes is not None:
            update_fields["size_bytes"] = schema.size_bytes

        if schema.summary is not None:
            update_fields["summary"] = schema.summary.strip()

        # Check lifecycle transitions
        new_proc = schema.processing_status if schema.processing_status is not None else doc.processing_status
        new_idx = schema.indexing_status if schema.indexing_status is not None else doc.indexing_status

        if new_idx in ("indexing", "indexed") and new_proc != "processed":
            raise BadRequestError(
                f"Document must be in 'processed' state before indexing (current processing status: '{new_proc}')."
            )

        if schema.processing_status is not None:
            update_fields["processing_status"] = new_proc

        if schema.indexing_status is not None:
            update_fields["indexing_status"] = new_idx

        updated_doc = await knowledge_document_repository.update(db, doc, **update_fields)
        await db.commit()
        await db.refresh(updated_doc)
        return updated_doc

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        organization_id: UUID | None = None,
    ) -> None:
        doc = await self.get_document(db, document_id, organization_id=organization_id)
        await knowledge_document_repository.delete(db, doc)
        await db.commit()


knowledge_document_service = KnowledgeDocumentService()
