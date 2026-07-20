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
    # 환경변수로 배포했던 MCP 토큰을 DB로 1회 이관(이미 있으면 no-op)
    from app.core.db import async_session_maker
    from app.services import mcp_token as mcp_token_service

    try:
        async with async_session_maker() as session:
            moved = await mcp_token_service.backfill_from_env(session)
            if moved:
                print(f"[startup] MCP 토큰 {moved}건 DB로 이관")
    except Exception as e:  # 이관 실패가 기동을 막지 않도록
        print(f"[startup] MCP 토큰 이관 건너뜀: {e}")
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


# ── 프론트 SPA 서빙 (배포 시 단일 서비스로 SPA+API 제공) ──────────
# FRONTEND_DIST 가 설정되고 존재하면, 빌드된 Vue 정적 파일을 서빙하고
# SPA 라우팅을 위해 알 수 없는 경로는 index.html 로 폴백한다(로컬 dev 는 미설정).
import os  # noqa: E402

from fastapi import HTTPException  # noqa: E402
from starlette.responses import FileResponse  # noqa: E402
from starlette.staticfiles import StaticFiles  # noqa: E402

_frontend_dist = os.getenv("FRONTEND_DIST")
if _frontend_dist and os.path.isdir(_frontend_dist):
    _assets = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    _index = os.path.join(_frontend_dist, "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # API/문서 경로는 SPA 폴백에서 제외(정의된 라우터가 우선하지만 방어적으로 404)
        if full_path.startswith(("api", "docs", "openapi.json", "redoc")):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = os.path.join(_frontend_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(_index)
