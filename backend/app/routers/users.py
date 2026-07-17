"""사용자 라우터 — P1/P2에서 구현."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["users"])
