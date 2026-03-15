from django.db import models
import uuid


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_id = models.UUIDField(unique=True)
    event_name = models.CharField(max_length=255)
    seat = models.CharField(max_length=50)
    user_email = models.EmailField()
    pdf_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Ожидает генерации"),
            ("generated", "PDF создан"),
            ("sent", "Отправлен"),
            ("failed", "Ошибка"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Билет {self.booking_id} — {self.event_name}"
