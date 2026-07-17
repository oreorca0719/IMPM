"""이슈 라우터 — P2에서 구현."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["issues"])
