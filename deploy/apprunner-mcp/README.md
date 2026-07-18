# IMPM MCP 서버 — AWS App Runner 호스팅 (팀원별 귀속)

팀원이 설치 없이 **URL + 개인 토큰**으로 연결해 쓰도록 MCP 서버를 App Runner에 호스팅합니다.
전송은 **Streamable HTTP(stateless)**, 인증은 **팀원별 Bearer 토큰**입니다.
각 팀원은 자기 토큰으로 붙고, 그 사람 IMPM 계정으로 **활동로그가 귀속**됩니다(봇 대행).

```
각자의 Claude ─(HTTPS, 개인 토큰)→ impm-mcp (App Runner) ─(봇 + X-Act-As: 이메일)→ IMPM API + RDS
                                       └ 토큰→이메일 매핑(MCP_USER_TOKENS)
```

- 미들웨어가 개인 토큰을 이메일로 매핑 → contextvar → ImpmClient 가 `X-Act-As: <이메일>` 헤더 부착.
- 백엔드 `get_current_user` 는 **봇 계정일 때만** `X-Act-As` 를 신뢰해 그 사용자로 대행(권한상승 방지).
- MCP 엔드포인트: `https://<mcp-url>/mcp` · 헬스체크: `/health`(무인증).

## 리소스 (ap-northeast-1)

| 종류 | 이름 |
|---|---|
| ECR | `impm-mcp` |
| CodeBuild | `impm-mcp-build` |
| App Runner | `impm-mcp` · URL `https://2gtp4nrtmn.ap-northeast-1.awsapprunner.com` |

env: `IMPM_BASE_URL`, `IMPM_BOT_EMAIL`, `IMPM_BOT_PASSWORD`, `MCP_USER_TOKENS`.

`MCP_USER_TOKENS` 는 JSON `{"<token>": "<사용자ID>"}` 형식입니다. **이메일이 아니라 사용자 ID**를 쓰는 이유는,
팀원이 계정 설정에서 아이디(이메일)를 바꿔도 귀속이 깨지지 않게 하기 위함입니다.
(백엔드 `X-Act-As` 는 숫자면 ID, 아니면 이메일로 해석합니다.)

## 팀원 연결 (각자 1회, 개인 토큰 사용)

```bash
claude mcp add --transport http impm \
  https://2gtp4nrtmn.ap-northeast-1.awsapprunner.com/mcp \
  --header "Authorization: Bearer <본인-개인-토큰>"
```
개인 토큰은 관리자(김범준)가 안전하게 전달. 이후 "STRIPE 진행 중 이슈 알려줘" 처럼 자연어로 사용하면,
그 작업이 활동로그에 **본인 이름**으로 남습니다.

## 팀원 토큰 추가/회전

토큰↔이메일 맵은 `MCP_USER_TOKENS` env(JSON)에 있습니다. 새 팀원 추가나 토큰 교체 시 이 값을 갱신:
```bash
# 예: 새 토큰 생성
openssl rand -hex 20
# MCP_USER_TOKENS 를 {"<tok>":"<email>", ...} 로 만들어 update-service 로 반영(아래 배포 참고)
```

## 재배포 (중요: digest 고정)

⚠️ App Runner 는 `:latest` 태그를 안정적으로 다시 pull 하지 않는 경우가 있어(태그 캐싱),
**이미지 digest 를 명시**해 배포해야 새 코드가 확실히 반영됩니다.

```bash
# 1) 빌드
git archive --format=zip -o /tmp/src.zip HEAD
aws s3 cp /tmp/src.zip s3://impm-src-333347414948/source.zip --region ap-northeast-1
aws codebuild start-build --project-name impm-mcp-build --region ap-northeast-1   # SUCCEEDED 대기
# 2) 새 digest 확인
aws ecr describe-images --repository-name impm-mcp --image-ids imageTag=latest \
  --query 'imageDetails[0].imageDigest' --output text --region ap-northeast-1
# 3) update-service 로 ImageIdentifier 를 ...impm-mcp@<digest> 로 지정(+env 유지) 후 배포
```

## 보안 메모

- `/mcp` 는 개인 토큰 필수(무토큰/미등록 토큰 401). `/health` 만 공개.
- 개인 토큰 유출 시 해당 토큰만 `MCP_USER_TOKENS`에서 제거/교체.
- DNS 리바인딩 보호는 프록시 특성상 off; 접근 제어는 토큰이 담당.
