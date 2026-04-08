from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import events, bookings, health, auth, compat, ticket_status
from app.core.database import get_db
from app.core.security import hash_password


LOADTEST_USERS = [
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "email": "loadtest@hfbs.local",
        "name": "loadtest",
        "password": "loadtest123",
        "seat_ids": [1, 2, 3],
        "booking_ids": [
            "20000000-0000-0000-0000-000000000001",
            "20000000-0000-0000-0000-000000000002",
            "20000000-0000-0000-0000-000000000003",
        ],
    },
    {
        "id": "10000000-0000-0000-0000-000000000002",
        "email": "loadtest_fastapi@hfbs.local",
        "name": "loadtest_fastapi",
        "password": "loadtest123",
        "seat_ids": [4, 5, 6],
        "booking_ids": [
            "20000000-0000-0000-0000-000000000011",
            "20000000-0000-0000-0000-000000000012",
            "20000000-0000-0000-0000-000000000013",
        ],
    },
]

app = FastAPI(
    redirect_slashes=False,
    title="HFBS — Booking Service",
    description="High-Frequency Booking System — async бронирование",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   prefix="/health",       tags=["health"])
app.include_router(auth.router,     prefix="/api/auth",     tags=["auth"])
app.include_router(events.router,   prefix="/api/events",   tags=["events"])
app.include_router(ticket_status.router, tags=["ticket-status"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(compat.router, tags=["compat"])


async def ensure_loadtest_state():
    async with get_db() as db:
        for user in LOADTEST_USERS:
            existing_user = await db.fetchrow(
                "SELECT id FROM users WHERE id = $1 OR email = $2 OR name = $3",
                user["id"],
                user["email"],
                user["name"],
            )
            if not existing_user:
                await db.execute(
                    """
                    INSERT INTO users (id, email, name, password_hash)
                    VALUES ($1, $2, $3, $4)
                    """,
                    user["id"],
                    user["email"],
                    user["name"],
                    hash_password(user["password"]),
                )

            for booking_id, seat_id in zip(user["booking_ids"], user["seat_ids"]):
                seat = await db.fetchrow(
                    "SELECT event_id FROM seats WHERE id = $1",
                    seat_id,
                )
                if not seat:
                    continue

                existing_booking = await db.fetchrow(
                    "SELECT id FROM bookings WHERE id = $1",
                    booking_id,
                )
                if existing_booking:
                    continue

                await db.execute(
                    """
                    INSERT INTO bookings (id, event_id, seat_id, user_id, user_email, status)
                    VALUES ($1, $2, $3, $4, $5, 'PAID')
                    """,
                    booking_id,
                    seat["event_id"],
                    seat_id,
                    user["id"],
                    user["email"],
                )

@app.on_event("startup")
async def startup():
    from app.core.redis import redis_client
    await redis_client.connect()
    await ensure_loadtest_state()

@app.on_event("shutdown")
async def shutdown():
    from app.core.redis import redis_client
    await redis_client.disconnect()
