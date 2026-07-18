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
