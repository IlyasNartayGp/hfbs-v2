from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    venue = models.CharField(max_length=255, verbose_name="Место проведения")
    date = models.DateTimeField(verbose_name="Дата и время")
    description = models.TextField(blank=True, verbose_name="Описание")
    image_url = models.URLField(blank=True, verbose_name="Изображение")
    total_seats = models.IntegerField(default=100, verbose_name="Всего мест")
    available_seats = models.IntegerField(default=100, verbose_name="Свободных мест")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    sale_open = models.BooleanField(default=False, verbose_name="Продажи открыты")
    sale_open_at = models.DateTimeField(null=True, blank=True, verbose_name="Время открытия продаж")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} — {self.date.strftime('%d.%m.%Y')}"


class SeatCategory(models.Model):
    CATEGORY_CHOICES = [
        ("vip", "VIP"),
        ("standard", "Стандарт"),
        ("economy", "Эконом"),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    color = models.CharField(max_length=20, default="#6366f1", verbose_name="Цвет на карте")

    class Meta:
        verbose_name = "Категория мест"
        verbose_name_plural = "Категории мест"

    def __str__(self):
        return f"{self.event.name} — {self.name} ({self.price} ₸)"


class Seat(models.Model):
    STATUS_CHOICES = [
        ("available", "Свободно"),
        ("booked", "Забронировано"),
        ("sold", "Продано"),
        ("blocked", "Заблокировано"),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="seats")
    category = models.ForeignKey(
        SeatCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="seats"
    )
    row = models.CharField(max_length=5, verbose_name="Ряд")
    number = models.IntegerField(verbose_name="Номер места")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default="available", verbose_name="Статус"
    )

    class Meta:
        verbose_name = "Место"
        verbose_name_plural = "Места"
        unique_together = ["event", "row", "number"]
        ordering = ["row", "number"]

    def __str__(self):
        return f"Ряд {self.row}, место {self.number} — {self.event.name}"
