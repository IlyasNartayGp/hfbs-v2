import asyncio, json, os
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import redis.asyncio as aioredis
import httpx

REDIS_URL    = os.getenv("REDIS_URL", "redis://redis:6379")
KAFKA_URL    = os.getenv("KAFKA_URL", "kafka:9092")
ANTIFROD_URL = os.getenv("ANTIFROD_URL", "http://antifrod:9303")


async def run():
    redis = await aioredis.from_url(REDIS_URL)
    while True:
        try:
            producer = AIOKafkaProducer(bootstrap_servers=KAFKA_URL)
            await producer.start()
            consumer = AIOKafkaConsumer(
                "booking.confirmed",
                bootstrap_servers=KAFKA_URL,
                group_id="antifrod-service",
                auto_offset_reset="earliest",
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            await consumer.start()
            print("[antifrod-consumer] started, listening booking.confirmed...")
            try:
                async for msg in consumer:
                    try:
                        data = json.loads(msg.value)
                        await check_and_act(data, redis, producer)
                    except Exception as e:
                        print(f"[antifrod-consumer] message error: {e}")
            finally:
                await consumer.stop()
                await producer.stop()
        except Exception as e:
            print(f"[antifrod-consumer] connection error: {e}, retry in 5s...")
            await asyncio.sleep(5)


async def check_and_act(data: dict, redis, producer):
    booking_id = data["booking_id"]
    ip         = data.get("ip", "")
    user_agent = data.get("user_agent", "")
    seat_id    = data["seat_id"]
    event_id   = data["event_id"]

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(
                f"{ANTIFROD_URL}/api/antifrod/check",
                json={"ip": ip, "user_agent": user_agent,
                      "seat_id": seat_id, "event_id": event_id},
            )
            verdict = resp.json().get("verdict", "allowed")
    except Exception:
        verdict = "allowed"

    if verdict == "blocked":
        lock_key = f"seat_lock:{event_id}:{seat_id}"
        await redis.delete(lock_key)
        await producer.send(
            "booking.cancelled",
            value=json.dumps({
                "booking_id": booking_id,
                "reason": "antifrod_blocked",
            }).encode(),
        )
        print(f"[antifrod-consumer] BLOCKED {booking_id}, lock released")
    else:
        print(f"[antifrod-consumer] OK {booking_id} verdict={verdict}")


if __name__ == "__main__":
    asyncio.run(run())
