# IMPM — AWS App Runner 배포

STRIPE 프로젝트 관리 사이트(IMPM)를 AWS App Runner에 단일 컨테이너로 배포합니다.
로컬 Docker 없이 **CodeBuild**로 이미지를 빌드하고, DB는 **RDS PostgreSQL**(VPC 커넥터로 프라이빗 접속)을 사용합니다.

## 아키텍처

```
CodeBuild(이미지 빌드) → ECR → App Runner (FastAPI + Vue SPA)
                                     │  VPC Connector(egress)
                                     ▼
                             RDS PostgreSQL (프라이빗, db.t4g.micro)
```

- App Runner 컨테이너가 부팅 시 `scripts.seed`(init_db=스키마 생성 + 멱등 시드)를 실행한 뒤 uvicorn 기동.
- DB는 관리형 RDS라 영속·자동 백업(보존 7일). App Runner 재배포/재시작과 무관하게 데이터 유지.
- App Runner는 VPC 커넥터를 통해 프라이빗 RDS(5432)에 접속(외부 미노출).

## 생성된 리소스 (리전 ap-northeast-1)

| 종류 | 이름/식별자 |
|---|---|
| ECR 레포 | `impm` |
| RDS PostgreSQL | `impm-pg` (db.t4g.micro, DB명 `impm`, user `impm`) |
| VPC 커넥터 | `impm-conn` (기본 VPC 3개 서브넷) |
| 보안그룹 | `impm-apprunner-conn`(커넥터), `impm-rds`(5432 ← 커넥터 SG만) |
| DB 서브넷 그룹 | `impm-db-subnets` |
| S3 (빌드 소스) | `impm-src-333347414948` |
| CodeBuild 프로젝트 | `impm-build` |
| IAM 역할 | `impm-codebuild-role`, `impm-apprunner-ecr`, `impm-apprunner-instance` |
| 오토스케일링 | `impm-single` (min=max=1) |
| App Runner 서비스 | `impm` |

**서비스 URL**: https://a4xrpcaxpu.ap-northeast-1.awsapprunner.com

> 참고: SQLite/litestream 구성에서 RDS로 이전 완료. 과거 `impm-db-333347414948`(litestream S3) 버킷은
> 더 이상 사용하지 않으며 삭제해도 됩니다. RDS는 관리형 백업을 사용하므로 별도 S3 백업 불필요.

## 재배포

코드 변경 후:
```bash
bash deploy/apprunner/redeploy.sh
```
(소스 zip 업로드 → CodeBuild → App Runner `start-deployment` 으로 :latest 재배포)

## 환경변수 (App Runner 서비스)

`DATABASE_URL`(`postgresql+asyncpg://impm:***@impm-pg...:5432/impm`), `JWT_SECRET`,
`JWT_EXPIRE_HOURS`, `CORS_ORIGINS`, `BOT_PASSWORD`, `SEED_PASSWORD`.
값 변경: `aws apprunner update-service` 로 `RuntimeEnvironmentVariables` 갱신.

## 스케일링

현재 오토스케일링 `impm-single`(min=max=1)로 1인스턴스 고정. RDS를 쓰므로 이제
다중 인스턴스로 확장 가능 — 새 AutoScalingConfiguration(예: min=1,max=3)을 만들어
서비스에 연결하면 됨. (4인 규모에선 1인스턴스로 충분)

## 비용 (대략)

- **App Runner**: 1 인스턴스(1 vCPU/2GB) 상시 → 월 $5~수십 달러대(사용량 의존).
- **RDS db.t4g.micro**: 12개월 무료티어(월 750시간), 이후 대략 월 $12~15 + 스토리지.
- **CodeBuild/ECR/S3(소스)**: 소액.

## 백업/복구

RDS 자동 백업(보존 7일) + 스냅샷. 수동 스냅샷:
```bash
aws rds create-db-snapshot --db-instance-identifier impm-pg --db-snapshot-identifier impm-manual-YYYYMMDD --region ap-northeast-1
```

## 주의

- RDS는 **프라이빗**(publicly-accessible=false) — App Runner VPC 커넥터를 통해서만 접근.
- 비밀번호/DATABASE_URL 등 시크릿은 App Runner env 및 로컬 배포 노트에만 존재(레포 커밋 금지).
- 초기 계정 비밀번호(`SEED_PASSWORD`)는 배포 후 변경 안내 필요(비번 변경 API는 확장 시).
