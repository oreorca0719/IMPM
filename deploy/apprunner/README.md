# IMPM — AWS App Runner 배포

STRIPE 프로젝트 관리 사이트(IMPM)를 AWS App Runner에 단일 컨테이너로 배포합니다.
로컬 Docker 없이 **CodeBuild**로 이미지를 빌드하고, **litestream**으로 SQLite를 S3에 실시간 복제해 영속화합니다.

## 아키텍처

```
CodeBuild(이미지 빌드) → ECR → App Runner (FastAPI + Vue SPA, 1 인스턴스)
                                      │
                                      └─ litestream ⇄ S3 (SQLite 실시간 복제/복원)
```

- App Runner 컨테이너는 디스크가 비영속 → 부팅 시 S3에서 DB 복원, 종료 전까지 S3로 복제.
- 반드시 **1 인스턴스**(오토스케일링 min=max=1)로 운영 — SQLite 단일 라이터 제약.

## 생성된 리소스 (리전 ap-northeast-1)

| 종류 | 이름/식별자 |
|---|---|
| ECR 레포 | `impm` |
| S3 (DB 복제) | `impm-db-333347414948` |
| S3 (빌드 소스) | `impm-src-333347414948` |
| CodeBuild 프로젝트 | `impm-build` |
| IAM 역할 | `impm-codebuild-role`, `impm-apprunner-ecr`, `impm-apprunner-instance` |
| 오토스케일링 | `impm-single` (min=max=1) |
| App Runner 서비스 | `impm` |

**서비스 URL**: https://a4xrpcaxpu.ap-northeast-1.awsapprunner.com

## 재배포

코드 변경 후:

```bash
# 프로젝트 루트에서
bash deploy/apprunner/redeploy.sh
```

수동으로 하려면:
```bash
git archive --format=zip -o /tmp/source.zip HEAD
aws s3 cp /tmp/source.zip s3://impm-src-333347414948/source.zip --region ap-northeast-1
aws codebuild start-build --project-name impm-build --region ap-northeast-1
# 빌드 완료(SUCCEEDED) 후 App Runner 재배포(:latest pull)
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:ap-northeast-1:333347414948:service/impm/81282104b9f2464ba6de08b43d4581e2 \
  --region ap-northeast-1
```

## 환경변수 (App Runner 서비스에 설정됨)

`DATABASE_URL`(컨테이너 내 SQLite 절대경로), `JWT_SECRET`, `JWT_EXPIRE_HOURS`,
`CORS_ORIGINS`, `LITESTREAM_BUCKET`, `AWS_REGION`, `BOT_PASSWORD`, `SEED_PASSWORD`.
비밀 값 변경: `aws apprunner update-service ...` 로 `RuntimeEnvironmentVariables` 갱신.

## 비용 (대략)

- **App Runner**: 1 인스턴스(1 vCPU/2GB) 상시 → 월 $5~수십 달러대(활성 사용량에 따라).
- **RDS 미사용** — SQLite+S3라 DB 비용 거의 0(S3 저장·요청 몇 센트).
- **CodeBuild**: 빌드 시에만 과금(분당, 소액). **ECR/S3**: 저장 소액.

## 백업/복구

litestream이 S3(`impm-db-.../impm-db/`)에 스냅샷+WAL을 지속 저장.
장애 시 새 컨테이너가 부팅하며 자동 복원됨. 수동 복원:
```bash
litestream restore -o restored.db -config deploy/apprunner/litestream.yml /app/data/impm.db
```

## 주의

- App Runner는 **절대 2인스턴스 이상으로 스케일하면 안 됨**(SQLite 손상). 오토스케일링 `impm-single`로 고정돼 있음.
- 초기 계정 비밀번호(사람용 `SEED_PASSWORD`)는 배포 후 각자 변경 안내 필요(문서 14장-6, 변경 API는 확장 시).
