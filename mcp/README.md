# IMPM MCP 서버

Claude Code(및 기타 MCP 클라이언트)가 **IMPM을 통해 STRIPE 프로젝트를 관리**할 수 있도록,
IMPM REST API를 MCP 도구로 노출합니다. Claude Code가 이슈 생성·이동·조회, 에픽, 댓글,
대시보드 등을 자연어로 다룰 수 있습니다.

## 동작 방식

```
Claude Code  ──(MCP/stdio)──▶  impm-mcp 서버  ──(HTTPS + JWT)──▶  IMPM API
```

- **전용 봇 계정**(`bot@impm.team`, role=`bot`)으로 IMPM에 로그인해 토큰을 얻고, 만료 시 자동 재로그인.
- 봇의 모든 변경은 활동 로그에 `claude-bot`으로 남아 **사람 vs AI 행위가 구분**됩니다.

## 제공 도구 (21종)

| 구분 | 도구 |
|---|---|
| 조회 | `impm_whoami`, `impm_list_projects`, `impm_list_users`, `impm_list_epics`, `impm_list_issues`, `impm_get_issue`, `impm_list_comments`, `impm_get_issue_activity`, `impm_list_labels`, `impm_get_dashboard` |
| 이슈 | `impm_create_issue`, `impm_update_issue`, `impm_move_issue`, `impm_delete_issue` |
| 에픽 | `impm_create_epic`, `impm_update_epic`, `impm_delete_epic` |
| 댓글·라벨 | `impm_add_comment`, `impm_create_label`, `impm_add_label_to_issue`, `impm_remove_label_from_issue` |

> 프로젝트가 하나면 대부분 도구에서 `project_id`를 생략할 수 있습니다(자동 해석).

## 설치

```bash
cd mcp
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -e .
```

## 환경변수

| 변수 | 설명 | 기본값 |
|---|---|---|
| `IMPM_BASE_URL` | IMPM 서버 루트(뒤에 `/api` 자동 부착) | `http://localhost:8000` |
| `IMPM_BOT_EMAIL` | 봇 계정 이메일 | `bot@impm.team` |
| `IMPM_BOT_PASSWORD` | 봇 계정 비밀번호(시드 `BOT_PASSWORD`와 일치) | (필수) |

배포 후에는 `IMPM_BASE_URL`을 실제 도메인/IP로 지정하세요(예: `https://impm.example.com`).

## Claude Code 에 연결

### 방법 A — CLI (권장)
`mcp/.venv`의 python 절대경로로 실행합니다.

```bash
claude mcp add impm \
  -e IMPM_BASE_URL=http://localhost:8000 \
  -e IMPM_BOT_EMAIL=bot@impm.team \
  -e IMPM_BOT_PASSWORD='설정한-봇-비밀번호' \
  -- "C:\Users\User\Desktop\IMPM\mcp\.venv\Scripts\python.exe" -m impm_mcp.server
```

연결 후 `claude mcp list`로 확인하고, Claude Code 세션에서 `/mcp`로 도구를 볼 수 있습니다.

### 방법 B — 프로젝트 공유 설정(`.mcp.json`)
레포 루트의 `.mcp.json.example`을 `.mcp.json`으로 복사하고 `command`의 python 경로를 각자 환경에 맞게 수정하세요.
비밀번호는 `${IMPM_BOT_PASSWORD}` 로 참조하므로, 셸 환경변수 `IMPM_BOT_PASSWORD`를 설정해 두면 커밋에 노출되지 않습니다.

## 사용 예 (Claude Code 대화)

- "STRIPE 프로젝트에서 진행 중인 이슈 알려줘" → `impm_list_issues(status=IN_PROGRESS)`
- "'로그인 버그' 이슈 만들고 김범준한테 배정해줘" → `impm_list_users` → `impm_create_issue`
- "STR-5를 완료로 옮겨줘" → `impm_move_issue(status=DONE)`
- "지금 프로젝트 진행률 요약해줘" → `impm_get_dashboard`

## 로컬 테스트

IMPM 백엔드를 먼저 띄우고(`uvicorn app.main:app --port 8000`), 시드로 봇 계정을 만든 뒤:

```bash
python -c "import asyncio, os; \
os.environ.update(IMPM_BASE_URL='http://127.0.0.1:8000', IMPM_BOT_PASSWORD='impm-initial-pw!'); \
import impm_mcp.server as s; \
print(asyncio.run(s.impm_whoami()))"
```
