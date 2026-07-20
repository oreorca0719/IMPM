"""이슈 라우터 — 목록/생성/상세/수정/삭제/이동/라벨."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.crud import issue as issue_crud
from app.crud import label as label_crud
from app.crud import project as project_crud
from app.models import Comment, Epic, Issue, User
from app.schemas.issue import IssueCreate, IssueDetail, IssueMove, IssueRead, IssueUpdate
from app.schemas.label import LabelAttach, LabelRead
from app.services import issue as issue_service

router = APIRouter(prefix="/api", tags=["issues"])


async def _issue_or_404(session: AsyncSession, issue_id: int) -> Issue:
    issue = await issue_crud.get(session, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다.")
    return issue


async def _build_detail(session: AsyncSession, issue: Issue) -> IssueDetail:
    labels = await label_crud.list_for_issue(session, issue.id)
    count = (
        await session.exec(
            select(func.count()).select_from(Comment).where(Comment.issue_id == issue.id)
        )
    ).one()
    return IssueDetail(
        **IssueRead.model_validate(issue).model_dump(),
        labels=[LabelRead.model_validate(la) for la in labels],
        comment_count=count,
    )


@router.get("/projects/{pid}/issues", response_model=list[IssueRead])
async def list_issues(
    pid: int,
    status_: str | None = Query(default=None, alias="status"),
    assignee_id: int | None = None,
    epic_id: int | None = None,
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    if await project_crud.get(session, pid) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return await issue_crud.list_by_project(
        session, pid, status=status_, assignee_id=assignee_id, epic_id=epic_id, q=q
    )


@router.post(
    "/projects/{pid}/issues",
    response_model=IssueDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(
    pid: int,
    payload: IssueCreate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    project = await project_crud.get(session, pid)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    if payload.epic_id is not None:
        epic = await session.get(Epic, payload.epic_id)
        if epic is None or epic.project_id != pid:
            raise HTTPException(status_code=400, detail="유효하지 않은 에픽입니다.")
    if payload.assignee_id is not None and await session.get(User, payload.assignee_id) is None:
        raise HTTPException(status_code=400, detail="유효하지 않은 담당자입니다.")

    issue = await issue_service.create_issue(
        session, project=project, reporter_id=current.id, data=payload
    )
    return await _build_detail(session, issue)


@router.get("/issues/{issue_id}", response_model=IssueDetail)
async def get_issue(
    issue_id: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    issue = await _issue_or_404(session, issue_id)
    return await _build_detail(session, issue)


@router.patch("/issues/{issue_id}", response_model=IssueDetail)
async def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    issue = await _issue_or_404(session, issue_id)
    changes = payload.model_dump(exclude_unset=True)
    if "epic_id" in changes and changes["epic_id"] is not None:
        epic = await session.get(Epic, changes["epic_id"])
        if epic is None or epic.project_id != issue.project_id:
            raise HTTPException(status_code=400, detail="유효하지 않은 에픽입니다.")
    if changes.get("assignee_id") is not None and await session.get(User, changes["assignee_id"]) is None:
        raise HTTPException(status_code=400, detail="유효하지 않은 담당자입니다.")
    if "reporter_id" in changes:
        if changes["reporter_id"] is None:
            raise HTTPException(status_code=400, detail="등록자는 비울 수 없습니다.")
        if await session.get(User, changes["reporter_id"]) is None:
            raise HTTPException(status_code=400, detail="유효하지 않은 등록자입니다.")

    issue = await issue_service.update_issue(
        session, issue=issue, actor_id=current.id, data=payload
    )
    return await _build_detail(session, issue)


@router.delete("/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    issue_id: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    issue = await _issue_or_404(session, issue_id)
    await issue_service.delete_issue(session, issue=issue)


@router.patch("/issues/{issue_id}/move", response_model=IssueRead)
async def move_issue(
    issue_id: int,
    payload: IssueMove,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    issue = await _issue_or_404(session, issue_id)
    return await issue_service.move_issue(
        session, issue=issue, actor_id=current.id, data=payload
    )


@router.post("/issues/{issue_id}/labels", response_model=IssueDetail)
async def add_label(
    issue_id: int,
    payload: LabelAttach,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    issue = await _issue_or_404(session, issue_id)
    label = await label_crud.get(session, payload.label_id)
    if label is None or label.project_id != issue.project_id:
        raise HTTPException(status_code=400, detail="유효하지 않은 라벨입니다.")
    await label_crud.attach(session, issue_id=issue_id, label_id=payload.label_id)
    return await _build_detail(session, issue)


@router.delete("/issues/{issue_id}/labels/{label_id}", response_model=IssueDetail)
async def remove_label(
    issue_id: int,
    label_id: int,
    session: AsyncSession = Depends(get_session),
    _u: User = Depends(get_current_user),
):
    issue = await _issue_or_404(session, issue_id)
    await label_crud.detach(session, issue_id=issue_id, label_id=label_id)
    return await _build_detail(session, issue)
