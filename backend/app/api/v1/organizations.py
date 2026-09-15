from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization_service import organization_service

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new enterprise organization tenant.",
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    return await organization_service.create_organization(db, payload)


@router.get(
    "",
    response_model=List[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Organizations",
    description="Retrieve a paginated list of organizations.",
)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination page size"),
    db: AsyncSession = Depends(get_db_session),
) -> List[OrganizationResponse]:
    orgs = await organization_service.list_organizations(db, skip=skip, limit=limit)
    return list(orgs)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Organization",
    description="Retrieve a single organization by its UUID.",
)
async def get_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    return await organization_service.get_organization(db, organization_id)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Organization",
    description="Update an organization's name or slug.",
)
async def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    return await organization_service.update_organization(db, organization_id, payload)
