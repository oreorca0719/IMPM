"""댓글 라우터 + 이슈 활동 로그 조회."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import comment as comment_crud
from app.crud import issue as issue_crud
from app.models import User
from app.schemas.comment import (
    ActivityRead,
    CommentCreate,
    CommentRead,
    CommentUpdate,
)

router = APIRouter(prefix="/api", tags=["comments"])


async def _issue_or_404(session: AsyncSession, issue_id: int):
    issue = await issue_crud.get(session, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다.")
    return issue


@router.get("/issues/{issue_id}/comments", response_model=list[CommentRead])
async def list_comments(
    issue_id: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    await _issue_or_404(session, issue_id)
    return await comment_crud.list_by_issue(session, issue_id)


@router.post(
    "/issues/{issue_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    issue_id: int,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    await _issue_or_404(session, issue_id)
    return await comment_crud.create(
        session, issue_id=issue_id, author_id=current.id, body=payload.body
    )


@router.patch("/comments/{cid}", response_model=CommentRead)
async def update_comment(
    cid: int,
    payload: CommentUpdate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    comment = await comment_crud.get(session, cid)
    if comment is None:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.author_id != current.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 수정할 수 있습니다.")
    return await comment_crud.update(session, comment=comment, body=payload.body)


@router.delete("/comments/{cid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    cid: int,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    comment = await comment_crud.get(session, cid)
    if comment is None:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.author_id != current.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 삭제할 수 있습니다.")
    await comment_crud.delete(session, comment=comment)


@router.get("/issues/{issue_id}/activity", response_model=list[ActivityRead])
async def issue_activity(
    issue_id: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    await _issue_or_404(session, issue_id)
    return await comment_crud.list_activity(session, issue_id)
