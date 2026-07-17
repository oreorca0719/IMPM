"""댓글 · 활동 DTO."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    body: str


class CommentUpdate(BaseModel):
    body: str


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    author_id: int
    body: str
    created_at: datetime
    updated_at: datetime


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    actor_id: int
    action: str
    field: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime
