"""사용자 라우터 — 담당자 지정용 목록 / 관리자 계정 삭제."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import user as user_crud
from app.models import ActivityLog, Comment, Epic, Issue, User
from app.schemas.user import UserRead

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _current: User = Depends(get_current_user),
) -> list[UserRead]:
    users = await user_crud.list_all(session)
    return [UserRead.model_validate(u) for u in users]


async def _reference_count(session: AsyncSession, uid: int) -> int:
    """해당 사용자를 참조하는 데이터 수(삭제 안전성 확인용)."""
    checks = [
        select(func.count()).select_from(Issue).where(Issue.reporter_id == uid),
        select(func.count()).select_from(Issue).where(Issue.assignee_id == uid),
        select(func.count()).select_from(Epic).where(Epic.owner_id == uid),
        select(func.count()).select_from(Comment).where(Comment.author_id == uid),
        select(func.count()).select_from(ActivityLog).where(ActivityLog.actor_id == uid),
    ]
    total = 0
    for stmt in checks:
        total += (await session.exec(stmt)).one()
    return total


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    uid: int,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    """계정 삭제 — 관리자 전용. 본인은 삭제 불가, 데이터가 있으면 409."""
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 계정을 삭제할 수 있습니다.")
    if uid == current.id:
        raise HTTPException(status_code=400, detail="본인 계정은 삭제할 수 없습니다.")

    target = await session.get(User, uid)
    if target is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    refs = await _reference_count(session, uid)
    if refs:
        raise HTTPException(
            status_code=409,
            detail=f"이 계정과 연결된 데이터가 {refs}건 있어 삭제할 수 없습니다.",
        )

    await session.delete(target)
    await session.commit()
