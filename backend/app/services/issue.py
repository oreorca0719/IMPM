"""이슈 비즈니스 로직 — 채번, 보드 정렬값, 생성/수정/이동/삭제.

이슈 변경 시 활동 로그를 동일 트랜잭션에서 원자적으로 생성한다(P3).
"""
from __future__ import annotations

from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ActivityAction, Issue, Project, now_utc
from app.schemas.issue import IssueCreate, IssueMove, IssueUpdate
from app.services import activity as activity_service
from app.services.keys import next_key


async def _next_board_order(session: AsyncSession, project_id: int, status: str) -> float:
    result = await session.exec(
        select(func.coalesce(func.max(Issue.board_order), 0.0)).where(
            Issue.project_id == project_id, Issue.status == status
        )
    )
    return float(result.one()) + 1.0


def _enum_value(v):
    return v.value if hasattr(v, "value") else v


async def create_issue(
    session: AsyncSession, *, project: Project, reporter_id: int, data: IssueCreate
) -> Issue:
    key = await next_key(session, project_id=project.id, project_key=project.key)
    order = await _next_board_order(session, project.id, data.status.value)
    issue = Issue(
        project_id=project.id,
        epic_id=data.epic_id,
        key=key,
        title=data.title,
        description=data.description,
        status=data.status.value,
        priority=data.priority.value,
        assignee_id=data.assignee_id,
        reporter_id=reporter_id,
        due_date=data.due_date,
        board_order=order,
    )
    session.add(issue)
    await session.flush()  # issue.id 확보
    session.add(
        activity_service.build(
            issue_id=issue.id,
            actor_id=reporter_id,
            action=ActivityAction.created,
        )
    )
    await session.commit()
    await session.refresh(issue)
    return issue


async def update_issue(
    session: AsyncSession, *, issue: Issue, actor_id: int, data: IssueUpdate
) -> Issue:
    changes = data.model_dump(exclude_unset=True)
    logs = []
    for field, raw in changes.items():
        new_value = _enum_value(raw)
        old_value = getattr(issue, field)
        if field in activity_service.TRACKED and old_value != new_value:
            action, log_field = activity_service.TRACKED[field]
            logs.append(
                activity_service.build(
                    issue_id=issue.id,
                    actor_id=actor_id,
                    action=action,
                    field=log_field,
                    old=old_value,
                    new=new_value,
                )
            )
        setattr(issue, field, new_value)

    issue.updated_at = now_utc()
    session.add(issue)
    for log in logs:
        session.add(log)
    await session.commit()
    await session.refresh(issue)
    return issue


async def move_issue(
    session: AsyncSession, *, issue: Issue, actor_id: int, data: IssueMove
) -> Issue:
    old_status = issue.status
    new_status = data.status.value
    issue.status = new_status
    issue.board_order = data.board_order
    issue.updated_at = now_utc()
    session.add(issue)
    if old_status != new_status:
        session.add(
            activity_service.build(
                issue_id=issue.id,
                actor_id=actor_id,
                action=ActivityAction.status_changed,
                field="status",
                old=old_status,
                new=new_status,
            )
        )
    await session.commit()
    await session.refresh(issue)
    return issue


async def delete_issue(session: AsyncSession, *, issue: Issue) -> None:
    for tbl in ("issue_labels", "comments", "activity_logs"):
        await session.execute(
            text(f"DELETE FROM {tbl} WHERE issue_id = :iid"), {"iid": issue.id}
        )
    await session.delete(issue)
    await session.commit()
