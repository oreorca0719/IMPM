"""에픽 라우터 — 목록(+진행률)/생성/수정/삭제."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import epic as epic_crud
from app.crud import project as project_crud
from app.models import User
from app.schemas.epic import EpicCreate, EpicRead, EpicUpdate, EpicWithProgress
from app.services import epic as epic_service

router = APIRouter(prefix="/api", tags=["epics"])


@router.get("/projects/{pid}/epics", response_model=list[EpicWithProgress])
async def list_epics(
    pid: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    if await project_crud.get(session, pid) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    epics = await epic_crud.list_by_project(session, pid)
    pmap = await epic_service.progress_map(session, pid)
    out = []
    for e in epics:
        done, total = pmap.get(e.id, (0, 0))
        out.append(
            EpicWithProgress(
                **EpicRead.model_validate(e).model_dump(),
                done=done,
                total=total,
                percent=epic_service.percent(done, total),
            )
        )
    return out


@router.post(
    "/projects/{pid}/epics", response_model=EpicRead, status_code=status.HTTP_201_CREATED
)
async def create_epic(
    pid: int,
    payload: EpicCreate,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    project = await project_crud.get(session, pid)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return await epic_service.create_epic(session, project=project, data=payload)


@router.patch("/epics/{epic_id}", response_model=EpicRead)
async def update_epic(
    epic_id: int,
    payload: EpicUpdate,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    epic = await epic_crud.get(session, epic_id)
    if epic is None:
        raise HTTPException(status_code=404, detail="에픽을 찾을 수 없습니다.")
    return await epic_service.update_epic(session, epic=epic, data=payload)


@router.delete("/epics/{epic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_epic(
    epic_id: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    epic = await epic_crud.get(session, epic_id)
    if epic is None:
        raise HTTPException(status_code=404, detail="에픽을 찾을 수 없습니다.")
    await epic_service.delete_epic(session, epic=epic)
