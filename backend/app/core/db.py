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


async def _ensure_columns(conn) -> None:
    """기존 DB에 없는 컬럼을 멱등하게 추가(간이 마이그레이션).

    운영 DB(RDS)는 프라이빗이라 외부에서 Alembic 실행이 어려워, 앱 부팅 시 보정한다.
    새 DB에서는 create_all 이 이미 만들어 두므로 no-op.
    """
    if _is_sqlite:
        rows = await conn.exec_driver_sql("PRAGMA table_info(users)")
        cols = {r[1] for r in rows.fetchall()}
        if "must_change_password" not in cols:
            await conn.exec_driver_sql(
                "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 1"
            )
        if "mcp_token" not in cols:
            await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN mcp_token VARCHAR")
    else:
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
            "must_change_password BOOLEAN NOT NULL DEFAULT TRUE"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS mcp_token VARCHAR"
        )
    await conn.exec_driver_sql(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_mcp_token ON users (mcp_token)"
    )


async def init_db() -> None:
    """테이블 생성(SQLModel.metadata 기준; 스키마 버전 관리는 Alembic)."""
    import app.models  # noqa: F401  (메타데이터 등록)

    async with engine.begin() as conn:
        if _is_sqlite:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.run_sync(SQLModel.metadata.create_all)
        await _ensure_columns(conn)
