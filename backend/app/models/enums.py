"""상태·우선순위·활동 enum.

DB에는 문자열로 저장(확장성 확보 — BACKLOG/IN_REVIEW 등을 마이그레이션 없이 추가 가능).
API 검증은 이 Enum으로 수행하고, 칸반 컬럼 구성은 프론트 상수(BOARD_COLUMNS)로 분리한다.
"""
from __future__ import annotations

from enum import Enum


class IssueStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    # 확장 여지: BACKLOG = "BACKLOG", IN_REVIEW = "IN_REVIEW"


class EpicStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ActivityAction(str, Enum):
    created = "created"
    status_changed = "status_changed"
    assignee_changed = "assignee_changed"
    due_changed = "due_changed"
    priority_changed = "priority_changed"
    epic_changed = "epic_changed"
    reporter_changed = "reporter_changed"  # 등록자(작성자) 정정
