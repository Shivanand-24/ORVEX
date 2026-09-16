from typing import Sequence
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument, KnowledgeSource


class KnowledgeSourceRepository:
    """Encapsulates database access for KnowledgeSource entities."""

    async def create(
        self,
        db: AsyncSession,
        organization_id: UUID,
        name: str,
        description: str | None = None,
    ) -> KnowledgeSource:
        source = KnowledgeSource(
            organization_id=organization_id,
            name=name,
            description=description,
        )
        db.add(source)
        await db.flush()
        return source

    async def list(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[KnowledgeSource]:
        stmt = select(KnowledgeSource)
        if organization_id is not None:
            stmt = stmt.where(KnowledgeSource.organization_id == organization_id)
        stmt = stmt.order_by(KnowledgeSource.name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self, db: AsyncSession, source_id: UUID
    ) -> KnowledgeSource | None:
        stmt = select(KnowledgeSource).where(KnowledgeSource.id == source_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        source: KnowledgeSource,
        name: str | None = None,
        description: str | None = None,
    ) -> KnowledgeSource:
        if name is not None:
            source.name = name
        if description is not None:
            source.description = description
        await db.flush()
        return source

    async def delete(self, db: AsyncSession, source: KnowledgeSource) -> None:
        await db.delete(source)
        await db.flush()

    async def count_documents(self, db: AsyncSession, source_id: UUID) -> int:
        stmt = select(func.count(KnowledgeDocument.id)).where(
            KnowledgeDocument.source_id == source_id
        )
        result = await db.execute(stmt)
        return result.scalar_one() or 0


knowledge_source_repository = KnowledgeSourceRepository()
