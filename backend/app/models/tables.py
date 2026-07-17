"""SQLModel 테이블 정의 (6장 ERD 기준)."""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    # naive UTC — Postgres(TIMESTAMP WITHOUT TIME ZONE)와 SQLite 양쪽 호환.
    # 모든 시각은 UTC 기준(naive)으로 저장한다.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    name: str
    role: str = Field(default="member")  # member/admin (1차는 표시용)
    created_at: datetime = Field(default_factory=now_utc)


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)  # 이슈키 접두어 (예: STR)
    name: str
    description: str | None = None
    issue_seq: int = Field(default=0)  # 이슈키 채번 카운터
    created_at: datetime = Field(default_factory=now_utc)


class Epic(SQLModel, table=True):
    __tablename__ = "epics"

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    key: str  # 예: STR-2 (에픽도 키 부여)
    title: str
    description: str | None = None
    status: str = Field(default="TODO")  # IssueStatus 문자열
    owner_id: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Issue(SQLModel, table=True):
    __tablename__ = "issues"

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    epic_id: int | None = Field(default=None, foreign_key="epics.id", index=True)
    key: str = Field(index=True, unique=True)  # project.key + seq
    title: str
    description: str | None = None
    status: str = Field(default="TODO", index=True)
    priority: str = Field(default="MEDIUM")
    assignee_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    reporter_id: int = Field(foreign_key="users.id")  # 생성자
    due_date: date | None = Field(default=None)
    board_order: float = Field(default=0.0)  # 칸반 컬럼 내 정렬(소수 간격)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Label(SQLModel, table=True):
    __tablename__ = "labels"

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    name: str
    color: str = Field(default="#6B7280")  # HEX


class IssueLabel(SQLModel, table=True):
    __tablename__ = "issue_labels"

    issue_id: int = Field(foreign_key="issues.id", primary_key=True)
    label_id: int = Field(foreign_key="labels.id", primary_key=True)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int | None = Field(default=None, primary_key=True)
    issue_id: int = Field(foreign_key="issues.id", index=True)
    author_id: int = Field(foreign_key="users.id")
    body: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_logs"

    id: int | None = Field(default=None, primary_key=True)
    issue_id: int = Field(foreign_key="issues.id", index=True)
    actor_id: int = Field(foreign_key="users.id")
    action: str  # ActivityAction 문자열
    field: str | None = Field(default=None)
    old_value: str | None = Field(default=None)
    new_value: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=now_utc)
