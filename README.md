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
| DB | SQLite (WAL 모드) |
| 인프라 | AWS EC2 t2.micro · Docker Compose · Nginx · Let's Encrypt · S3 백업 |

## 디렉터리

```
IMPM/
├── backend/          # FastAPI (routers→services→crud→models/schemas, core)
│   ├── app/
│   ├── alembic/
│   ├── scripts/seed.py
│   └── tests/
├── frontend/         # Vue 3 + Vite
├── deploy/           # docker-compose, nginx, backup.sh
├── .env.example
└── README.md
```

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
| P8 | EC2 배포 · Nginx · S3 백업 | ⏳ (PM 확인 필요, 14장) |

## 라이선스 / 내부용

경기청년 갭이어 팀 내부 프로젝트 관리용.
