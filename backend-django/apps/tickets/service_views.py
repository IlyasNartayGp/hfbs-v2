import json
import os

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views import View
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import Ticket


def _ticket_path(booking_id: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, "tickets", f"{booking_id}.pdf")


def _write_ticket_pdf(*, booking_id: str, event_name: str, seat_label: str, user_email: str) -> str:
    output_path = _ticket_path(booking_id)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pdf = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 80, "HFBS Ticket")
    pdf.setLineWidth(2)
    pdf.line(40, height - 100, width - 40, height - 100)
    pdf.setFont("Helvetica", 14)
    pdf.drawString(60, height - 150, f"Booking ID: {booking_id}")
    pdf.drawString(60, height - 180, f"Event: {event_name}")
    pdf.drawString(60, height - 210, f"Seat: {seat_label}")
    pdf.drawString(60, height - 240, f"Email: {user_email}")
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(width / 2, 60, "Present this ticket at the entrance")
    pdf.save()
    return output_path


class GenerateTicketView(View):
    def post(self, request):
        try:
            data = json.loads(request.body or "{}")
            booking_id = str(data.get("booking_id") or "").strip()
            if not booking_id:
                return JsonResponse({"detail": "booking_id is required"}, status=400)

            event_name = data.get("event_name") or f"Event #{data.get('event_id', '?')}"
            seat_label = data.get("seat_label") or f"Seat #{data.get('seat_id', '?')}"
            user_email = data.get("user_email") or "unknown@hfbs.local"

            output_path = _write_ticket_pdf(
                booking_id=booking_id,
                event_name=event_name,
                seat_label=seat_label,
                user_email=user_email,
            )

            Ticket.objects.update_or_create(
                booking_id=booking_id,
                defaults={
                    "event_name": event_name,
                    "seat": seat_label,
                    "user_email": user_email,
                    "pdf_path": output_path,
                    "status": "generated",
                },
            )

            return JsonResponse({"status": "ok", "path": output_path})
        except Exception as exc:
            return JsonResponse({"status": "error", "detail": str(exc)}, status=500)


class DownloadTicketView(View):
    def head(self, request, booking_id):
        return self.get(request, booking_id)

    def get(self, request, booking_id):
        booking_id = str(booking_id)
        ticket = Ticket.objects.filter(booking_id=booking_id).first()

        if ticket is None:
            ticket = Ticket.objects.create(
                booking_id=booking_id,
                event_name="HFBS Event",
                seat="TBD",
                user_email="unknown@hfbs.local",
                status="pending",
            )

        path = ticket.pdf_path or _ticket_path(booking_id)
        if not os.path.exists(path):
            path = _write_ticket_pdf(
                booking_id=booking_id,
                event_name=ticket.event_name,
                seat_label=ticket.seat,
                user_email=ticket.user_email,
            )
            ticket.pdf_path = path
            ticket.status = "generated"
            ticket.save(update_fields=["pdf_path", "status"])

        return FileResponse(open(path, "rb"), content_type="application/pdf")
