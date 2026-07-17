"""요청 스코프 컨텍스트 — 현재 요청을 보낸 팀원의 IMPM 이메일.

HTTP 미들웨어가 Bearer 토큰을 이메일로 매핑해 여기에 설정하고(stateless HTTP),
ImpmClient 가 요청마다 이 값을 읽어 X-Act-As 헤더로 붙인다.
"""
from __future__ import annotations

from contextvars import ContextVar

# None 이면 대행 없음(봇 계정 그대로 = claude-bot 귀속)
actor_email: ContextVar[str | None] = ContextVar("actor_email", default=None)
