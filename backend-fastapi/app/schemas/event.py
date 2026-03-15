from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventResponse(BaseModel):
    id: int
    name: str
    venue: str
    date: datetime
    total_seats: int
    available_seats: int
