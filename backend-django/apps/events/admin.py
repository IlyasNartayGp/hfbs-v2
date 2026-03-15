from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Event, Seat, SeatCategory


class SeatCategoryInline(admin.TabularInline):
    model = SeatCategory
    extra = 3
    fields = ["name", "price", "color"]


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    fields = ["row", "number", "price", "status", "category"]
    readonly_fields = []
    show_change_link = True
    max_num = 50
    can_delete = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "name", "venue", "date", "total_seats",
        "available_seats", "sale_status", "is_active"
    ]
    list_filter = ["is_active", "sale_open", "date"]
    search_fields = ["name", "venue"]
    readonly_fields = ["created_at", "available_seats"]
    inlines = [SeatCategoryInline]
    actions = ["open_sales", "close_sales", "generate_seats"]

    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "venue", "date", "description", "image_url")
        }),
        ("Места", {
            "fields": ("total_seats", "available_seats")
        }),
        ("Продажи", {
            "fields": ("is_active", "sale_open", "sale_open_at")
        }),
        ("Системное", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    def sale_status(self, obj):
        if obj.sale_open:
            return format_html('<span style="color:green;font-weight:bold">✓ Открыты</span>')
        return format_html('<span style="color:gray">✗ Закрыты</span>')
    sale_status.short_description = "Продажи"

    @admin.action(description="Открыть продажи")
    def open_sales(self, request, queryset):
        queryset.update(sale_open=True, sale_open_at=timezone.now())
        self.message_user(request, f"Продажи открыты для {queryset.count()} событий")

    @admin.action(description="Закрыть продажи")
    def close_sales(self, request, queryset):
        queryset.update(sale_open=False)
        self.message_user(request, f"Продажи закрыты для {queryset.count()} событий")

    @admin.action(description="Сгенерировать места (10 рядов × 20 мест)")
    def generate_seats(self, request, queryset):
        for event in queryset:
            if event.seats.exists():
                continue
            category = event.categories.filter(name="standard").first()
            seats = []
            for row_num in range(1, 11):
                row_letter = chr(64 + row_num)
                for seat_num in range(1, 21):
                    price = 15000 if row_num <= 3 else 10000 if row_num <= 6 else 5000
                    seats.append(Seat(
                        event=event,
                        category=category,
                        row=row_letter,
                        number=seat_num,
                        price=price,
                    ))
            Seat.objects.bulk_create(seats)
            event.total_seats = len(seats)
            event.available_seats = len(seats)
            event.save()
        self.message_user(request, "Места сгенерированы")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["event", "row", "number", "price", "status", "category"]
    list_filter = ["event", "status", "category"]
    search_fields = ["event__name", "row"]
    list_editable = ["status"]
    list_per_page = 100


@admin.register(SeatCategory)
class SeatCategoryAdmin(admin.ModelAdmin):
    list_display = ["event", "name", "price", "color"]
    list_filter = ["event", "name"]
