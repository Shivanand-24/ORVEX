from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    """Encapsulates persistence queries for global User entities."""

    async def create(self, db: AsyncSession, email: str, full_name: str) -> User:
        user = User(email=email.lower().strip(), full_name=full_name.strip())
        db.add(user)
        await db.flush()
        return user

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[User]:
        stmt = select(User).order_by(User.full_name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


user_repository = UserRepository()
