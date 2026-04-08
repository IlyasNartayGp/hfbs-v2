from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from app.core.redis import redis_client
from app.core.database import get_db
from app.schemas.booking import BookingRequest, BookingResponse
import uuid, json, os
from aiokafka import AIOKafkaProducer

router = APIRouter()
_producer = None


def _extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip

    return request.client.host

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_URL", "kafka:9092")
        )
        await _producer.start()
    return _producer


@router.post("", response_model=BookingResponse, include_in_schema=False)
@router.post("/", response_model=BookingResponse)
async def create_booking(request: Request, booking: BookingRequest):
    client_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    # Antifrod inline Redis check
    ip_key = f"af:ip:{client_ip}"
    requests_count = int(await redis_client.incr(ip_key) or 1)
    await redis_client.expire(ip_key, 60)
    if requests_count > 30:
        await redis_client.incr("af:blocked_total")
        await redis_client.incr("af:total_requests")
        raise HTTPException(status_code=429, detail="Слишком много запросов с этого IP")

    seat_key = f"af:seat:{booking.event_id}:{booking.seat_id}"
    seat_attempts = int(await redis_client.incr(seat_key) or 1)
    await redis_client.expire(seat_key, 300)
    if seat_attempts > 8:
        await redis_client.incr("af:blocked_total")
        await redis_client.incr("af:total_requests")
        raise HTTPException(status_code=429, detail="Подозрительная активность на этом месте")

    await redis_client.incr("af:allowed_total")
    await redis_client.incr("af:total_requests")

    # Redis lock
    lock_key = f"seat_lock:{booking.event_id}:{booking.seat_id}"
    lock_acquired = await redis_client.set(lock_key, "locked", nx=True, ex=600)
    if not lock_acquired:
        raise HTTPException(status_code=409, detail="Место уже занято или забронировано")

    booking_id = str(uuid.uuid4())
    try:
        async with get_db() as db:
            await db.execute(
                """INSERT INTO bookings (id, event_id, seat_id, user_id, user_email, status)
                   VALUES ($1, $2, $3, $4, $5, 'pending')""",
                booking_id,
                booking.event_id,
                booking.seat_id,
                booking.user_id,
                booking.user_email,
            )
        producer = await get_producer()
        await producer.send(
            "booking.confirmed",
            value=json.dumps({
                "booking_id": booking_id,
                "event_id":   booking.event_id,
                "seat_id":    booking.seat_id,
                "user_id":    booking.user_id,
                "user_email": booking.user_email,
                "ip":         client_ip,
                "user_agent": user_agent,
            }).encode(),
        )
    except Exception as e:
        await redis_client.delete(lock_key)
        raise HTTPException(status_code=500, detail=str(e))

    return BookingResponse(
        booking_id=booking_id,
        status="confirmed",
        message="Место успешно забронировано!",
    )


@router.delete("/{booking_id}")
async def cancel_booking(booking_id: str):
    async with get_db() as db:
        row = await db.fetchrow(
            "SELECT event_id, seat_id FROM bookings WHERE id = $1", booking_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Бронирование не найдено")
        lock_key = f"seat_lock:{row['event_id']}:{row['seat_id']}"
        await redis_client.delete(lock_key)
        await db.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = $1", booking_id
        )
    return {"message": "Бронирование отменено"}


@router.head("/{booking_id}/ticket", include_in_schema=False)
@router.head("/{booking_id}/ticket/", include_in_schema=False)
@router.get("/{booking_id}/ticket")
@router.get("/{booking_id}/ticket/", include_in_schema=False)
async def download_ticket(booking_id: str):
    return RedirectResponse(url=f"/api/tickets/{booking_id}/download/", status_code=307)
    import os
    path = f"/app/media/tickets/{booking_id}.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Билет ещё генерируется, попробуйте через 5 секунд")
    return FileResponse(path, media_type="application/pdf", filename=f"ticket_{booking_id}.pdf")
