#!/bin/sh
# App Runner 컨테이너 시작:
#  1) S3 리플리카가 있으면 SQLite 복원(재배포/재시작 후 데이터 유지)
#  2) 시드(멱등) — 최초엔 계정/프로젝트 생성, 이후엔 없는 것만 보충
#  3) litestream 복제와 함께 uvicorn 실행(앱 종료 시 litestream 도 종료)
set -e

DB_PATH="/app/data/impm.db"

echo "[entrypoint] restoring DB from S3 if replica exists..."
litestream restore -if-replica-exists -config /etc/litestream.yml "$DB_PATH" || true

echo "[entrypoint] seeding (idempotent)..."
python -m scripts.seed || echo "[entrypoint] seed skipped/failed (계속 진행)"

echo "[entrypoint] starting litestream + uvicorn..."
exec litestream replicate -config /etc/litestream.yml \
  -exec "uvicorn app.main:app --host 0.0.0.0 --port 8000"
