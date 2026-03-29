"""
Сравнительное тестирование HFBS v2

Классы:
  PureLoadUser     — чистая нагрузка без антифрод триггеров (baseline)
  SlowBotUser      — умный бот, обходит rate limit (низкая частота, разные IP)
  DjangoUser       — тестирует Django эндпоинты напрямую
  FastAPIUser      — тестирует FastAPI эндпоинты напрямую
"""
from locust import HttpUser, task, between
import uuid, random, time

HUMAN_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0",
]

EVENT_IDS = [1, 2, 3]


class PureLoadUser(HttpUser):
    """
    Чистая нагрузка — только browse + booking без bot UA.
    Показывает максимальный RPS системы без антифрод блокировок.
    """
    wait_time = between(0.5, 1.5)
    weight = 1

    def on_start(self):
        self.user_id = str(uuid.uuid4())
        self.headers = {
            "User-Agent": random.choice(HUMAN_UAS),
            "Content-Type": "application/json",
        }
        # Уникальный IP симуляция через user_id
        self._seat_counter = 0

    @task(3)
    def browse(self):
        self.client.get("/api/events/", headers=self.headers, name="[pure] GET /api/events/")

    @task(2)
    def seats(self):
        eid = random.choice(EVENT_IDS)
        self.client.get(f"/api/events/{eid}/seats", headers=self.headers,
                        name="[pure] GET /api/events/{id}/seats")

    @task(5)
    def book(self):
        self._seat_counter += 1
        # Каждый раз новое место чтобы не триггерить seat_attempts
        seat_id = random.randint(1, 400)
        self.client.post("/api/bookings/", json={
            "event_id": random.choice(EVENT_IDS),
            "seat_id":  seat_id,
            "user_id":  self.user_id,
        }, headers=self.headers, name="[pure] POST /api/bookings/")


class SlowBotUser(HttpUser):
    """
    Умный бот — обходит rate limit.
    Медленный темп, разные места, нормальный UA.
    Проверяем насколько ML модель его поймает.
    """
    wait_time = between(2, 4)
    weight = 1

    def on_start(self):
        # Каждый бот имитирует нового пользователя
        self.ua = random.choice(HUMAN_UAS)
        self.event_id = random.choice(EVENT_IDS)

    @task
    def slow_book(self):
        # Всегда первые ряды — дорогие места
        seat_id = random.randint(1, 50)
        self.client.post("/api/bookings/", json={
            "event_id":    self.event_id,
            "seat_id":     seat_id,
            "user_id":     str(uuid.uuid4()),
            "seat_price":  15000,
            "is_front_row": True,
        }, headers={
            "User-Agent":   self.ua,
            "Content-Type": "application/json",
        }, name="[slow-bot] POST /api/bookings/")


class DjangoUser(HttpUser):
    """
    Тестирует Django sync эндпоинты напрямую — порт 9202.
    Показывает производительность sync Django vs async FastAPI.
    """
    wait_time = between(0.5, 1.5)
    weight = 1

    @task(4)
    def django_events(self):
        self.client.get("/api/events/", name="[django] GET /api/events/")

    @task(2)
    def django_seats(self):
        eid = random.choice(EVENT_IDS)
        self.client.get(f"/api/events/{eid}/seats",
                        name="[django] GET /api/events/{id}/seats")

    @task(1)
    def django_admin(self):
        self.client.get("/admin/", name="[django] GET /admin/")


class FastAPIUser(HttpUser):
    """
    Тестирует FastAPI async эндпоинты напрямую — порт 9101.
    Сравниваем с Django по latency и RPS.
    """
    wait_time = between(0.5, 1.5)
    weight = 1

    @task(4)
    def fastapi_events(self):
        self.client.get("/api/events/", name="[fastapi] GET /api/events/")

    @task(2)
    def fastapi_seats(self):
        eid = random.choice(EVENT_IDS)
        self.client.get(f"/api/events/{eid}/seats",
                        name="[fastapi] GET /api/events/{id}/seats")

    @task(3)
    def fastapi_book(self):
        self.client.post("/api/bookings/", json={
            "event_id": random.choice(EVENT_IDS),
            "seat_id":  random.randint(1, 400),
            "user_id":  str(uuid.uuid4()),
        }, headers={"Content-Type": "application/json"},
           name="[fastapi] POST /api/bookings/")
