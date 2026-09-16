from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument


class KnowledgeDocumentRepository:
    """Encapsulates database access for KnowledgeDocument entities."""

    async def create(
        self,
        db: AsyncSession,
        organization_id: UUID,
        source_id: UUID,
        name: str,
        file_type: str,
        storage_path: str,
        size_bytes: int,
        processing_status: str = "pending",
        indexing_status: str = "not_indexed",
        summary: str | None = None,
    ) -> KnowledgeDocument:
        document = KnowledgeDocument(
            organization_id=organization_id,
            source_id=source_id,
            name=name,
            file_type=file_type,
            storage_path=storage_path,
            size_bytes=size_bytes,
            processing_status=processing_status,
            indexing_status=indexing_status,
            summary=summary,
        )
        db.add(document)
        await db.flush()
        return document

    async def list_by_source(
        self,
        db: AsyncSession,
        source_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.source_id == source_id)
            .order_by(KnowledgeDocument.name)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self, db: AsyncSession, document_id: UUID
    ) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        document: KnowledgeDocument,
        **fields,
    ) -> KnowledgeDocument:
        for key, value in fields.items():
            if value is not None and hasattr(document, key):
                setattr(document, key, value)
        await db.flush()
        return document

    async def delete(self, db: AsyncSession, document: KnowledgeDocument) -> None:
        await db.delete(document)
        await db.flush()


knowledge_document_repository = KnowledgeDocumentRepository()
