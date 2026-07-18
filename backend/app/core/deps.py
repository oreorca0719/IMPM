"""공용 FastAPI 의존성 — 현재 사용자 인증 (+ 봇 대행 impersonation)."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.security import decode_access_token
from app.crud import user as user_crud
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
    x_act_as: str | None = Header(default=None, alias="X-Act-As"),
) -> User:
    """토큰의 사용자를 반환. 단, 인증 주체가 **봇(role=bot)** 이고 `X-Act-As`(이메일)가
    오면 그 사용자로 대행한다 — MCP 호스팅에서 팀원별 활동로그 귀속에 사용.
    봇이 아닌 주체의 X-Act-As 는 무시(권한 상승 방지).
    """
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise _credentials_error
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _credentials_error
    principal = await session.get(User, user_id)
    if principal is None:
        raise _credentials_error

    if x_act_as and principal.role == "bot":
        # 숫자면 사용자 ID, 아니면 이메일로 해석(이메일 변경에도 귀속이 유지되도록)
        if x_act_as.isdigit():
            target = await session.get(User, int(x_act_as))
        else:
            target = await user_crud.get_by_email(session, x_act_as)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"대행 대상 사용자를 찾을 수 없습니다: {x_act_as}",
            )
        return target

    return principal
