"""Alembic 환경 — SQLModel 메타데이터 기반, 동기 SQLite 드라이버 사용."""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

import app.models  # noqa: F401  (테이블 메타데이터 등록)
from app.core.config import settings

config = context.config

# 비동기 URL을 동기 드라이버로 변환 — 마이그레이션은 동기 실행
#   sqlite+aiosqlite  -> sqlite
#   postgresql+asyncpg -> postgresql+psycopg2
sync_url = settings.database_url.replace("+aiosqlite", "").replace(
    "+asyncpg", "+psycopg2"
)
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite ALTER 지원
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
