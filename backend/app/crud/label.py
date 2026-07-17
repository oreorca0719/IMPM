"""라벨 DB 접근 (라벨 정의 + 이슈-라벨 M:N)."""
from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import IssueLabel, Label


async def create(session: AsyncSession, *, project_id: int, name: str, color: str) -> Label:
    label = Label(project_id=project_id, name=name, color=color)
    session.add(label)
    await session.commit()
    await session.refresh(label)
    return label


async def get(session: AsyncSession, label_id: int) -> Label | None:
    return await session.get(Label, label_id)


async def list_by_project(session: AsyncSession, project_id: int) -> list[Label]:
    result = await session.exec(
        select(Label).where(Label.project_id == project_id).order_by(Label.name)
    )
    return list(result.all())


async def list_for_issue(session: AsyncSession, issue_id: int) -> list[Label]:
    result = await session.exec(
        select(Label)
        .join(IssueLabel, IssueLabel.label_id == Label.id)
        .where(IssueLabel.issue_id == issue_id)
        .order_by(Label.name)
    )
    return list(result.all())


async def attach(session: AsyncSession, *, issue_id: int, label_id: int) -> None:
    exists = await session.get(IssueLabel, (issue_id, label_id))
    if exists is None:
        session.add(IssueLabel(issue_id=issue_id, label_id=label_id))
        await session.commit()


async def detach(session: AsyncSession, *, issue_id: int, label_id: int) -> None:
    link = await session.get(IssueLabel, (issue_id, label_id))
    if link is not None:
        await session.delete(link)
        await session.commit()
