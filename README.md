# IMPM

**STRIPE 개발 프로젝트를 관리하기 위한 경량 프로젝트 관리 도구** (Jira 대체)

> **용어 정리**
> - **STRIPE** — 우리가 개발 중인 실제 제품/프로젝트 (읽기 능력 진단·처방 플랫폼, 구 RISA)
> - **IMPM** — *이 저장소.* STRIPE 개발을 관리하기 위한 이슈/에픽/칸반/대시보드 웹앱

경기청년 갭이어 4인 팀이 정지된 Jira 대신 사용하기 위한, 월 운영비 0원에 수렴하는 자체 호스팅 플랫폼입니다.

---

## 기능 (1차 MVP)

- 이메일/비밀번호 인증 (JWT)
- 프로젝트 · 에픽 · 이슈 CRUD (담당자·마감일·우선순위·라벨·상태)
- 칸반 보드 (드래그&드롭 상태 전환 + 컬럼 내 정렬)
- 이슈별 댓글 스레드
- 활동 로그 (생성·상태·담당자·마감일·우선순위 변경 자동 기록)
- 진행률 대시보드 (에픽별 진행률·상태별 이슈 수·담당자별 할당·마감 임박)

## 기술 스택

| 영역 | 스택 |
|---|---|
| 백엔드 | Python 3.12 · FastAPI · SQLModel · Alembic · aiosqlite |
| 인증 | python-jose(JWT) + passlib[bcrypt] |
| 프론트 | Vue 3(Composition API) · Vite · Pinia · Vue Router · Tailwind · Chart.js · vuedraggable |
| DB | 로컬: SQLite(WAL) · 배포: **RDS PostgreSQL** (SQLModel/SQLAlchemy로 양쪽 지원) |
| 인프라 | AWS App Runner · CodeBuild(이미지 빌드) · ECR · RDS PostgreSQL · VPC 커넥터 |

## 디렉터리

```
IMPM/
├── backend/          # FastAPI (routers→services→crud→models/schemas, core)
│   ├── app/
│   ├── alembic/
│   ├── scripts/seed.py
│   └── tests/
├── frontend/         # Vue 3 + Vite
├── mcp/              # Claude Code 연동 MCP 서버 (IMPM API → 도구 21종)
├── deploy/           # docker-compose, nginx, backup.sh
├── .env.example
├── .mcp.json.example # Claude Code MCP 설정 예시
└── README.md
```

## Claude Code 연동 (MCP)

Claude Code가 IMPM을 통해 STRIPE 프로젝트를 직접 관리할 수 있도록 **MCP 서버**를 제공합니다.
전용 봇 계정(`bot@impm.team`)으로 동작하며, 봇의 변경은 활동 로그에 `claude-bot`으로 남아
사람과 구분됩니다. 이슈/에픽 생성·이동·수정·삭제, 댓글, 라벨, 대시보드 조회 등 **21개 도구**를 노출합니다.

**MCP 서버도 App Runner에 호스팅**돼 있어, 팀원은 설치 없이 URL+토큰으로 각자 연결합니다.

```bash
claude mcp add --transport http impm \
  https://2gtp4nrtmn.ap-northeast-1.awsapprunner.com/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```
그 후 Claude에서 "STRIPE 진행 중 이슈 알려줘", "STR-5 완료로 옮겨줘" 처럼 자연어로 관리합니다.
호스팅/재배포/토큰 회전: [deploy/apprunner-mcp/README.md](deploy/apprunner-mcp/README.md) · 로컬 stdio 실행: [mcp/README.md](mcp/README.md).

## 로컬 개발

### 백엔드
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp ../.env.example ../.env      # 값 수정(JWT_SECRET 등)
uvicorn app.main:app --reload   # http://localhost:8000/docs
pytest                          # 테스트
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173  (/api → :8000 프록시)
```

### Docker (통합)
```bash
cp .env.example .env
docker compose -f deploy/docker-compose.yml up --build   # http://localhost
```

## 구현 단계 (Phase)

| Phase | 내용 | 상태 |
|---|---|---|
| P0 | 모노레포 스캐폴드 · Docker 골격 | ✅ |
| P1 | DB 모델 · WAL · JWT 로그인 · seed | ✅ |
| P2 | 프로젝트·에픽·이슈 CRUD · 이슈키 채번 · 라벨 | ✅ |
| P3 | 댓글 · 활동로그 자동 기록 | ✅ |
| P4 | 프론트 기반(로그인·AppShell·axios) | ✅ |
| P5 | 칸반 보드 · DnD · 낙관적 업데이트 | ✅ |
| P6 | 이슈 상세 Drawer · 댓글/활동 탭 | ✅ |
| P7 | 에픽 뷰 · 대시보드 시각화 | ✅ |
| P8 | **App Runner 배포** · CodeBuild · **RDS PostgreSQL** | ✅ [배포 문서](deploy/apprunner/README.md) |

**라이브**: https://a4xrpcaxpu.ap-northeast-1.awsapprunner.com (App Runner, ap-northeast-1)
재배포: `bash deploy/apprunner/redeploy.sh`

## 라이선스 / 내부용

경기청년 갭이어 팀 내부 프로젝트 관리용.
