from fastapi import APIRouter, HTTPException, Request
from app.core.redis import redis_client
from app.core.database import get_db
from app.schemas.booking import BookingRequest, BookingResponse
from app.services.antifrod import check_antifrod
import httpx
import uuid

router = APIRouter()


@router.post("/", response_model=BookingResponse)
async def create_booking(request: Request, booking: BookingRequest):
    """
    Бронирование места.
    1. Antifrod проверка — не бот ли?
    2. Redis lock — захватываем место
    3. Транзакция в БД
    4. Отправка задачи Celery для PDF
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # 1. Antifrod проверка
    is_bot = await check_antifrod(
        ip=client_ip,
        user_agent=user_agent,
        seat_id=booking.seat_id,
        event_id=booking.event_id,
        seat_price=getattr(booking, "seat_price", 5000.0),
        is_front_row=getattr(booking, "is_front_row", False),
    )
    if is_bot:
        raise HTTPException(
            status_code=429,
            detail="Подозрительная активность. Попробуйте позже."
        )

    # 2. Redis lock на место (TTL 10 минут)
    lock_key = f"seat_lock:{booking.event_id}:{booking.seat_id}"
    lock_acquired = await redis_client.set(
        lock_key, "locked", nx=True, ex=600
    )
    if not lock_acquired:
        raise HTTPException(
            status_code=409,
            detail="Место уже занято или забронировано"
        )

    # 3. Создаём бронирование в БД
    booking_id = str(uuid.uuid4())
    try:
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO bookings (id, event_id, seat_id, user_id, status)
                VALUES ($1, $2, $3, $4, 'pending')
                """,
                booking_id, booking.event_id, booking.seat_id, booking.user_id
            )
    except Exception as e:
        await redis_client.delete(lock_key)
        raise HTTPException(status_code=500, detail=str(e))

    # 4. Отправляем задачу Django/Celery для генерации PDF
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://django:9202/api/tickets/generate/",
            json={"booking_id": booking_id}
        )

    return BookingResponse(
        booking_id=booking_id,
        status="confirmed",
        message="Место успешно забронировано! PDF билет отправлен на email."
    )


@router.delete("/{booking_id}")
async def cancel_booking(booking_id: str):
    """Отмена бронирования — освобождаем Redis lock"""
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
