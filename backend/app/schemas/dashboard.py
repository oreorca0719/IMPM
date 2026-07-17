"""대시보드 집계 DTO."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class EpicProgressItem(BaseModel):
    epic_key: str
    title: str
    done: int
    total: int
    percent: int


class AssigneeLoadItem(BaseModel):
    user: str
    open: int
    done: int


class DueSoonItem(BaseModel):
    id: int
    key: str
    title: str
    due_date: date


class DashboardData(BaseModel):
    status_counts: dict[str, int]
    epic_progress: list[EpicProgressItem]
    assignee_load: list[AssigneeLoadItem]
    due_soon: list[DueSoonItem]
