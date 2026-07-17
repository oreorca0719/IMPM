"""에픽 비즈니스 로직 — 키 채번, 진행률 집계, 삭제 시 이슈 분리."""
from __future__ import annotations

from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Epic, Issue, Project
from app.schemas.epic import EpicCreate, EpicUpdate
from app.services.keys import next_key


async def create_epic(session: AsyncSession, *, project: Project, data: EpicCreate) -> Epic:
    key = await next_key(session, project_id=project.id, project_key=project.key)
    epic = Epic(
        project_id=project.id,
        key=key,
        title=data.title,
        description=data.description,
        status=data.status.value,
        owner_id=data.owner_id,
    )
    session.add(epic)
    await session.commit()
    await session.refresh(epic)
    return epic


async def update_epic(session: AsyncSession, *, epic: Epic, data: EpicUpdate) -> Epic:
    changes = data.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] is not None:
        changes["status"] = changes["status"].value if hasattr(changes["status"], "value") else changes["status"]
    for field, value in changes.items():
        setattr(epic, field, value)
    epic.updated_at = _now()
    session.add(epic)
    await session.commit()
    await session.refresh(epic)
    return epic


async def delete_epic(session: AsyncSession, *, epic: Epic) -> None:
    # 소속 이슈는 epic_id=null 로 분리
    await session.execute(
        text("UPDATE issues SET epic_id = NULL WHERE epic_id = :eid"),
        {"eid": epic.id},
    )
    await session.delete(epic)
    await session.commit()


async def progress_map(session: AsyncSession, project_id: int) -> dict[int, tuple[int, int]]:
    """epic_id -> (done, total). 에픽 미소속(NULL) 제외."""
    result = await session.exec(
        select(Issue.epic_id, Issue.status, func.count())
        .where(Issue.project_id == project_id, Issue.epic_id.is_not(None))
        .group_by(Issue.epic_id, Issue.status)
    )
    agg: dict[int, list[int]] = {}
    for epic_id, status, cnt in result.all():
        bucket = agg.setdefault(epic_id, [0, 0])
        bucket[1] += cnt
        if status == "DONE":
            bucket[0] += cnt
    return {eid: (v[0], v[1]) for eid, v in agg.items()}


def percent(done: int, total: int) -> int:
    return round(done / total * 100) if total else 0


def _now():
    from app.models import now_utc

    return now_utc()
