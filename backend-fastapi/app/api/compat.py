from fastapi import APIRouter, HTTPException, Request

from app.api.auth import build_token_response, fetch_user_by_login
from app.core.database import get_db
from app.core.redis import redis_client
from app.core.security import decode_token, verify_password

router = APIRouter()


async def _get_current_user(request: Request) -> dict:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with get_db() as db:
        user = await db.fetchrow(
            """
            SELECT id, email, name, created_at
            FROM users
            WHERE id = $1
            """,
            payload["sub"],
        )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)


async def _parse_credentials(request: Request) -> tuple[str, str]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    login_value = data.get("username") or data.get("email")
    password = data.get("password")
    if not login_value or not password:
        raise HTTPException(status_code=400, detail="username/email and password are required")
    return str(login_value), str(password)


@router.post("/api/v1/auth/token/")
async def compat_token(request: Request):
    login_value, password = await _parse_credentials(request)
    user = await fetch_user_by_login(login_value)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return build_token_response(user)


@router.get("/api/v1/events/")
async def compat_events():
    async with get_db() as db:
        rows = await db.fetch(
            """
            SELECT id, name, venue, date, total_seats, available_seats
            FROM events
            ORDER BY date
            """
        )
    return [dict(row) for row in rows]


@router.get("/api/v1/events/{event_id}/")
async def compat_event_detail(event_id: int):
    async with get_db() as db:
        row = await db.fetchrow(
            """
            SELECT id, name, venue, date, total_seats, available_seats
            FROM events
            WHERE id = $1
            """,
            event_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return dict(row)


@router.get("/api/v1/seats/")
async def compat_seats(event_id: int):
    async with get_db() as db:
        rows = await db.fetch(
            """
            SELECT s.id, s.event_id, s.row, s.number, s.price,
                   CASE
                       WHEN EXISTS (
                           SELECT 1
                           FROM bookings b
                           WHERE b.seat_id = s.id
                             AND b.event_id = $1
                             AND LOWER(b.status) <> 'cancelled'
                       )
                       THEN 'BOOKED'
                       ELSE 'FREE'
                   END AS base_status
            FROM seats s
            WHERE s.event_id = $1
            ORDER BY s.row, s.number
            """,
            event_id,
        )

    locked_keys = await redis_client.keys(f"seat_lock:{event_id}:*")
    locked_ids = {
        int(key.rsplit(":", 1)[-1])
        for key in locked_keys
        if key.rsplit(":", 1)[-1].isdigit()
    }

    seats = []
    for row in rows:
        seat = dict(row)
        status = seat.pop("base_status")
        if status == "FREE" and seat["id"] in locked_ids:
            status = "RESERVED"
        seat["status"] = status
        seats.append(seat)
    return seats


@router.post("/api/v1/seats/{seat_id}/reserve/")
async def compat_reserve_seat(seat_id: int, request: Request):
    user = await _get_current_user(request)

    async with get_db() as db:
        seat = await db.fetchrow(
            """
            SELECT id, event_id, row, number, price
            FROM seats
            WHERE id = $1
            """,
            seat_id,
        )
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")

        existing = await db.fetchrow(
            """
            SELECT id
            FROM bookings
            WHERE seat_id = $1
              AND LOWER(status) <> 'cancelled'
            LIMIT 1
            """,
            seat_id,
        )
        if existing:
            raise HTTPException(status_code=409, detail="Seat already booked")

    lock_key = f"seat_lock:{seat['event_id']}:{seat_id}"
    acquired = await redis_client.set(lock_key, str(user["id"]), nx=True, ex=300)
    if not acquired:
        raise HTTPException(status_code=409, detail="Seat already reserved")

    return {
        "message": "Seat reserved successfully",
        "seat": {
            "id": seat["id"],
            "event_id": seat["event_id"],
            "row": seat["row"],
            "number": seat["number"],
            "price": float(seat["price"]),
            "status": "RESERVED",
        },
        "lock_ttl_seconds": 300,
    }


@router.post("/api/v1/seats/{seat_id}/release/")
async def compat_release_seat(seat_id: int, request: Request):
    await _get_current_user(request)

    async with get_db() as db:
        seat = await db.fetchrow("SELECT event_id FROM seats WHERE id = $1", seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    await redis_client.delete(f"seat_lock:{seat['event_id']}:{seat_id}")
    return {"message": "Reservation released"}


@router.get("/api/v1/orders/")
async def compat_orders(request: Request):
    user = await _get_current_user(request)
    async with get_db() as db:
        rows = await db.fetch(
            """
            SELECT b.id AS order_id,
                   s.price AS amount,
                   UPPER(b.status) AS status,
                   b.created_at
            FROM bookings b
            JOIN seats s ON s.id = b.seat_id
            WHERE b.user_id = $1
            ORDER BY b.created_at DESC
            """,
            str(user["id"]),
        )
    return [
        {
            "order_id": str(row["order_id"]),
            "amount": float(row["amount"]),
            "status": row["status"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
