import re
from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.organization import Organization
from app.repositories.organization_repository import organization_repository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


def slugify(text: str) -> str:
    """Generates a clean URL-friendly slug from string."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "org"


class OrganizationService:
    """Business logic for Organization management."""

    async def create_organization(
        self, db: AsyncSession, schema: OrganizationCreate
    ) -> Organization:
        name = schema.name.strip()
        slug = schema.slug.strip() if schema.slug else slugify(name)

        # Check slug uniqueness
        existing = await organization_repository.get_by_slug(db, slug)
        if existing:
            raise ConflictError(f"Organization with slug '{slug}' already exists.")

        org = await organization_repository.create(db, name=name, slug=slug)
        await db.commit()
        await db.refresh(org)
        return org

    async def list_organizations(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Organization]:
        return await organization_repository.list(db, skip=skip, limit=limit)

    async def get_organization(self, db: AsyncSession, organization_id: UUID) -> Organization:
        org = await organization_repository.get_by_id(db, organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{organization_id}' not found.")
        return org

    async def update_organization(
        self, db: AsyncSession, organization_id: UUID, schema: OrganizationUpdate
    ) -> Organization:
        org = await self.get_organization(db, organization_id)

        new_name = schema.name.strip() if schema.name is not None else None
        new_slug = schema.slug.strip() if schema.slug is not None else None

        if new_slug and new_slug != org.slug:
            existing = await organization_repository.get_by_slug(db, new_slug)
            if existing:
                raise ConflictError(f"Organization with slug '{new_slug}' already exists.")

        updated_org = await organization_repository.update(
            db, org, name=new_name, slug=new_slug
        )
        await db.commit()
        await db.refresh(updated_org)
        return updated_org


organization_service = OrganizationService()
