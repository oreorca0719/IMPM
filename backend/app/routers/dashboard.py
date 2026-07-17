"""대시보드 라우터 — 집계 데이터 단일 호출."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import project as project_crud
from app.models import User
from app.schemas.dashboard import DashboardData
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/projects/{pid}/dashboard", response_model=DashboardData)
async def get_dashboard(
    pid: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    if await project_crud.get(session, pid) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return await dashboard_service.build(session, pid)
