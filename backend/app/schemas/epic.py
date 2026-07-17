"""에픽 DTO."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueStatus


class EpicCreate(BaseModel):
    title: str
    description: str | None = None
    status: IssueStatus = IssueStatus.TODO
    owner_id: int | None = None


class EpicUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None
    owner_id: int | None = None


class EpicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    key: str
    title: str
    description: str | None
    status: str
    owner_id: int | None
    created_at: datetime
    updated_at: datetime


class EpicWithProgress(EpicRead):
    done: int = 0
    total: int = 0
    percent: int = 0
