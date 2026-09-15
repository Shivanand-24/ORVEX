from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.membership import OrganizationMembership
from app.repositories.membership_repository import membership_repository
from app.repositories.organization_repository import organization_repository
from app.repositories.user_repository import user_repository
from app.schemas.membership import MembershipCreate, MembershipUpdate


class MembershipService:
    """Business logic for Organization Membership management."""

    async def add_member(
        self, db: AsyncSession, organization_id: UUID, schema: MembershipCreate
    ) -> OrganizationMembership:
        # Verify organization exists
        org = await organization_repository.get_by_id(db, organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        # Verify user exists
        user = await user_repository.get_by_id(db, schema.user_id)
        if not user:
            raise NotFoundError(f"User with ID '{schema.user_id}' not found.")

        # Check duplicate membership
        existing = await membership_repository.find_by_organization_and_user(
            db, organization_id, schema.user_id
        )
        if existing:
            raise ConflictError(
                f"User '{schema.user_id}' is already a member of organization '{organization_id}'."
            )

        membership = await membership_repository.create(
            db, organization_id=organization_id, user_id=schema.user_id, role=schema.role
        )
        await db.commit()
        return membership

    async def list_members(
        self, db: AsyncSession, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[OrganizationMembership]:
        # Verify organization exists
        org = await organization_repository.get_by_id(db, organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        return await membership_repository.list_by_organization(
            db, organization_id, skip=skip, limit=limit
        )

    async def update_membership_role(
        self,
        db: AsyncSession,
        organization_id: UUID,
        membership_id: UUID,
        schema: MembershipUpdate,
    ) -> OrganizationMembership:
        # Verify organization exists
        org = await organization_repository.get_by_id(db, organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        # Get membership
        membership = await membership_repository.get_by_id(db, membership_id)
        if not membership:
            raise NotFoundError(f"Membership with ID '{membership_id}' not found.")

        # Cross-organization verification
        if membership.organization_id != organization_id:
            raise NotFoundError(
                f"Membership '{membership_id}' does not belong to organization '{organization_id}'."
            )

        updated = await membership_repository.update_role(db, membership, role=schema.role)
        await db.commit()
        return updated

    async def remove_member(
        self, db: AsyncSession, organization_id: UUID, membership_id: UUID
    ) -> None:
        # Verify organization exists
        org = await organization_repository.get_by_id(db, organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        # Get membership
        membership = await membership_repository.get_by_id(db, membership_id)
        if not membership:
            raise NotFoundError(f"Membership with ID '{membership_id}' not found.")

        # Cross-organization verification
        if membership.organization_id != organization_id:
            raise NotFoundError(
                f"Membership '{membership_id}' does not belong to organization '{organization_id}'."
            )

        await membership_repository.delete(db, membership)
        await db.commit()


membership_service = MembershipService()
