from pydantic import BaseModel
from typing import Optional


class BookingRequest(BaseModel):
    event_id: int
    seat_id: int
    user_id: str
    user_email: Optional[str] = None


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    message: str
