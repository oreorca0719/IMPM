"""활동 로그 생성 헬퍼 — 이슈 변경 트랜잭션과 함께 원자적으로 add.

값은 문자열로 저장(assignee/epic은 id, status/priority는 enum 값, due는 ISO).
사람이 읽는 렌더('{actor}이(가) 상태를 A→B로 변경')는 프론트(ActivityFeed)에서 수행.
"""
from __future__ import annotations

from app.models import ActivityAction, ActivityLog

# 추적 필드 → (액션, 로그 field 이름)
TRACKED = {
    "status": (ActivityAction.status_changed, "status"),
    "assignee_id": (ActivityAction.assignee_changed, "assignee"),
    "due_date": (ActivityAction.due_changed, "due_date"),
    "priority": (ActivityAction.priority_changed, "priority"),
    "epic_id": (ActivityAction.epic_changed, "epic"),
}


def _s(v) -> str | None:
    if v is None:
        return None
    return v.value if hasattr(v, "value") else str(v)


def build(
    *, issue_id: int, actor_id: int, action: ActivityAction, field: str | None = None,
    old=None, new=None,
) -> ActivityLog:
    return ActivityLog(
        issue_id=issue_id,
        actor_id=actor_id,
        action=action.value,
        field=field,
        old_value=_s(old),
        new_value=_s(new),
    )
