#!/bin/bash
set +e

HOST="${1:-http://localhost:8880}"
REPORT_DIR="./scripts/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CSV_PREFIX="${REPORT_DIR}/cmp_${TIMESTAMP}"

echo "╔══════════════════════════════════════════════════╗"
echo "║   HFBS v2 — Сравнительное тестирование          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── ТЕСТ A: Чистая нагрузка без антифрод блокировок ──
echo "▶ Тест A: Чистая нагрузка PureLoadUser (200 юзеров, 30 сек)..."
docker compose exec -T redis redis-cli FLUSHDB > /dev/null
docker compose exec -T redis redis-cli KEYS "af:ip:*" | \
  xargs -r docker compose exec -T redis redis-cli DEL > /dev/null 2>&1 || true

locust -f ./scripts/comparison_test.py \
  --host=$HOST \
  --users 200 \
  --spawn-rate 50 \
  --run-time 30s \
  --headless \
  --csv="${CSV_PREFIX}_pure" \
  2>/dev/null
echo "✓ Тест A завершён"
PURE_RPS=$(tail -2 "${CSV_PREFIX}_pure_stats.csv" | head -1 | cut -d',' -f9)
echo "   RPS: ${PURE_RPS}"

# ── ТЕСТ B: Умные боты (slow bot bypass attempt) ─────
echo ""
echo "▶ Тест B: Умные боты SlowBotUser (100 юзеров, 60 сек)..."
docker compose exec -T redis redis-cli FLUSHDB > /dev/null

locust -f ./scripts/comparison_test.py \
  --host=$HOST \
  --users 100 \
  --spawn-rate 20 \
  --run-time 60s \
  --headless \
  --csv="${CSV_PREFIX}_slowbot" \
  2>/dev/null
echo "✓ Тест B завершён"

SLOWBOT_BLOCKED=$(docker compose exec -T redis redis-cli GET "af:blocked_total" 2>/dev/null | tr -d ' \n')
SLOWBOT_ALLOWED=$(docker compose exec -T redis redis-cli GET "af:allowed_total" 2>/dev/null | tr -d ' \n')
echo "   Заблокировано: ${SLOWBOT_BLOCKED:-0}, Пропущено: ${SLOWBOT_ALLOWED:-0}"

# ── ТЕСТ C: Django vs FastAPI сравнение ──────────────
echo ""
echo "▶ Тест C: Django :9202 vs FastAPI :9101 (100 юзеров, 30 сек)..."
docker compose exec -T redis redis-cli FLUSHDB > /dev/null

# Django тест
# Создать отдельные locustfile для Django и FastAPI
cat > /tmp/django_test.py << 'LOCEOF'
from locust import HttpUser, task, between
import random
EVENT_IDS = [1, 2, 3]
class DjangoUser(HttpUser):
    wait_time = between(0.5, 1.5)
    @task(4)
    def events(self):
        self.client.get("/api/events/", name="GET /api/events/")
    @task(2)
    def seats(self):
        self.client.get(f"/api/events/{random.choice(EVENT_IDS)}/seats", name="GET /api/events/{id}/seats")
LOCEOF

cat > /tmp/fastapi_test.py << 'LOCEOF'
from locust import HttpUser, task, between
import random, uuid
EVENT_IDS = [1, 2, 3]
class FastAPIUser(HttpUser):
    wait_time = between(0.5, 1.5)
    @task(4)
    def events(self):
        self.client.get("/api/events/", name="GET /api/events/")
    @task(2)
    def seats(self):
        self.client.get(f"/api/events/{random.choice(EVENT_IDS)}/seats", name="GET /api/events/{id}/seats")
    @task(2)
    def book(self):
        self.client.post("/api/bookings/", json={"event_id": random.choice(EVENT_IDS), "seat_id": random.randint(1,400), "user_id": str(uuid.uuid4())}, headers={"Content-Type": "application/json"}, name="POST /api/bookings/")
LOCEOF

locust -f /tmp/django_test.py   --host=http://localhost:9202   --users 100   --spawn-rate 20   --run-time 30s   --headless   --csv="${CSV_PREFIX}_django"   2>/dev/null
echo "✓ Django тест завершён"
DJANGO_RPS=$(grep "Aggregated" "${CSV_PREFIX}_django_stats.csv" 2>/dev/null | cut -d',' -f10)
DJANGO_P50=$(grep "Aggregated" "${CSV_PREFIX}_django_stats.csv" 2>/dev/null | cut -d',' -f12)

locust -f /tmp/fastapi_test.py   --host=http://localhost:9101   --users 100   --spawn-rate 20   --run-time 30s   --headless   --csv="${CSV_PREFIX}_fastapi"   2>/dev/null
echo "✓ FastAPI тест завершён"
FASTAPI_RPS=$(grep "Aggregated" "${CSV_PREFIX}_fastapi_stats.csv" 2>/dev/null | cut -d',' -f10)
FASTAPI_P50=$(grep "Aggregated" "${CSV_PREFIX}_fastapi_stats.csv" 2>/dev/null | cut -d',' -f12)

# ── Итог в консоли ────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  РЕЗУЛЬТАТЫ СРАВНЕНИЯ                            ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Django  RPS: ${DJANGO_RPS}   P50: ${DJANGO_P50} ms"
echo "║  FastAPI RPS: ${FASTAPI_RPS}   P50: ${FASTAPI_P50} ms"
echo "║  Slow bot заблокировано: ${SLOWBOT_BLOCKED:-0}"
echo "╚══════════════════════════════════════════════════╝"

# ── Генерация PDF ─────────────────────────────────────
ANTIFROD=$(curl -s ${HOST}/health/antifrod-stats 2>/dev/null)

python3 ./scripts/generate_comparison_report.py \
  --csv-prefix="${CSV_PREFIX}" \
  --django-rps="${DJANGO_RPS}" \
  --fastapi-rps="${FASTAPI_RPS}" \
  --django-p50="${DJANGO_P50}" \
  --fastapi-p50="${FASTAPI_P50}" \
  --slowbot-blocked="${SLOWBOT_BLOCKED:-0}" \
  --antifrod="${ANTIFROD}" \
  --output="${REPORT_DIR}/comparison_${TIMESTAMP}.pdf"

echo ""
echo "PDF: ${REPORT_DIR}/comparison_${TIMESTAMP}.pdf"
