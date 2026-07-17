"""사용자 DB 접근."""
from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.exec(select(User).where(User.email == email))
    return result.first()


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def list_all(session: AsyncSession) -> list[User]:
    result = await session.exec(select(User).order_by(User.name))
    return list(result.all())
