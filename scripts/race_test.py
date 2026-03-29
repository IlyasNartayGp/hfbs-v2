from locust import HttpUser, task, between
import uuid, random

HUMAN_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
]

class RaceConditionTest(HttpUser):
    wait_time = between(0, 0.01)

    @task
    def race(self):
        self.client.post(
            "/api/bookings/",
            json={
                "event_id": 1,
                "seat_id":  1,
                "user_id":  str(uuid.uuid4()),
                "user_email": "stress@test.kz",
                "seat_price": 15000,
                "is_front_row": True,
            },
            headers={
                "User-Agent": random.choice(HUMAN_UAS),
                "Content-Type": "application/json",
            },
            name="/api/bookings/ [race]",
        )
