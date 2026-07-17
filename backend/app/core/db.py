"""비동기 SQLite 세션 · WAL 모드 활성화 · 테이블 생성."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

# 테스트에서 in-memory(:memory:)를 쓰면 커넥션마다 별도 DB가 되므로 StaticPool 필요
_is_memory = ":memory:" in settings.database_url

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool if _is_memory else None,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _record):
    """모든 커넥션에 WAL 모드 + 외래키 제약 활성화."""
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
    """테이블 생성(1차는 SQLModel.metadata 기준; 스키마 버전 관리는 Alembic)."""
    # 모델 모듈 import로 메타데이터에 테이블 등록 보장
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.run_sync(SQLModel.metadata.create_all)
