"""프로젝트 DB 접근."""
from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Project


async def create(session: AsyncSession, *, key: str, name: str, description: str | None) -> Project:
    project = Project(key=key, name=name, description=description)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def get(session: AsyncSession, project_id: int) -> Project | None:
    return await session.get(Project, project_id)


async def get_by_key(session: AsyncSession, key: str) -> Project | None:
    result = await session.exec(select(Project).where(Project.key == key))
    return result.first()


async def list_all(session: AsyncSession) -> list[Project]:
    result = await session.exec(select(Project).order_by(Project.created_at))
    return list(result.all())
