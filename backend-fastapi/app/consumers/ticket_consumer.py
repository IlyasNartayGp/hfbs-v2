import asyncio, json, os
from aiokafka import AIOKafkaConsumer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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
            print("[ticket-consumer] started, listening booking.confirmed...")
            try:
                async for msg in consumer:
                    try:
                        data = json.loads(msg.value)
                        await generate_pdf(
                            booking_id=data["booking_id"],
                            event_id=data["event_id"],
                            seat_id=data["seat_id"],
                            user_id=data.get("user_id", "unknown"),
                        )
                    except Exception as e:
                        print(f"[ticket-consumer] message error: {e}")
            finally:
                await consumer.stop()
        except Exception as e:
            print(f"[ticket-consumer] connection error: {e}, retry in 5s...")
            await asyncio.sleep(5)


async def generate_pdf(booking_id: str, event_id: int, seat_id: int, user_id: str):
    output_path = f"/app/media/tickets/{booking_id}.pdf"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 80, "HFBS — Электронный билет")
    c.setLineWidth(2)
    c.line(40, height - 100, width - 40, height - 100)
    c.setFont("Helvetica", 14)
    c.drawString(60, height - 150, f"Мероприятие: event #{event_id}")
    c.drawString(60, height - 180, f"Место: {seat_id}")
    c.drawString(60, height - 210, f"Номер брони: {booking_id}")
    c.drawString(60, height - 240, f"Пользователь: {user_id}")
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, 60, "Предъявите этот билет на входе")
    c.save()
    print(f"[ticket-consumer] PDF готов: {output_path}")


if __name__ == "__main__":
    asyncio.run(run())
