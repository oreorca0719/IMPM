#!/usr/bin/env bash
# IMPM 재배포 — 소스 zip 업로드 → CodeBuild 이미지 빌드 → App Runner 재배포.
# 사용: 프로젝트 루트에서  bash deploy/apprunner/redeploy.sh
set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
ACCT="${AWS_ACCOUNT_ID:-333347414948}"
SRC_BUCKET="impm-src-$ACCT"
PROJECT="impm-build"
SERVICE_ARN="arn:aws:apprunner:$REGION:$ACCT:service/impm/81282104b9f2464ba6de08b43d4581e2"

# aws 실행 경로(PATH에 없으면 Windows 기본 경로 사용)
AWS_BIN="$(command -v aws || echo '/c/Program Files/Amazon/AWSCLIV2/aws.exe')"
aws() { "$AWS_BIN" "$@"; }

echo "1) 소스 아카이브 업로드"
git archive --format=zip -o /tmp/impm-source.zip HEAD
aws s3 cp /tmp/impm-source.zip "s3://$SRC_BUCKET/source.zip" --region "$REGION"

echo "2) CodeBuild 빌드 시작"
BUILD_ID=$(aws codebuild start-build --project-name "$PROJECT" --region "$REGION" --query 'build.id' --output text)
echo "   build: $BUILD_ID"
while true; do
  ST=$(aws codebuild batch-get-builds --ids "$BUILD_ID" --region "$REGION" --query 'builds[0].buildStatus' --output text)
  echo "   status: $ST"
  [ "$ST" = "IN_PROGRESS" ] || break
  sleep 15
done
[ "$ST" = "SUCCEEDED" ] || { echo "빌드 실패: $ST"; exit 1; }

echo "3) App Runner 재배포"
aws apprunner start-deployment --service-arn "$SERVICE_ARN" --region "$REGION" >/dev/null
echo "   완료 요청됨. 진행 상황: aws apprunner describe-service --service-arn $SERVICE_ARN"
