#!/bin/sh
# App Runner 컨테이너 시작 (DB: RDS PostgreSQL):
#  1) 시드(멱등) — init_db 로 스키마 생성 + 없는 계정/프로젝트만 보충
#  2) uvicorn 실행
set -e

echo "[entrypoint] seeding (idempotent, schema 생성 포함)..."
python -m scripts.seed || echo "[entrypoint] seed skipped/failed (계속 진행)"

echo "[entrypoint] starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
