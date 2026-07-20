"""인증 라우터 — 로그인 / 내 정보 / 아이디·비밀번호 변경."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.crud import user as user_crud
from app.models import User
from app.core.config import settings
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import (
    McpResolveRequest,
    McpResolveResult,
    McpTokenRead,
    PasswordChange,
    ProfileUpdate,
    UserRead,
)
from app.services import mcp_token as mcp_token_service

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


# ─────────────────── Claude(MCP) 개인 토큰 ───────────────────


def _token_payload(token: str) -> McpTokenRead:
    url = settings.mcp_public_url or "https://<MCP-서버-주소>/mcp"
    cmd = (
        "claude mcp add --transport http --scope user impm "
        f'{url} --header "Authorization: Bearer {token}"'
    )
    return McpTokenRead(token=token, mcp_url=url, connect_command=cmd)


@router.get("/mcp-token", response_model=McpTokenRead)
async def my_mcp_token(
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
) -> McpTokenRead:
    """본인의 MCP 연동 토큰 조회(없으면 발급). 다른 사용자의 토큰은 볼 수 없다."""
    token = await mcp_token_service.ensure_token(session, current)
    return _token_payload(token)


@router.post("/mcp-token/rotate", response_model=McpTokenRead)
async def rotate_my_mcp_token(
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
) -> McpTokenRead:
    """토큰 재발급 — 기존 토큰은 즉시 사용 불가."""
    token = await mcp_token_service.rotate_token(session, current)
    return _token_payload(token)


@router.post("/mcp-resolve", response_model=McpResolveResult)
async def resolve_mcp_token(
    payload: McpResolveRequest,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
) -> McpResolveResult:
    """MCP 서버 전용: 개인 토큰 → 사용자 해석. 봇 계정만 호출 가능."""
    if current.role != "bot":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="허용되지 않은 요청입니다.")
    user = await mcp_token_service.get_user_by_token(session, payload.token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유효하지 않은 토큰입니다.")
    return McpResolveResult(id=user.id, email=user.email, name=user.name)
