"""인증 라우터 — P1에서 구현."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])
