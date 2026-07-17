# IMPM MCP 서버 (Streamable HTTP) — App Runner 호스팅용 이미지. 컨텍스트는 레포 루트.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY mcp/ ./
RUN pip install --no-cache-dir .

EXPOSE 8000
# /mcp = MCP 엔드포인트, /health = 헬스체크(무인증). 인증은 MCP_AUTH_TOKEN(Bearer).
CMD ["uvicorn", "impm_mcp.server:http_app", "--host", "0.0.0.0", "--port", "8000"]
