"""IMPM FastAPI 앱 — 라우터 등록, CORS, 헬스체크."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 개발 편의: 앱 기동 시 테이블 보장(운영 스키마 변경은 Alembic 사용)
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_desc,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


# ── 라우터 등록 (Phase 진행하며 확장) ──────────────────────────
from app.routers import auth, comments, dashboard, epics, issues, labels, projects, users  # noqa: E402

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(epics.router)
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(labels.router)
app.include_router(dashboard.router)
