"""IMPM REST API 클라이언트 — 봇 계정 자동 로그인 + 401 시 재로그인.

환경변수:
  IMPM_BASE_URL   : IMPM 서버 루트 (기본 http://localhost:8000). '/api' 는 자동 부착.
  IMPM_BOT_EMAIL  : 봇 계정 이메일 (기본 bot@impm.team)
  IMPM_BOT_PASSWORD : 봇 계정 비밀번호 (필수 — 시드의 BOT_PASSWORD 와 일치해야 함)
"""
from __future__ import annotations

import os

import httpx

from impm_mcp.context import actor_email


class ImpmError(Exception):
    """IMPM API 오류 — 메시지에 상태코드/detail 포함."""


class ImpmClient:
    def __init__(self) -> None:
        base = os.getenv("IMPM_BASE_URL", "http://localhost:8000").rstrip("/")
        self.base_url = f"{base}/api"
        self.email = os.getenv("IMPM_BOT_EMAIL", "bot@impm.team")
        self.password = os.getenv("IMPM_BOT_PASSWORD", "")
        self._token: str | None = None
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=15.0)

    async def _login(self) -> None:
        if not self.password:
            raise ImpmError(
                "IMPM_BOT_PASSWORD 가 설정되지 않았습니다. MCP 서버 환경변수를 확인하세요."
            )
        resp = await self._http.post(
            "/auth/login", json={"email": self.email, "password": self.password}
        )
        if resp.status_code != 200:
            raise ImpmError(
                f"봇 로그인 실패({resp.status_code}): {_detail(resp)}. "
                "IMPM 서버 기동 여부와 봇 계정/비밀번호를 확인하세요."
            )
        self._token = resp.json()["access_token"]

    def _headers(self) -> dict:
        h = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        # 현재 요청을 보낸 팀원으로 대행(봇 계정일 때 백엔드가 신뢰)
        who = actor_email.get()
        if who:
            h["X-Act-As"] = who
        return h

    async def request(self, method: str, path: str, **kwargs):
        if self._token is None:
            await self._login()
        resp = await self._http.request(method, path, headers=self._headers(), **kwargs)
        if resp.status_code == 401:
            # 토큰 만료 → 1회 재로그인 후 재시도
            await self._login()
            resp = await self._http.request(
                method, path, headers=self._headers(), **kwargs
            )
        if resp.status_code >= 400:
            raise ImpmError(f"{method} {path} 실패({resp.status_code}): {_detail(resp)}")
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    async def get(self, path, **kw):
        return await self.request("GET", path, **kw)

    async def post(self, path, **kw):
        return await self.request("POST", path, **kw)

    async def patch(self, path, **kw):
        return await self.request("PATCH", path, **kw)

    async def delete(self, path, **kw):
        return await self.request("DELETE", path, **kw)

    async def aclose(self) -> None:
        await self._http.aclose()


def _detail(resp: httpx.Response) -> str:
    try:
        return str(resp.json().get("detail", resp.text))
    except Exception:
        return resp.text
