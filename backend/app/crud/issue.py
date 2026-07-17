"""이슈 DB 접근 (필터 목록 포함)."""
from __future__ import annotations

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Issue


async def get(session: AsyncSession, issue_id: int) -> Issue | None:
    return await session.get(Issue, issue_id)


async def list_by_project(
    session: AsyncSession,
    project_id: int,
    *,
    status: str | None = None,
    assignee_id: int | None = None,
    epic_id: int | None = None,
    q: str | None = None,
) -> list[Issue]:
    stmt = select(Issue).where(Issue.project_id == project_id)
    if status is not None:
        stmt = stmt.where(Issue.status == status)
    if assignee_id is not None:
        stmt = stmt.where(Issue.assignee_id == assignee_id)
    if epic_id is not None:
        stmt = stmt.where(Issue.epic_id == epic_id)
    if q:
        stmt = stmt.where(col(Issue.title).contains(q))
    stmt = stmt.order_by(Issue.board_order, Issue.id)
    result = await session.exec(stmt)
    return list(result.all())
