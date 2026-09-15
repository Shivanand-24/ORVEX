from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.membership import OrganizationMembership


class MembershipRepository:
    """Encapsulates persistence queries for OrganizationMembership entities."""

    async def create(
        self, db: AsyncSession, organization_id: UUID, user_id: UUID, role: str
    ) -> OrganizationMembership:
        membership = OrganizationMembership(
            organization_id=organization_id, user_id=user_id, role=role
        )
        db.add(membership)
        await db.flush()

        # Re-fetch with user loaded for response
        return await self.get_by_id(db, membership.id)  # type: ignore[return-value]

    async def list_by_organization(
        self, db: AsyncSession, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[OrganizationMembership]:
        stmt = (
            select(OrganizationMembership)
            .options(joinedload(OrganizationMembership.user))
            .where(OrganizationMembership.organization_id == organization_id)
            .order_by(OrganizationMembership.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self, db: AsyncSession, membership_id: UUID
    ) -> OrganizationMembership | None:
        stmt = (
            select(OrganizationMembership)
            .options(joinedload(OrganizationMembership.user))
            .where(OrganizationMembership.id == membership_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_organization_and_user(
        self, db: AsyncSession, organization_id: UUID, user_id: UUID
    ) -> OrganizationMembership | None:
        stmt = (
            select(OrganizationMembership)
            .options(joinedload(OrganizationMembership.user))
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_role(
        self, db: AsyncSession, membership: OrganizationMembership, role: str
    ) -> OrganizationMembership:
        membership.role = role
        await db.flush()
        return membership

    async def delete(self, db: AsyncSession, membership: OrganizationMembership) -> None:
        await db.delete(membership)
        await db.flush()


membership_repository = MembershipRepository()
