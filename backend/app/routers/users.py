"""사용자 라우터 — 담당자 지정용 목록."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import user as user_crud
from app.models import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _current: User = Depends(get_current_user),
) -> list[UserRead]:
    users = await user_crud.list_all(session)
    return [UserRead.model_validate(u) for u in users]
