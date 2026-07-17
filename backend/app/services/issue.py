"""이슈 비즈니스 로직 — 채번, 보드 정렬값, 생성/수정/이동/삭제.

활동 로그(P3)는 이 계층에서 이슈 변경 트랜잭션과 함께 원자적으로 생성된다.
P2에서는 순수 CRUD만 구현하고, P3에서 활동 기록을 주입한다.
"""
from __future__ import annotations

from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Issue, Project, now_utc
from app.schemas.issue import IssueCreate, IssueMove, IssueUpdate
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
    await session.commit()
    await session.refresh(issue)
    return issue


async def update_issue(session: AsyncSession, *, issue: Issue, data: IssueUpdate) -> Issue:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(issue, field, _enum_value(value))
    issue.updated_at = now_utc()
    session.add(issue)
    await session.commit()
    await session.refresh(issue)
    return issue


async def move_issue(session: AsyncSession, *, issue: Issue, data: IssueMove) -> Issue:
    issue.status = data.status.value
    issue.board_order = data.board_order
    issue.updated_at = now_utc()
    session.add(issue)
    await session.commit()
    await session.refresh(issue)
    return issue


async def delete_issue(session: AsyncSession, *, issue: Issue) -> None:
    # 자식 레코드 먼저 정리(FK 제약)
    for tbl in ("issue_labels", "comments", "activity_logs"):
        await session.execute(
            text(f"DELETE FROM {tbl} WHERE issue_id = :iid"), {"iid": issue.id}
        )
    await session.delete(issue)
    await session.commit()
