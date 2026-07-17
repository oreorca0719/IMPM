"""pytest 공용 픽스처 — in-memory SQLite + httpx AsyncClient."""
from __future__ import annotations

import os

# app import 전에 테스트용 환경변수 강제(설정이 import 시점에 로드됨)
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-prod"
os.environ["JWT_EXPIRE_HOURS"] = "12"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.core.db import async_session_maker, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_setup():
    """각 테스트마다 깨끗한 스키마."""
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_setup):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def session(db_setup):
    async with async_session_maker() as s:
        yield s


@pytest_asyncio.fixture
async def auth(client, session):
    """인증된 사용자 + Authorization 헤더가 준비된 클라이언트 번들."""
    from app.core.security import hash_password
    from app.models import User

    user = User(
        email="kbj@impm.team",
        name="김범준",
        role="admin",
        password_hash=hash_password("pw"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    resp = await client.post(
        "/api/auth/login", json={"email": user.email, "password": "pw"}
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    return {"client": client, "user": user, "headers": headers, "session": session}
