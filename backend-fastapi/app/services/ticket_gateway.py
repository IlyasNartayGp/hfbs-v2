import os

import httpx


DJANGO_TICKET_URL = os.getenv(
    "DJANGO_TICKET_URL",
    "http://django:8002/api/tickets/generate/",
)


async def request_ticket_generation(payload: dict) -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(DJANGO_TICKET_URL, json=payload)
        response.raise_for_status()
