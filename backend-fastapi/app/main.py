from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import events, bookings, health, auth

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
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])

@app.on_event("startup")
async def startup():
    from app.core.redis import redis_client
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown():
    from app.core.redis import redis_client
    await redis_client.disconnect()
