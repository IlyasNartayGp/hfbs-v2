from fastapi import APIRouter
from app.core.redis import redis_client

router = APIRouter()


@router.get("/")
async def health():
    redis_ok = await redis_client.ping()
    return {
        "status": "ok",
        "service": "fastapi-booking",
        "redis": "ok" if redis_ok else "error",
    }
