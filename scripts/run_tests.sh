#!/bin/bash
set +e

HOST="${1:-http://localhost:8880}"
REPORT_DIR="./scripts/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CSV_PREFIX="${REPORT_DIR}/locust_${TIMESTAMP}"

echo "╔══════════════════════════════════════════╗"
echo "║     HFBS v2 — Нагрузочное тестирование  ║"
echo "╚══════════════════════════════════════════╝"
echo "Host: $HOST"
echo "Время: $(date '+%d.%m.%Y %H:%M:%S')"
echo ""

# Полный сброс перед стартом
docker compose exec -T redis redis-cli FLUSHDB > /dev/null
docker compose exec -T postgres psql -U hfbs -d hfbs -c "DELETE FROM bookings;" > /dev/null 2>&1 || true
echo "✓ Redis и БД очищены"

# ── ТЕСТ 1: Базовая нагрузка ─────────────────────────────
echo ""
echo "▶ Тест 1/3: Базовая нагрузка (100 юзеров, 30 сек)..."
locust -f ./scripts/locustfile.py \
  --host=$HOST \
  --users 100 \
  --spawn-rate 20 \
  --run-time 30s \
  --headless \
  --csv="${CSV_PREFIX}_test1" \
  2>/dev/null
echo "✓ Тест 1 завершён"

# ── ТЕСТ 2: Race condition ────────────────────────────────
echo ""
echo "▶ Тест 2/3: Race condition (500 юзеров на 1 место)..."
# Сброс locks и antifrod счётчиков для чистого race теста
docker compose exec -T redis redis-cli DEL "seat_lock:1:1" > /dev/null 2>&1 || true
docker compose exec -T redis redis-cli DEL "af:seat:1:1" > /dev/null 2>&1 || true
docker compose exec -T redis redis-cli KEYS "af:ip:*" | xargs -r docker compose exec -T redis redis-cli DEL > /dev/null 2>&1 || true
docker compose exec -T postgres psql -U hfbs -d hfbs -c "DELETE FROM bookings WHERE seat_id=1 AND event_id=1;" > /dev/null 2>&1 || true

locust -f ./scripts/race_test.py \
  --host=$HOST \
  --users 500 \
  --spawn-rate 500 \
  --run-time 15s \
  --headless \
  --csv="${CSV_PREFIX}_test2" \
  2>/dev/null

RACE_COUNT=$(docker compose exec -T postgres psql -U hfbs -d hfbs -t -c \
  "SELECT COUNT(*) FROM bookings WHERE seat_id=1 AND event_id=1;" 2>/dev/null | tr -d ' \n')
if [ -z "$RACE_COUNT" ]; then RACE_COUNT="0"; fi
echo "✓ Тест 2 завершён — забронировано мест: ${RACE_COUNT}"

# ── ТЕСТ 3: Боты + Люди ───────────────────────────────────
echo ""
echo "▶ Тест 3/3: Боты + Люди (200 юзеров, 30 сек)..."
# Только seat locks — af: счётчики НЕ сбрасываем
docker compose exec -T redis redis-cli KEYS "seat_lock:*" | \
  xargs -r docker compose exec -T redis redis-cli DEL > /dev/null 2>&1 || true

locust -f ./scripts/locustfile.py \
  --host=$HOST \
  --users 200 \
  --spawn-rate 30 \
  --run-time 30s \
  --headless \
  --csv="${CSV_PREFIX}_test3" \
  2>/dev/null
echo "✓ Тест 3 завершён"

# ── Antifrod статистика (после всех тестов) ───────────────
echo ""
echo "▶ Сбор antifrod статистики..."
ANTIFROD=$(curl -s ${HOST}/health/antifrod-stats 2>/dev/null)
BLOCKED=$(echo $ANTIFROD | python3 -c "import json,sys; print(json.load(sys.stdin)['blocked_total'])" 2>/dev/null)
ALLOWED=$(echo $ANTIFROD | python3 -c "import json,sys; print(json.load(sys.stdin)['allowed_total'])" 2>/dev/null)
echo "Заблокировано: ${BLOCKED}, Пропущено: ${ALLOWED}"

# ── Генерация PDF ─────────────────────────────────────────
echo ""
echo "▶ Генерация PDF отчёта..."
python3 ./scripts/generate_report.py \
  --csv-prefix="${CSV_PREFIX}" \
  --race-count="${RACE_COUNT}" \
  --antifrod="${ANTIFROD}" \
  --output="${REPORT_DIR}/report_${TIMESTAMP}.pdf"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Отчёт готов:                            ║"
echo "║  ${REPORT_DIR}/report_${TIMESTAMP}.pdf"
echo "╚══════════════════════════════════════════╝"
