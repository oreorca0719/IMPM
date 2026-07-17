"""라벨 라우터 — 프로젝트 스코프 라벨 목록/생성."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import label as label_crud
from app.crud import project as project_crud
from app.models import User
from app.schemas.label import LabelCreate, LabelRead

router = APIRouter(prefix="/api", tags=["labels"])


@router.get("/projects/{pid}/labels", response_model=list[LabelRead])
async def list_labels(
    pid: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    if await project_crud.get(session, pid) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return await label_crud.list_by_project(session, pid)


@router.post(
    "/projects/{pid}/labels",
    response_model=LabelRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_label(
    pid: int,
    payload: LabelCreate,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    if await project_crud.get(session, pid) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return await label_crud.create(
        session, project_id=pid, name=payload.name, color=payload.color
    )
