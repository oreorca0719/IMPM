"""초기 데이터 시드 — 4계정 + STRIPE 관리 프로젝트.

실행: (backend 디렉터리에서)
    python -m scripts.seed

멱등: 이미 존재하는 이메일/프로젝트키는 건너뜀.
초기 비밀번호는 환경변수 SEED_PASSWORD 로 override (기본값은 개발용).
⚠️ 운영 배포 시 초기 비밀번호 안전 전달 방식은 PM 확정 필요(문서 14장-6).
"""
from __future__ import annotations

import asyncio
import os

from app.core.db import async_session_maker, init_db
from app.core.security import hash_password
from app.crud import user as user_crud
from app.models import Project, User
from sqlmodel import select

SEED_PASSWORD = os.getenv("SEED_PASSWORD", "impm-initial-pw!")

# 문서 1.4 사용자표 기준 (이메일은 임시 — 실제 값은 배포 시 조정)
SEED_USERS = [
    {"email": "kbj@impm.team", "name": "김범준", "role": "admin"},   # PM/기술총괄
    {"email": "mjs@impm.team", "name": "문준석", "role": "member"},  # 기획·의사결정
    {"email": "cjh@impm.team", "name": "최재헌", "role": "member"},  # 문서·QA·테스트
    {"email": "reserve@impm.team", "name": "예비멤버", "role": "member"},
    # Claude Code 전용 봇 계정 — 활동로그에서 'claude-bot' 으로 사람과 구분됨.
    # 비밀번호는 BOT_PASSWORD env(없으면 SEED_PASSWORD)로 지정하며 MCP 서버와 동일해야 함.
    {"email": "bot@impm.team", "name": "claude-bot", "role": "bot"},
]

BOT_PASSWORD = os.getenv("BOT_PASSWORD", SEED_PASSWORD)

SEED_PROJECT = {
    "key": "STR",
    "name": "STRIPE",
    "description": "읽기 능력 진단·처방 플랫폼(구 RISA) 개발 프로젝트",
}


async def run() -> None:
    await init_db()
    async with async_session_maker() as session:
        # 사용자
        for u in SEED_USERS:
            existing = await user_crud.get_by_email(session, u["email"])
            if existing:
                print(f"  = 사용자 존재: {u['email']}")
                continue
            pw = BOT_PASSWORD if u["role"] == "bot" else SEED_PASSWORD
            session.add(
                User(
                    email=u["email"],
                    name=u["name"],
                    role=u["role"],
                    password_hash=hash_password(pw),
                )
            )
            print(f"  + 사용자 생성: {u['name']} <{u['email']}>")

        # 프로젝트
        result = await session.exec(
            select(Project).where(Project.key == SEED_PROJECT["key"])
        )
        if result.first():
            print(f"  = 프로젝트 존재: {SEED_PROJECT['key']}")
        else:
            session.add(Project(**SEED_PROJECT))
            print(f"  + 프로젝트 생성: {SEED_PROJECT['key']} ({SEED_PROJECT['name']})")

        await session.commit()

    print(f"\n시드 완료. 초기 비밀번호: {SEED_PASSWORD!r} (배포 후 변경 안내 필요)")


if __name__ == "__main__":
    asyncio.run(run())
