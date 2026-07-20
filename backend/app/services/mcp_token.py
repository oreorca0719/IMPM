"""Claude(MCP) 연동용 개인 토큰 관리.

- 토큰의 단일 진실 소스는 DB(users.mcp_token).
- 기존에 MCP 서버 환경변수로 배포했던 토큰은 최초 기동 시 DB로 이관(backfill)하여
  이미 배포된 팀원 토큰이 끊기지 않게 한다.
"""
from __future__ import annotations

import json
import secrets

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import User

TOKEN_BYTES = 20  # hex 40자


def generate_token() -> str:
    return secrets.token_hex(TOKEN_BYTES)


async def ensure_token(session: AsyncSession, user: User) -> str:
    """토큰이 없으면 생성해 저장하고 반환."""
    if user.mcp_token:
        return user.mcp_token
    user.mcp_token = generate_token()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.mcp_token


async def rotate_token(session: AsyncSession, user: User) -> str:
    """새 토큰 발급(기존 토큰은 즉시 무효)."""
    user.mcp_token = generate_token()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.mcp_token


async def get_user_by_token(session: AsyncSession, token: str) -> User | None:
    if not token:
        return None
    result = await session.exec(select(User).where(User.mcp_token == token))
    return result.first()


async def backfill_from_env(session: AsyncSession) -> int:
    """MCP_USER_TOKENS(JSON {token: user_id})의 값을 아직 토큰이 없는 사용자에게 이관."""
    raw = settings.mcp_user_tokens.strip()
    if not raw:
        return 0
    try:
        mapping = json.loads(raw)
    except Exception:
        return 0

    moved = 0
    for token, user_ref in mapping.items():
        user = None
        ref = str(user_ref)
        if ref.isdigit():
            user = await session.get(User, int(ref))
        else:
            result = await session.exec(select(User).where(User.email == ref))
            user = result.first()
        if user is not None and not user.mcp_token:
            user.mcp_token = token
            session.add(user)
            moved += 1
    if moved:
        await session.commit()
    return moved
