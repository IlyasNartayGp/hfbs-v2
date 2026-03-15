from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from .models import Ticket
from .tasks import generate_ticket_pdf, send_ticket_email
import os


class GenerateTicketView(APIView):
    """
    POST /api/tickets/generate/
    Принимает booking_id от FastAPI, ставит задачу в очередь Celery.
    Sync Django view — намеренно, это CPU-bound задача.
    """
    def post(self, request):
        booking_id = request.data.get("booking_id")
        event_name = request.data.get("event_name", "Мероприятие")
        seat = request.data.get("seat", "—")
        user_email = request.data.get("user_email", "user@example.com")

        if not booking_id:
            return Response(
                {"error": "booking_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket = Ticket.objects.create(
            booking_id=booking_id,
            event_name=event_name,
            seat=seat,
            user_email=user_email,
        )

        # Отправляем в очередь Celery
        chain = generate_ticket_pdf.s(
            str(booking_id), event_name, seat, user_email
        ) | send_ticket_email.s(user_email)
        chain.delay()

        return Response(
            {"status": "queued", "ticket_id": str(ticket.id)},
            status=status.HTTP_202_ACCEPTED,
        )


class DownloadTicketView(APIView):
    """GET /api/tickets/<booking_id>/download/"""
    def get(self, request, booking_id):
        try:
            ticket = Ticket.objects.get(booking_id=booking_id)
        except Ticket.DoesNotExist:
            return Response({"error": "Билет не найден"}, status=404)

        if not ticket.pdf_path or not os.path.exists(ticket.pdf_path):
            return Response({"error": "PDF ещё генерируется"}, status=202)

        return FileResponse(
            open(ticket.pdf_path, "rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"ticket_{booking_id}.pdf",
        )
