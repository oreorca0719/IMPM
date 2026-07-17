# IMPM MCP 서버 — AWS App Runner 호스팅

팀원이 각자 설치 없이 **URL + 토큰**으로 연결해 쓰도록 MCP 서버를 App Runner에 호스팅합니다.
전송은 **Streamable HTTP**, 인증은 **Bearer 토큰**(`MCP_AUTH_TOKEN`)입니다.

```
각자의 Claude ──(HTTPS, Bearer 토큰)──▶ impm-mcp (App Runner) ──(bot 계정)──▶ IMPM API + RDS
```

- MCP 엔드포인트: `https://<mcp-url>/mcp`  ·  헬스체크: `/health`(무인증)
- 서버는 IMPM에 **봇 계정(`bot@impm.team`)** 으로 접속 → 팀원이 시킨 AI 작업은 활동로그에 `claude-bot` 으로 남음(공용 봇).
- 세션이 메모리에 있어 **1 인스턴스 고정**(오토스케일 `impm-single`).

## 리소스 (ap-northeast-1)

| 종류 | 이름 |
|---|---|
| ECR | `impm-mcp` |
| CodeBuild | `impm-mcp-build` (buildspec `deploy/apprunner-mcp/buildspec.yml`) |
| App Runner | `impm-mcp` |
| 서비스 URL | `https://2gtp4nrtmn.ap-northeast-1.awsapprunner.com` |

환경변수: `IMPM_BASE_URL`(배포 IMPM URL), `IMPM_BOT_EMAIL`, `IMPM_BOT_PASSWORD`, `MCP_AUTH_TOKEN`.

## 팀원 연결 방법 (각자 1회)

### Claude Code (데스크톱/CLI) — 권장
```bash
claude mcp add --transport http impm \
  https://2gtp4nrtmn.ap-northeast-1.awsapprunner.com/mcp \
  --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
```
연결 후 세션에서 `/mcp` 로 확인. 이후 "STRIPE 진행 중 이슈 알려줘" 처럼 자연어로 사용.

또는 프로젝트 `.mcp.json`(레포 루트 참고, `type: http`)을 각자 환경에 두는 방법도 있음.

> **토큰은 별도로 공유**합니다(레포에 커밋하지 않음). 분실/유출 시 아래 "토큰 회전" 참고.

### claude.ai (웹)
웹 커넥터는 보통 OAuth를 요구해 현재의 Bearer 토큰 방식과 바로는 호환되지 않습니다.
웹에서 붙여야 하면 OAuth 지원을 추가해야 하니 별도 요청 바랍니다.

## 재배포

```bash
# 소스 업로드 → 이미지 빌드 → 재배포
git archive --format=zip -o /tmp/src.zip HEAD
aws s3 cp /tmp/src.zip s3://impm-src-333347414948/source.zip --region ap-northeast-1
aws codebuild start-build --project-name impm-mcp-build --region ap-northeast-1
# 빌드 SUCCEEDED 후
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:ap-northeast-1:333347414948:service/impm-mcp/291b0d6ca77b47fc8775b7df6edcfc33 \
  --region ap-northeast-1
```

## 토큰 회전 (유출 시)

```bash
NEW=$(openssl rand -hex 24)
aws apprunner update-service --service-arn <impm-mcp ARN> --region ap-northeast-1 \
  --source-configuration '{"ImageRepository":{"ImageConfiguration":{"RuntimeEnvironmentVariables":{"MCP_AUTH_TOKEN":"'$NEW'", ...나머지 env 동일...}}}}'
# 팀원에게 새 토큰 재공유
```

## 보안 메모

- `/mcp` 는 Bearer 토큰 필수(무토큰/오토큰 401). `/health` 만 공개.
- 공용 봇 계정이라 개인별 귀속이 안 됨 — 개인 귀속이 필요하면 OAuth 매핑 필요(후속).
- DNS 리바인딩 보호는 프록시(App Runner) 특성상 비활성; 접근 제어는 토큰이 담당.
