"""비동기 DB 세션 · 테이블 생성.

SQLite(로컬/테스트)와 PostgreSQL(배포·RDS)을 모두 지원한다.
SQLite 전용 설정(WAL·check_same_thread·StaticPool)은 dialect 로 분기한다.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
# in-memory(:memory:)는 커넥션마다 별도 DB가 되므로 StaticPool 필요
_is_memory = ":memory:" in settings.database_url

_engine_kwargs: dict = {"echo": False, "future": True}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    if _is_memory:
        _engine_kwargs["poolclass"] = StaticPool
else:
    # Postgres 등: 커넥션 풀 재활용(유휴 커넥션 회수)
    _engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.database_url, **_engine_kwargs)


if _is_sqlite:

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record):
        """SQLite 커넥션에 WAL 모드 + 외래키 제약 활성화."""
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()


async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성: 요청 스코프 DB 세션."""
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """테이블 생성(SQLModel.metadata 기준; 스키마 버전 관리는 Alembic)."""
    import app.models  # noqa: F401  (메타데이터 등록)

    async with engine.begin() as conn:
        if _is_sqlite:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.run_sync(SQLModel.metadata.create_all)
