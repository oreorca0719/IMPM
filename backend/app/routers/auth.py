"""인증 라우터 — 로그인 / 내 정보 / 아이디·비밀번호 변경."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.crud import user as user_crud
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import PasswordChange, ProfileUpdate, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _bad_password() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="현재 비밀번호가 올바르지 않습니다.",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await user_crud.get_by_email(session, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
) -> UserRead:
    """아이디(이메일)·이름 변경. 본인 확인을 위해 현재 비밀번호를 받는다."""
    if not verify_password(payload.current_password, current.password_hash):
        raise _bad_password()

    if payload.email and payload.email != current.email:
        existing = await user_crud.get_by_email(session, payload.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            )
        current.email = payload.email

    if payload.name:
        current.name = payload.name

    session.add(current)
    await session.commit()
    await session.refresh(current)
    return UserRead.model_validate(current)


@router.post("/password", response_model=UserRead)
async def change_password(
    payload: PasswordChange,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
) -> UserRead:
    """비밀번호 변경. 성공 시 '변경 필요' 플래그를 해제한다."""
    if not verify_password(payload.current_password, current.password_hash):
        raise _bad_password()
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호가 현재 비밀번호와 같습니다.",
        )

    current.password_hash = hash_password(payload.new_password)
    current.must_change_password = False
    session.add(current)
    await session.commit()
    await session.refresh(current)
    return UserRead.model_validate(current)
