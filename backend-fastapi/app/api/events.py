from fastapi import APIRouter, HTTPException
from app.core.database import get_db
from app.schemas.event import EventResponse
from typing import List

router = APIRouter()


@router.get("/", response_model=List[EventResponse])
async def list_events():
    """Список всех событий"""
    async with get_db() as db:
        rows = await db.fetch(
            "SELECT id, name, venue, date, total_seats, available_seats FROM events ORDER BY date"
        )
    return [dict(r) for r in rows]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """Детали события с картой мест"""
    async with get_db() as db:
        row = await db.fetchrow(
            "SELECT * FROM events WHERE id = $1", event_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return dict(row)


@router.get("/{event_id}/seats")
async def get_seats(event_id: int):
    """Карта мест — какие свободны, какие заняты"""
    async with get_db() as db:
        rows = await db.fetch(
            """
            SELECT s.id, s.row, s.number, s.price,
                   CASE WHEN b.id IS NOT NULL THEN 'booked' ELSE 'available' END as status
            FROM seats s
            LEFT JOIN bookings b ON b.seat_id = s.id AND b.event_id = $1 AND b.status != 'cancelled'
            WHERE s.event_id = $1
            ORDER BY s.row, s.number
            """,
            event_id
        )
    return [dict(r) for r in rows]
