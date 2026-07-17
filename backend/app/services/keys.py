"""이슈/에픽 키 채번 — 프로젝트 카운터를 원자적으로 증가.

에픽과 이슈는 동일한 프로젝트 카운터(issue_seq)를 공유한다
(예: STR-2 에픽, STR-13 이슈 → 같은 번호 공간). UPDATE ... RETURNING 으로
단일 문장 원자 증가하여 동시 생성 시 키 충돌을 방지한다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession


async def next_key(session: AsyncSession, *, project_id: int, project_key: str) -> str:
    result = await session.execute(
        text(
            "UPDATE projects SET issue_seq = issue_seq + 1 "
            "WHERE id = :pid RETURNING issue_seq"
        ),
        {"pid": project_id},
    )
    row = result.first()
    if row is None:
        raise ValueError(f"project {project_id} not found for key numbering")
    seq = row[0]
    return f"{project_key}-{seq}"
