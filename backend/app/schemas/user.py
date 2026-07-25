"""사용자 DTO."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    role: str
    must_change_password: bool = False
    created_at: datetime


class ProfileUpdate(BaseModel):
    """아이디(이메일)·이름 변경. 이메일 변경 시 현재 비밀번호 확인 필요."""

    name: str | None = None
    email: EmailStr | None = None
    current_password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class McpTokenRead(BaseModel):
    """본인의 Claude(MCP) 연동 토큰과 연결 안내."""

    token: str
    mcp_url: str  # 기본 엔드포인트(헤더 인증용)
    chat_url: str  # 토큰이 포함된 URL(데스크톱 채팅 앱 커스텀 커넥터용)
    connect_command: str  # Claude Code CLI 명령어


class McpResolveRequest(BaseModel):
    token: str


class McpResolveResult(BaseModel):
    id: int
    email: EmailStr
    name: str
