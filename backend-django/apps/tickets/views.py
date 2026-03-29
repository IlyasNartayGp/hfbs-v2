from django.http import FileResponse, JsonResponse
from django.views import View
import os

class GenerateTicketView(View):
    def post(self, request):
        import json
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        try:
            data = json.loads(request.body)
            booking_id = data.get('booking_id', 'unknown')
            output_path = f'/app/media/tickets/{booking_id}.pdf'
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            c.setFont('Helvetica-Bold', 24)
            c.drawCentredString(width / 2, height - 80, 'HFBS — Электронный билет')
            c.setLineWidth(2)
            c.line(40, height - 100, width - 40, height - 100)
            c.setFont('Helvetica', 14)
            c.drawString(60, height - 150, f'Номер брони: {booking_id}')
            c.setFont('Helvetica-Oblique', 10)
            c.drawCentredString(width / 2, 60, 'Предъявите этот билет на входе')
            c.save()
            return JsonResponse({'status': 'ok', 'path': output_path})
        except Exception as e:
            return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)

class DownloadTicketView(View):
    def get(self, request, booking_id):
        path = f'/app/media/tickets/{booking_id}.pdf'
        if not os.path.exists(path):
            return JsonResponse({'detail': 'Билет не найден'}, status=404)
        return FileResponse(open(path, 'rb'), content_type='application/pdf')
