from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.ml.model import AntifrodModel
from app.core.redis import get_redis
import time
import json

app = FastAPI(
    title="HFBS — Antifrod Service",
    description="ML сервис для обнаружения ботов. RandomForest + GradientBoosting ансамбль.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = AntifrodModel()

# Время открытия продаж (устанавливается через API)
_sale_open_times: dict[int, float] = {}


# ─── Schemas ───────────────────────────────────────────────

class CheckRequest(BaseModel):
    ip: str
    user_agent: str
    seat_id: int
    event_id: int
    seat_price: Optional[float] = 5000.0
    is_front_row: Optional[bool] = False


class CheckResponse(BaseModel):
    is_bot: bool
    confidence: float
    verdict: str        # blocked | suspicious | allowed
    reason: str
    features: dict


class RetrainRequest(BaseModel):
    samples: list       # список [features_dict, label] пар
    description: str = ""


class FeedbackRequest(BaseModel):
    ip: str
    actual_label: int   # 0=человек, 1=бот
    features: dict


# ─── Endpoints ─────────────────────────────────────────────

@app.post("/api/antifrod/check", response_model=CheckResponse)
async def check(req: CheckRequest):
    """
    Основной эндпоинт — проверка запроса на бота.
    Вызывается FastAPI сервисом перед каждым бронированием.
    """
    redis = await get_redis()
    now = time.time()

    # Считаем запросы с IP за минуту
    ip_key = f"af:ip:{req.ip}"
    requests_count = int(await redis.incr(ip_key) or 1)
    await redis.expire(ip_key, 60)

    # Попытки на это место
    seat_key = f"af:seat:{req.event_id}:{req.seat_id}"
    seat_attempts = int(await redis.incr(seat_key) or 1)
    await redis.expire(seat_key, 300)

    # Уникальные места которые пробовал этот IP
    unique_key = f"af:unique:{req.ip}:{req.event_id}"
    await redis.sadd(unique_key, req.seat_id)
    await redis.expire(unique_key, 300)
    unique_seats = int(await redis.scard(unique_key) or 1)

    # Начало сессии
    session_key = f"af:session:{req.ip}"
    session_start_raw = await redis.get(session_key)
    if session_start_raw is None:
        await redis.set(session_key, str(now), ex=3600)
        session_start = now
    else:
        session_start = float(session_start_raw)

    # Front row счётчик
    if req.is_front_row:
        front_key = f"af:front:{req.ip}"
        front_count = int(await redis.incr(front_key) or 1)
        await redis.expire(front_key, 300)
    else:
        front_key = f"af:front:{req.ip}"
        front_count = int(await redis.get(front_key) or 0)

    # Время с открытия продаж
    sale_open = _sale_open_times.get(req.event_id, now - 3600)

    # Формируем фичи
    features = AntifrodModel.extract_features(
        ip=req.ip,
        user_agent=req.user_agent,
        requests_count=requests_count,
        seat_attempts=seat_attempts,
        unique_seats=unique_seats,
        session_start=session_start,
        sale_open_time=sale_open,
        avg_price=req.seat_price or 5000.0,
        front_row_count=front_count,
        total_attempts=seat_attempts,
    )

    # Предсказание
    is_bot, confidence, verdict = model.predict(features)

    # Логируем решение
    log_entry = {
        "ip": req.ip,
        "event_id": req.event_id,
        "seat_id": req.seat_id,
        "is_bot": is_bot,
        "confidence": confidence,
        "verdict": verdict,
        "ts": now,
    }
    await redis.lpush("af:log", json.dumps(log_entry))
    await redis.ltrim("af:log", 0, 999)  # храним последние 1000

    # Счётчики для статистики
    if is_bot:
        await redis.incr("af:blocked_total")
    else:
        await redis.incr("af:allowed_total")

    # Причина блокировки
    reason = _build_reason(
        verdict, requests_count, seat_attempts,
        unique_seats, req.user_agent, req.ip, confidence
    )

    return CheckResponse(
        is_bot=is_bot,
        confidence=confidence,
        verdict=verdict,
        reason=reason,
        features=features,
    )


@app.get("/api/antifrod/stats")
async def stats():
    """Статистика для Dashboard."""
    redis = await get_redis()
    blocked = int(await redis.get("af:blocked_total") or 0)
    allowed = int(await redis.get("af:allowed_total") or 0)
    total = blocked + allowed
    return {
        "blocked_total": blocked,
        "allowed_total": allowed,
        "total_requests": total,
        "block_rate": round(blocked / max(total, 1) * 100, 2),
        "model_metrics": model.metrics,
    }


@app.get("/api/antifrod/logs")
async def logs(limit: int = 50):
    """Последние N решений — для live dashboard."""
    redis = await get_redis()
    raw = await redis.lrange("af:log", 0, limit - 1)
    return {"logs": [json.loads(r) for r in raw]}


@app.get("/api/antifrod/ip/{ip}")
async def ip_info(ip: str):
    """Детальная информация по конкретному IP."""
    redis = await get_redis()
    requests = int(await redis.get(f"af:ip:{ip}") or 0)
    session_start = await redis.get(f"af:session:{ip}")
    front_count = int(await redis.get(f"af:front:{ip}") or 0)
    return {
        "ip": ip,
        "requests_per_minute": requests,
        "session_start": session_start,
        "front_row_attempts": front_count,
    }


@app.post("/api/antifrod/sale-open/{event_id}")
async def set_sale_open(event_id: int):
    """
    Устанавливает время открытия продаж для события.
    Вызывать когда открываете продажу билетов.
    """
    _sale_open_times[event_id] = time.time()
    return {"event_id": event_id, "sale_open_time": _sale_open_times[event_id]}


@app.post("/api/antifrod/feedback")
async def feedback(req: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Обратная связь — помечаем решение правильным/неправильным.
    Используется для накопления обучающих данных.
    """
    redis = await get_redis()
    entry = json.dumps({
        "features": req.features,
        "label": req.actual_label,
        "ip": req.ip,
        "ts": time.time(),
    })
    await redis.lpush("af:feedback", entry)
    await redis.ltrim("af:feedback", 0, 4999)
    return {"status": "saved", "message": "Спасибо! Данные будут использованы при следующем обучении."}


@app.post("/api/antifrod/retrain")
async def retrain(req: RetrainRequest, background_tasks: BackgroundTasks):
    """
    Переобучение модели на новых данных.
    Запускается в фоне чтобы не блокировать API.
    """
    if len(req.samples) < 10:
        raise HTTPException(
            status_code=400,
            detail="Нужно минимум 10 размеченных примеров для переобучения"
        )

    def _do_retrain():
        new_X = [list(s["features"].values()) for s in req.samples]
        new_y = [s["label"] for s in req.samples]
        metrics = model.retrain(new_X, new_y)
        print(f"Модель переобучена. F1={metrics.get('f1')} ROC-AUC={metrics.get('roc_auc')}")

    background_tasks.add_task(_do_retrain)
    return {"status": "started", "samples": len(req.samples), "description": req.description}


@app.get("/api/antifrod/model-info")
async def model_info():
    """Информация о текущей модели — метрики, фичи, дата обучения."""
    return {
        "model_type": "RandomForest + GradientBoosting (ensemble)",
        "features": AntifrodModel.FEATURE_NAMES,
        "bot_threshold": AntifrodModel.BOT_THRESHOLD,
        "suspicious_threshold": AntifrodModel.SUSPICIOUS_THRESHOLD,
        "metrics": model.metrics,
    }


@app.get("/health")
async def health():
    redis = await get_redis()
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {
        "status": "ok",
        "service": "antifrod",
        "redis": "ok" if redis_ok else "error",
        "model_loaded": model.rf is not None,
    }


# ─── Helpers ───────────────────────────────────────────────

def _build_reason(
    verdict: str,
    requests: int,
    seat_attempts: int,
    unique_seats: int,
    ua: str,
    ip: str,
    confidence: float,
) -> str:
    if verdict == "allowed":
        return "OK"
    reasons = []
    if requests > 30:
        reasons.append(f"высокая частота запросов ({requests}/мин)")
    if seat_attempts > 8:
        reasons.append(f"много попыток на одно место ({seat_attempts})")
    if unique_seats > 10:
        reasons.append(f"перебор мест ({unique_seats} разных)")
    if any(sig in ua.lower() for sig in ["bot", "curl", "python", "scrapy"]):
        reasons.append("подозрительный User-Agent")
    if any(ip.startswith(p) for p in ["185.220.", "185.100.", "162.247."]):
        reasons.append("подозрительный IP диапазон")
    if not reasons:
        reasons.append(f"ML модель: уверенность {confidence:.0%}")
    return "; ".join(reasons)

