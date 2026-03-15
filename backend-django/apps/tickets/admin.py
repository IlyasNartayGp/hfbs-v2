from django.contrib import admin
from django.utils.html import format_html
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        "booking_id", "event_name", "seat",
        "user_email", "status_badge", "created_at"
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["booking_id", "user_email", "event_name"]
    readonly_fields = ["booking_id", "created_at", "pdf_download_link"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Билет", {
            "fields": ("booking_id", "event_name", "seat", "user_email")
        }),
        ("PDF", {
            "fields": ("status", "pdf_path", "pdf_download_link")
        }),
        ("Системное", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "pending":   ("orange", "⏳ Ожидает"),
            "generated": ("green",  "✓ Готов"),
            "sent":      ("blue",   "📧 Отправлен"),
            "failed":    ("red",    "✗ Ошибка"),
        }
        color, label = colors.get(obj.status, ("gray", obj.status))
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>', color, label
        )
    status_badge.short_description = "Статус"

    def pdf_download_link(self, obj):
        if obj.pdf_path:
            return format_html(
                '<a href="/api/tickets/{}/download/" target="_blank">📥 Скачать PDF</a>',
                obj.booking_id
            )
        return "—"
    pdf_download_link.short_description = "PDF"

    actions = ["retry_generation"]

    @admin.action(description="Повторить генерацию PDF")
    def retry_generation(self, request, queryset):
        from .tasks import generate_ticket_pdf, send_ticket_email
        from celery import chain
        for ticket in queryset.filter(status__in=["pending", "failed"]):
            chain(
                generate_ticket_pdf.s(
                    str(ticket.booking_id),
                    ticket.event_name,
                    ticket.seat,
                    ticket.user_email,
                ) | send_ticket_email.s(ticket.user_email)
            ).delay()
        self.message_user(request, f"Задача поставлена для {queryset.count()} билетов")
