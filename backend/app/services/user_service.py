from typing import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate


class UserService:
    """Business logic for Global User management."""

    async def create_user(self, db: AsyncSession, schema: UserCreate) -> User:
        email = schema.email.lower().strip()

        # Check email uniqueness
        existing = await user_repository.get_by_email(db, email)
        if existing:
            raise ConflictError(f"User with email '{email}' already exists.")

        user = await user_repository.create(db, email=email, full_name=schema.full_name)
        await db.commit()
        await db.refresh(user)
        return user

    async def list_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[User]:
        return await user_repository.list(db, skip=skip, limit=limit)

    async def get_user(self, db: AsyncSession, user_id: UUID) -> User:
        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise NotFoundError(f"User with ID '{user_id}' not found.")
        return user


user_service = UserService()
