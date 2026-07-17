#!/usr/bin/env bash
# IMPM SQLite 일 1회 백업 → AWS S3 (P8에서 cron 등록)
# crontab 예: 0 3 * * *  /opt/impm/deploy/backup.sh >> /var/log/impm-backup.log 2>&1
set -euo pipefail

DB_PATH="${IMPM_DB_PATH:-/var/lib/docker/volumes/impm_impm-data/_data/impm.db}"
S3_BUCKET="${S3_BUCKET:-impm-backups}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
STAMP="$(date +%Y%m%d-%H%M%S)"
TMP="/tmp/impm-${STAMP}.db"

# WAL 체크포인트 후 일관된 스냅샷 생성(.backup 사용)
sqlite3 "$DB_PATH" ".backup '$TMP'"

aws s3 cp "$TMP" "s3://${S3_BUCKET}/impm-${STAMP}.db" --region "$AWS_REGION"
rm -f "$TMP"
echo "[$(date -Is)] backup uploaded: s3://${S3_BUCKET}/impm-${STAMP}.db"
