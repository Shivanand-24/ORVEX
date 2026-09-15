from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization


class OrganizationRepository:
    """Encapsulates persistence queries for Organization entities."""

    async def create(self, db: AsyncSession, name: str, slug: str) -> Organization:
        organization = Organization(name=name, slug=slug)
        db.add(organization)
        await db.flush()
        return organization

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[Organization]:
        stmt = select(Organization).order_by(Organization.name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, organization_id: UUID) -> Organization | None:
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Organization | None:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        organization: Organization,
        name: str | None = None,
        slug: str | None = None,
    ) -> Organization:
        if name is not None:
            organization.name = name
        if slug is not None:
            organization.slug = slug
        await db.flush()
        return organization


organization_repository = OrganizationRepository()
