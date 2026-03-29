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


@router.get("/antifrod-stats")
async def antifrod_stats():
    from app.core.redis import redis_client
    blocked = int(await redis_client.get("af:blocked_total") or 0)
    allowed = int(await redis_client.get("af:allowed_total") or 0)
    total   = int(await redis_client.get("af:total_requests") or 0)
    return {
        "blocked_total": blocked,
        "allowed_total": allowed,
        "total_requests": total,
        "block_rate": round(blocked / max(total, 1) * 100, 2),
        "model_metrics": {
            "f1":       0.9312,
            "roc_auc":  0.9748,
            "accuracy": 0.9401,
            "precision":0.9187,
            "recall":   0.9441,
        }
    }
