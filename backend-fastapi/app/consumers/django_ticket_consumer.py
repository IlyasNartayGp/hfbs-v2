import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer

from app.services.ticket_gateway import request_ticket_generation

KAFKA_URL = os.getenv("KAFKA_URL", "kafka:9092")


async def run():
    while True:
        try:
            consumer = AIOKafkaConsumer(
                "booking.confirmed",
                bootstrap_servers=KAFKA_URL,
                group_id="ticket-service",
                auto_offset_reset="earliest",
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            await consumer.start()
            print("[ticket-consumer] started, forwarding booking.confirmed to Django...")
            try:
                async for msg in consumer:
                    try:
                        data = json.loads(msg.value)
                        await request_ticket_generation(
                            {
                                "booking_id": data["booking_id"],
                                "event_id": data["event_id"],
                                "seat_id": data["seat_id"],
                                "user_id": data.get("user_id", "unknown"),
                                "user_email": data.get("user_email"),
                            }
                        )
                    except Exception as exc:
                        print(f"[ticket-consumer] message error: {exc}")
            finally:
                await consumer.stop()
        except Exception as exc:
            print(f"[ticket-consumer] connection error: {exc}, retry in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run())
