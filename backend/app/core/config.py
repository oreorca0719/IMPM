"""애플리케이션 설정 — 환경변수 기반(코드에 비밀 하드코딩 금지)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 앱 메타
    app_name: str = "IMPM"
    app_desc: str = "STRIPE 개발 프로젝트 관리 도구"

    # DB
    database_url: str = "sqlite+aiosqlite:///./data/impm.db"

    # 인증
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 12

    # CORS — 콤마 구분 문자열을 리스트로 파싱
    cors_origins: str = "http://localhost:5173,http://localhost"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
