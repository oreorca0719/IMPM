"""에픽 DB 접근."""
from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Epic


async def get(session: AsyncSession, epic_id: int) -> Epic | None:
    return await session.get(Epic, epic_id)


async def list_by_project(session: AsyncSession, project_id: int) -> list[Epic]:
    result = await session.exec(
        select(Epic).where(Epic.project_id == project_id).order_by(Epic.created_at)
    )
    return list(result.all())
