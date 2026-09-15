from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import user_service

router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a global user identity.",
)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await user_service.create_user(db, payload)


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List Users",
    description="Retrieve a paginated list of global users.",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination page size"),
    db: AsyncSession = Depends(get_db_session),
) -> List[UserResponse]:
    users = await user_service.list_users(db, skip=skip, limit=limit)
    return list(users)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User",
    description="Retrieve a single user by their UUID.",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await user_service.get_user(db, user_id)
