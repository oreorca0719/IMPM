"""대시보드 집계 — 상태별 수, 에픽 진행률, 담당자별 부하, 마감 임박."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import epic as epic_crud
from app.models import Issue, User
from app.schemas.dashboard import (
    AssigneeLoadItem,
    DashboardData,
    DueSoonItem,
    EpicProgressItem,
)
from app.services import epic as epic_service

DUE_SOON_DAYS = 7


async def build(session: AsyncSession, project_id: int) -> DashboardData:
    # 상태별 이슈 수
    status_rows = (
        await session.exec(
            select(Issue.status, func.count())
            .where(Issue.project_id == project_id)
            .group_by(Issue.status)
        )
    ).all()
    status_counts = {s: c for s, c in status_rows}

    # 에픽별 진행률
    epics = await epic_crud.list_by_project(session, project_id)
    pmap = await epic_service.progress_map(session, project_id)
    epic_progress = []
    for e in epics:
        done, total = pmap.get(e.id, (0, 0))
        epic_progress.append(
            EpicProgressItem(
                epic_key=e.key,
                title=e.title,
                done=done,
                total=total,
                percent=epic_service.percent(done, total),
            )
        )

    # 담당자별 오픈/완료
    load_rows = (
        await session.exec(
            select(Issue.assignee_id, Issue.status, func.count())
            .where(Issue.project_id == project_id)
            .group_by(Issue.assignee_id, Issue.status)
        )
    ).all()
    users = {u.id: u.name for u in (await session.exec(select(User))).all()}
    agg: dict[str, dict[str, int]] = {}
    for assignee_id, status, cnt in load_rows:
        name = users.get(assignee_id, "미지정") if assignee_id else "미지정"
        bucket = agg.setdefault(name, {"open": 0, "done": 0})
        if status == "DONE":
            bucket["done"] += cnt
        else:
            bucket["open"] += cnt
    assignee_load = [
        AssigneeLoadItem(user=name, open=v["open"], done=v["done"])
        for name, v in sorted(agg.items())
    ]

    # 마감 임박(7일 이내, 완료 제외)
    horizon = date.today() + timedelta(days=DUE_SOON_DAYS)
    due_rows = (
        await session.exec(
            select(Issue)
            .where(
                Issue.project_id == project_id,
                Issue.due_date.is_not(None),
                Issue.due_date <= horizon,
                Issue.status != "DONE",
            )
            .order_by(col(Issue.due_date))
        )
    ).all()
    due_soon = [
        DueSoonItem(id=i.id, key=i.key, title=i.title, due_date=i.due_date)
        for i in due_rows
    ]

    return DashboardData(
        status_counts=status_counts,
        epic_progress=epic_progress,
        assignee_load=assignee_load,
        due_soon=due_soon,
    )
