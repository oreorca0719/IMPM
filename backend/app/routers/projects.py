"""프로젝트 라우터."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import project as project_crud
from app.models import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _get_or_404(session: AsyncSession, pid: int):
    project = await project_crud.get(session, pid)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    return await project_crud.list_all(session)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    if await project_crud.get_by_key(session, payload.key):
        raise HTTPException(status_code=409, detail="이미 존재하는 프로젝트 키입니다.")
    return await project_crud.create(
        session, key=payload.key, name=payload.name, description=payload.description
    )


@router.get("/{pid}", response_model=ProjectRead)
async def get_project(
    pid: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    return await _get_or_404(session, pid)


@router.patch("/{pid}", response_model=ProjectRead)
async def update_project(
    pid: int,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    project = await _get_or_404(session, pid)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project
