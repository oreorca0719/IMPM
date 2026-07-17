"""공용 FastAPI 의존성 — 현재 사용자 인증."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.security import decode_access_token
from app.models import User

bearer_scheme = HTTPBearer(auto_error=True)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="유효하지 않은 인증 정보입니다.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise _credentials_error
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _credentials_error
    user = await session.get(User, user_id)
    if user is None:
        raise _credentials_error
    return user
