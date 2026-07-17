# IMPM App Runner 단일 이미지 — Vue SPA 빌드 + FastAPI (DB는 RDS PostgreSQL)
# CodeBuild 에서 빌드하여 ECR 로 푸시. 컨텍스트는 레포 루트.

# ── Stage 1: 프론트 빌드 ─────────────────────────────
FROM node:20-alpine AS fe
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build          # → /fe/dist

# ── Stage 2: 백엔드 런타임 ───────────────────────────
FROM python:3.12-slim

WORKDIR /app
COPY backend/ ./
RUN pip install --no-cache-dir .

# 빌드된 프론트 정적 파일
COPY --from=fe /fe/dist /app/static

COPY deploy/apprunner/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV FRONTEND_DIST=/app/static \
    PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
