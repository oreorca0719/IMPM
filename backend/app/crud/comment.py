"""댓글 · 활동로그 DB 접근."""
from __future__ import annotations

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ActivityLog, Comment, now_utc


async def create(session: AsyncSession, *, issue_id: int, author_id: int, body: str) -> Comment:
    comment = Comment(issue_id=issue_id, author_id=author_id, body=body)
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


async def get(session: AsyncSession, comment_id: int) -> Comment | None:
    return await session.get(Comment, comment_id)


async def list_by_issue(session: AsyncSession, issue_id: int) -> list[Comment]:
    result = await session.exec(
        select(Comment).where(Comment.issue_id == issue_id).order_by(Comment.created_at)
    )
    return list(result.all())


async def update(session: AsyncSession, *, comment: Comment, body: str) -> Comment:
    comment.body = body
    comment.updated_at = now_utc()
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


async def delete(session: AsyncSession, *, comment: Comment) -> None:
    await session.delete(comment)
    await session.commit()


async def list_activity(session: AsyncSession, issue_id: int) -> list[ActivityLog]:
    result = await session.exec(
        select(ActivityLog)
        .where(ActivityLog.issue_id == issue_id)
        .order_by(col(ActivityLog.created_at).desc(), col(ActivityLog.id).desc())
    )
    return list(result.all())
