"""
HFBS v2 — Нагрузочные тесты (Locust)

Запуск:
    locust -f locustfile.py --host=http://localhost:8880

Сценарии:
    HumanUser          — обычный пользователь, weight=7
    BotUser            — быстрый бот-скальпер, weight=3
    AuthUser           — авторизованный пользователь, weight=4
    RaceConditionTest  — стресс одного места, weight=0 (запускать отдельно)

Для диплома:
    1. HumanUser 500 польз. — замерь RPS FastAPI vs Django
    2. +BotUser 200 польз.  — смотри блокировки в Dashboard
    3. RaceConditionTest 1000 польз. — проверяй Redis lock (должен быть 1 успех)
"""
from locust import HttpUser, task, between, events
import random
import uuid

HUMAN_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0",
]

BOT_UAS = [
    "python-requests/2.31.0",
    "curl/8.1.2",
    "Go-http-client/1.1",
    "aiohttp/3.9.1",
    "httpx/0.27.0",
]

EVENT_IDS = [1, 2, 3]


class Stats:
    bookings_ok = 0
    bookings_409 = 0
    bookings_429 = 0
    bookings_err = 0

stats = Stats()


@events.quitting.add_listener
def on_quit(environment, **kwargs):
    print("\n========== HFBS ТЕСТ ЗАВЕРШЁН ==========")
    print(f"  Успешных бронирований:    {stats.bookings_ok}")
    print(f"  Место занято (409):       {stats.bookings_409}")
    print(f"  Заблокировано антифрод:   {stats.bookings_429}")
    print(f"  Ошибки сервера:           {stats.bookings_err}")
    total = stats.bookings_ok + stats.bookings_409 + stats.bookings_429 + stats.bookings_err
    if total:
        print(f"  Bot block rate:           {stats.bookings_429/total*100:.1f}%")
    print("=========================================\n")


class HumanUser(HttpUser):
    """Симуляция реального пользователя — нормальный UA, паузы между действиями."""
    wait_time = between(1, 3)
    weight = 7

    def on_start(self):
        self.user_id = str(uuid.uuid4())
        self.email = f"user_{random.randint(10000, 99999)}@test.kz"
        self.headers = {
            "User-Agent": random.choice(HUMAN_UAS),
            "Content-Type": "application/json",
        }

    @task(4)
    def browse_events(self):
        self.client.get("/api/events/", headers=self.headers, name="/api/events/ [list]")

    @task(3)
    def view_seats(self):
        event_id = random.choice(EVENT_IDS)
        self.client.get(
            f"/api/events/{event_id}/seats",
            headers=self.headers,
            name="/api/events/{id}/seats",
        )

    @task(2)
    def book_seat(self):
        seat_id = random.randint(1, 200)
        with self.client.post(
            "/api/bookings/",
            json={
                "event_id": random.choice(EVENT_IDS),
                "seat_id": seat_id,
                "user_id": self.user_id,
                "user_email": self.email,
                "seat_price": random.choice([5000, 10000, 15000]),
                "is_front_row": seat_id <= 25,
            },
            headers=self.headers,
            name="/api/bookings/ [human]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                stats.bookings_ok += 1
            elif resp.status_code in (409, 429):
                stats.bookings_409 += 1 if resp.status_code == 409 else 0
                stats.bookings_429 += 1 if resp.status_code == 429 else 0
                resp.success()
            else:
                stats.bookings_err += 1

    @task(1)
    def view_event_detail(self):
        event_id = random.choice(EVENT_IDS)
        self.client.get(
            f"/api/events/{event_id}",
            headers=self.headers,
            name="/api/events/{id} [detail]",
        )


class BotUser(HttpUser):
    """Бот-скальпер — без пауз, bot UA, только первые ряды. Должен блокироваться."""
    wait_time = between(0.01, 0.05)
    weight = 3

    def on_start(self):
        self.headers = {
            "User-Agent": random.choice(BOT_UAS),
            "Content-Type": "application/json",
        }

    @task
    def bot_book(self):
        seat_id = random.randint(1, 25)
        with self.client.post(
            "/api/bookings/",
            json={
                "event_id": 1,
                "seat_id": seat_id,
                "user_id": str(uuid.uuid4()),
                "user_email": "bot@spam.com",
                "seat_price": 15000,
                "is_front_row": True,
            },
            headers=self.headers,
            name="/api/bookings/ [bot]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 429:
                stats.bookings_429 += 1
                resp.success()
            elif resp.status_code == 200:
                stats.bookings_ok += 1
            else:
                resp.success()


class AuthUser(HttpUser):
    """Авторизованный пользователь — тестирует JWT под нагрузкой."""
    wait_time = between(2, 5)
    weight = 4

    def on_start(self):
        self.token = None
        self.ua = random.choice(HUMAN_UAS)
        email = f"auth_{uuid.uuid4().hex[:8]}@test.kz"
        res = self.client.post(
            "/api/auth/register",
            json={"email": email, "name": "Load Test User", "password": "testpass123"},
            headers={"User-Agent": self.ua},
            name="/api/auth/register",
        )
        if res.status_code == 200:
            self.token = res.json().get("access_token")

    def _headers(self):
        h = {"User-Agent": self.ua, "Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    @task(3)
    def book(self):
        self.client.post(
            "/api/bookings/",
            json={
                "event_id": random.choice(EVENT_IDS),
                "seat_id": random.randint(50, 150),
                "user_id": "auth-user",
                "user_email": "auth@test.kz",
                "seat_price": 5000,
                "is_front_row": False,
            },
            headers=self._headers(),
            name="/api/bookings/ [auth]",
        )

    @task(1)
    def my_bookings(self):
        self.client.get(
            "/api/auth/me/bookings",
            headers=self._headers(),
            name="/api/auth/me/bookings",
        )

    @task(1)
    def profile(self):
        self.client.get(
            "/api/auth/me",
            headers=self._headers(),
            name="/api/auth/me",
        )


class RaceConditionTest(HttpUser):
    """
    Race condition стресс-тест.
    1000 пользователей одновременно на место 1.
    С Redis lock должен быть ровно 1 успех.

    Запуск:
        locust -f locustfile.py --host=http://localhost:8880 \\
               -u 1000 -r 1000 --run-time 15s --headless
    """
    wait_time = between(0, 0.01)
    weight = 0  # отключён в обычном режиме

    @task
    def race(self):
        with self.client.post(
            "/api/bookings/",
            json={
                "event_id": 1,
                "seat_id": 1,
                "user_id": str(uuid.uuid4()),
                "user_email": "stress@test.kz",
                "seat_price": 15000,
                "is_front_row": True,
            },
            headers={
                "User-Agent": random.choice(HUMAN_UAS),
                "Content-Type": "application/json",
            },
            name="/api/bookings/ [race]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                stats.bookings_ok += 1
                print(f"\n[RACE] ✓ МЕСТО ЗАБРОНИРОВАНО! id={resp.json().get('booking_id')}")
            elif resp.status_code in (409, 429):
                stats.bookings_409 += 1
                resp.success()
            else:
                stats.bookings_err += 1
