"""IMPM MCP 서버 — Claude Code 가 STRIPE 프로젝트를 관리하도록 도구를 노출.

프로젝트가 하나면 대부분의 도구에서 project_id 를 생략할 수 있다(자동 해석).
쓰기 도구의 결과는 갱신된 객체를 그대로 반환한다.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from impm_mcp.client import ImpmClient, ImpmError

# 원격 호스팅(App Runner) 시 프록시가 Host 를 바꾸므로 DNS 리바인딩 보호를 끈다.
# 실제 접근 제어는 Bearer 토큰 미들웨어가 담당.
# stateless_http=True: 요청 인라인 처리 → 미들웨어가 설정한 contextvar(actor_email)가
# 도구 실행까지 전파되어 팀원별 대행(X-Act-As)이 동작한다.
mcp = FastMCP(
    "impm",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    ),
)
client = ImpmClient()

RO = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, openWorldHint=True)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)


async def _resolve_project(project_id: int | None) -> int:
    if project_id:
        return project_id
    projects = await client.get("/projects")
    if not projects:
        raise ImpmError("프로젝트가 없습니다. 먼저 프로젝트를 생성하세요.")
    return projects[0]["id"]


def _clean(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


# ─────────────────────────── 조회(read-only) ───────────────────────────


@mcp.tool(annotations=RO)
async def impm_whoami() -> dict:
    """현재 MCP 봇 계정 정보를 반환한다(연결 확인용)."""
    return await client.get("/auth/me")


@mcp.tool(annotations=RO)
async def impm_list_projects() -> list:
    """모든 프로젝트 목록(id, key, name)을 반환한다."""
    return await client.get("/projects")


@mcp.tool(annotations=RO)
async def impm_list_users() -> list:
    """담당자 지정에 쓸 수 있는 사용자 목록(id, name, email)을 반환한다."""
    return await client.get("/users")


@mcp.tool(annotations=RO)
async def impm_list_epics(project_id: int | None = None) -> list:
    """에픽 목록을 진행률 요약(done/total/percent)과 함께 반환한다."""
    pid = await _resolve_project(project_id)
    return await client.get(f"/projects/{pid}/epics")


@mcp.tool(annotations=RO)
async def impm_list_issues(
    project_id: int | None = None,
    status: str | None = None,
    assignee_id: int | None = None,
    epic_id: int | None = None,
    q: str | None = None,
) -> list:
    """이슈 목록을 조회한다.

    status: TODO|IN_PROGRESS|DONE, assignee_id/epic_id: 정수 id, q: 제목 부분검색.
    """
    pid = await _resolve_project(project_id)
    params = _clean(
        {"status": status, "assignee_id": assignee_id, "epic_id": epic_id, "q": q}
    )
    return await client.get(f"/projects/{pid}/issues", params=params)


@mcp.tool(annotations=RO)
async def impm_get_issue(issue_id: int) -> dict:
    """이슈 상세(라벨·댓글 수 포함)를 반환한다."""
    return await client.get(f"/issues/{issue_id}")


@mcp.tool(annotations=RO)
async def impm_list_comments(issue_id: int) -> list:
    """이슈의 댓글 목록을 반환한다."""
    return await client.get(f"/issues/{issue_id}/comments")


@mcp.tool(annotations=RO)
async def impm_get_issue_activity(issue_id: int) -> list:
    """이슈의 활동 로그(시간 역순)를 반환한다."""
    return await client.get(f"/issues/{issue_id}/activity")


@mcp.tool(annotations=RO)
async def impm_list_labels(project_id: int | None = None) -> list:
    """프로젝트의 라벨 목록을 반환한다."""
    pid = await _resolve_project(project_id)
    return await client.get(f"/projects/{pid}/labels")


@mcp.tool(annotations=RO)
async def impm_get_dashboard(project_id: int | None = None) -> dict:
    """진행률 대시보드 집계(상태별 수·에픽 진행률·담당자 부하·마감 임박)를 반환한다."""
    pid = await _resolve_project(project_id)
    return await client.get(f"/projects/{pid}/dashboard")


# ─────────────────────────── 이슈 쓰기 ───────────────────────────


@mcp.tool(annotations=WRITE)
async def impm_create_issue(
    title: str,
    project_id: int | None = None,
    description: str | None = None,
    epic_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    due_date: str | None = None,
) -> dict:
    """이슈를 생성한다. 제목만 필수.

    status: TODO|IN_PROGRESS|DONE(기본 TODO), priority: LOW|MEDIUM|HIGH|URGENT(기본 MEDIUM),
    due_date: 'YYYY-MM-DD'. 키는 자동 채번되며 활동로그(created)가 남는다.
    """
    pid = await _resolve_project(project_id)
    body = _clean(
        {
            "title": title,
            "description": description,
            "epic_id": epic_id,
            "status": status,
            "priority": priority,
            "assignee_id": assignee_id,
            "due_date": due_date,
        }
    )
    return await client.post(f"/projects/{pid}/issues", json=body)


@mcp.tool(annotations=WRITE)
async def impm_update_issue(
    issue_id: int,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    due_date: str | None = None,
    epic_id: int | None = None,
) -> dict:
    """이슈 필드를 수정한다(전달한 값만 반영).

    상태/담당자/마감일/우선순위/에픽 변경 시 활동로그가 자동 기록된다.
    """
    body = _clean(
        {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "assignee_id": assignee_id,
            "due_date": due_date,
            "epic_id": epic_id,
        }
    )
    if not body:
        raise ImpmError("수정할 필드를 최소 1개 전달하세요.")
    return await client.patch(f"/issues/{issue_id}", json=body)


@mcp.tool(annotations=WRITE)
async def impm_move_issue(
    issue_id: int, status: str, board_order: float | None = None
) -> dict:
    """칸반 상태를 이동한다. board_order 를 생략하면 대상 컬럼 맨 끝에 배치한다."""
    if board_order is None:
        issue = await client.get(f"/issues/{issue_id}")
        peers = await client.get(
            f"/projects/{issue['project_id']}/issues", params={"status": status}
        )
        board_order = (max((p["board_order"] for p in peers), default=0.0)) + 1.0
    return await client.patch(
        f"/issues/{issue_id}/move", json={"status": status, "board_order": board_order}
    )


@mcp.tool(annotations=DESTRUCTIVE)
async def impm_delete_issue(issue_id: int) -> dict:
    """이슈를 삭제한다(되돌릴 수 없음). 댓글·활동·라벨 연결도 함께 제거."""
    await client.delete(f"/issues/{issue_id}")
    return {"deleted": issue_id}


# ─────────────────────────── 에픽 쓰기 ───────────────────────────


@mcp.tool(annotations=WRITE)
async def impm_create_epic(
    title: str,
    project_id: int | None = None,
    description: str | None = None,
    owner_id: int | None = None,
    status: str | None = None,
) -> dict:
    """에픽을 생성한다(키 자동 채번, 이슈와 번호 공간 공유)."""
    pid = await _resolve_project(project_id)
    body = _clean(
        {"title": title, "description": description, "owner_id": owner_id, "status": status}
    )
    return await client.post(f"/projects/{pid}/epics", json=body)


@mcp.tool(annotations=WRITE)
async def impm_update_epic(
    epic_id: int,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    owner_id: int | None = None,
) -> dict:
    """에픽을 수정한다(전달한 값만 반영)."""
    body = _clean(
        {"title": title, "description": description, "status": status, "owner_id": owner_id}
    )
    if not body:
        raise ImpmError("수정할 필드를 최소 1개 전달하세요.")
    return await client.patch(f"/epics/{epic_id}", json=body)


@mcp.tool(annotations=DESTRUCTIVE)
async def impm_delete_epic(epic_id: int) -> dict:
    """에픽을 삭제한다. 소속 이슈는 삭제되지 않고 에픽에서 분리된다."""
    await client.delete(f"/epics/{epic_id}")
    return {"deleted": epic_id}


# ─────────────────────────── 댓글 · 라벨 ───────────────────────────


@mcp.tool(annotations=WRITE)
async def impm_add_comment(issue_id: int, body: str) -> dict:
    """이슈에 댓글을 작성한다(작성자는 봇 계정)."""
    return await client.post(f"/issues/{issue_id}/comments", json={"body": body})


@mcp.tool(annotations=WRITE)
async def impm_create_label(
    name: str, project_id: int | None = None, color: str | None = None
) -> dict:
    """프로젝트에 라벨을 생성한다. color 는 HEX(예: '#EF4444')."""
    pid = await _resolve_project(project_id)
    body = _clean({"name": name, "color": color})
    return await client.post(f"/projects/{pid}/labels", json=body)


@mcp.tool(annotations=WRITE)
async def impm_add_label_to_issue(issue_id: int, label_id: int) -> dict:
    """이슈에 라벨을 부착한다."""
    return await client.post(f"/issues/{issue_id}/labels", json={"label_id": label_id})


@mcp.tool(annotations=WRITE)
async def impm_remove_label_from_issue(issue_id: int, label_id: int) -> dict:
    """이슈에서 라벨을 제거한다."""
    return await client.delete(f"/issues/{issue_id}/labels/{label_id}")


# ─────────────────────── HTTP 호스팅 (Streamable HTTP + 토큰 인증) ───────────────────────
# 팀원이 각자 Claude 에서 URL+토큰으로 연결하도록 App Runner 에 호스팅할 때 사용.
# uvicorn 진입점:  uvicorn impm_mcp.server:http_app --host 0.0.0.0 --port 8000
#   MCP 엔드포인트: /mcp  ·  헬스체크: /health(무인증)
import json  # noqa: E402

from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse, Response  # noqa: E402
from starlette.routing import Route  # noqa: E402

from impm_mcp.context import actor_email  # noqa: E402

# 팀원별 토큰 맵: JSON {"<token>": "<email>", ...}. 각 팀원은 자기 토큰으로 붙고,
# 그 사람 IMPM 계정으로 활동로그가 귀속된다(백엔드 X-Act-As 대행).
_raw_user_tokens = os.getenv("MCP_USER_TOKENS", "")
try:
    USER_TOKENS: dict[str, str] = json.loads(_raw_user_tokens) if _raw_user_tokens else {}
except Exception:
    USER_TOKENS = {}

# (선택) 공용 토큰 — 대행 없이 봇(claude-bot) 계정으로 동작
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")


def _resolve_token(token: str) -> tuple[bool, str | None]:
    """(인증성공?, 대행이메일 or None). None = 봇 그대로."""
    if token and token in USER_TOKENS:
        return True, USER_TOKENS[token]
    if MCP_AUTH_TOKEN and token == MCP_AUTH_TOKEN:
        return True, None
    return False, None


async def _health(_request: Request):
    return JSONResponse({"status": "ok", "service": "impm-mcp"})


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """MCP 경로에 Bearer 토큰 요구(팀원별 토큰 또는 공용 토큰). /health 는 예외."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.rstrip("/") == "/health":
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        token = auth[7:] if auth[:7].lower() == "bearer " else ""
        ok, email = _resolve_token(token)
        if not ok:
            return Response("Unauthorized", status_code=401)
        actor_email.set(email)  # 요청 스코프 대행자 설정
        return await call_next(request)


def build_http_app():
    app = mcp.streamable_http_app()  # /mcp 엔드포인트 + 세션 매니저 lifespan 포함
    app.router.routes.append(Route("/health", _health))
    app.add_middleware(BearerAuthMiddleware)
    return app


# uvicorn 이 import 하는 모듈 레벨 ASGI 앱
http_app = build_http_app()


def main() -> None:
    """로컬 stdio 실행(각자 PC에서 Claude Code 가 spawn)."""
    mcp.run()


if __name__ == "__main__":
    main()
