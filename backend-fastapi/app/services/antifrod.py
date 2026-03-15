import httpx
import os

ANTIFROD_URL = os.getenv("ANTIFROD_URL", "http://antifrod:9303")


async def check_antifrod(
    ip: str,
    user_agent: str,
    seat_id: int,
    event_id: int,
    seat_price: float = 5000.0,
    is_front_row: bool = False,
) -> bool:
    """
    Отправляет запрос в Antifrod сервис.
    Возвращает True если бот (verdict=blocked), False иначе.
    При ошибке сервиса — fail open (пропускаем).
    """
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            resp = await client.post(
                f"{ANTIFROD_URL}/api/antifrod/check",
                json={
                    "ip": ip,
                    "user_agent": user_agent,
                    "seat_id": seat_id,
                    "event_id": event_id,
                    "seat_price": seat_price,
                    "is_front_row": is_front_row,
                },
            )
            data = resp.json()
            return data.get("verdict") == "blocked"
    except Exception:
        return False
