from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.membership import (
    MembershipCreate,
    MembershipResponse,
    MembershipUpdate,
)
from app.services.membership_service import membership_service

router = APIRouter()


@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Organization Member",
    description="Add a user as a member to an organization with a specific role.",
)
async def add_member(
    organization_id: UUID,
    payload: MembershipCreate,
    db: AsyncSession = Depends(get_db_session),
) -> MembershipResponse:
    return await membership_service.add_member(db, organization_id, payload)


@router.get(
    "",
    response_model=List[MembershipResponse],
    status_code=status.HTTP_200_OK,
    summary="List Organization Members",
    description="Retrieve all members belonging to an organization.",
)
async def list_members(
    organization_id: UUID,
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination page size"),
    db: AsyncSession = Depends(get_db_session),
) -> List[MembershipResponse]:
    members = await membership_service.list_members(
        db, organization_id, skip=skip, limit=limit
    )
    return list(members)


@router.patch(
    "/{membership_id}",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Member Role",
    description="Update an organization member's role ('admin', 'member', 'analyst').",
)
async def update_member_role(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> MembershipResponse:
    return await membership_service.update_membership_role(
        db, organization_id, membership_id, payload
    )


@router.delete(
    "/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Organization Member",
    description="Remove a member from an organization.",
)
async def remove_member(
    organization_id: UUID,
    membership_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await membership_service.remove_member(db, organization_id, membership_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
