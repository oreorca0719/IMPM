"""이슈 DTO."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueStatus, Priority
from app.schemas.label import LabelRead


class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    epic_id: int | None = None
    status: IssueStatus = IssueStatus.TODO
    priority: Priority = Priority.MEDIUM
    assignee_id: int | None = None
    due_date: date | None = None


class IssueUpdate(BaseModel):
    """부분 수정 — 전송된 필드만 반영(model_dump(exclude_unset=True))."""

    title: str | None = None
    description: str | None = None
    epic_id: int | None = None
    status: IssueStatus | None = None
    priority: Priority | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    # 등록자(작성자) 정정용 — 잘못된 계정으로 기록된 경우 바로잡을 때 사용
    reporter_id: int | None = None


class IssueMove(BaseModel):
    status: IssueStatus
    board_order: float


class IssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    epic_id: int | None
    key: str
    title: str
    description: str | None
    status: str
    priority: str
    assignee_id: int | None
    reporter_id: int
    due_date: date | None
    board_order: float
    created_at: datetime
    updated_at: datetime


class IssueDetail(IssueRead):
    labels: list[LabelRead] = []
    comment_count: int = 0
