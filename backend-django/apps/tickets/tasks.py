from celery import shared_task
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os


@shared_task(bind=True, max_retries=3)
def generate_ticket_pdf(self, booking_id: str, event_name: str, seat: str, user_email: str):
    """
    CPU-bound задача — генерация PDF билета.
    Выполняется в Celery worker (Django sync).
    Это намеренно sync — показываем в дипломе что CPU задачи
    не выигрывают от async.
    """
    try:
        output_path = f"/app/media/tickets/{booking_id}.pdf"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        # Заголовок
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 80, "HFBS — Электронный билет")

        # Линия
        c.setLineWidth(2)
        c.line(40, height - 100, width - 40, height - 100)

        # Данные билета
        c.setFont("Helvetica", 14)
        c.drawString(60, height - 150, f"Мероприятие: {event_name}")
        c.drawString(60, height - 180, f"Место: {seat}")
        c.drawString(60, height - 210, f"Номер брони: {booking_id}")
        c.drawString(60, height - 240, f"Email: {user_email}")

        # QR placeholder
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width / 2, 60, "Предъявите этот билет на входе")

        c.save()
        return {"status": "success", "path": output_path}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@shared_task
def send_ticket_email(booking_id: str, user_email: str):
    """Отправка PDF билета на email (заглушка)"""
    pdf_path = f"/app/media/tickets/{booking_id}.pdf"
    # TODO: интеграция с SMTP / SendGrid
    print(f"Отправка билета {pdf_path} на {user_email}")
    return {"status": "sent", "email": user_email}
