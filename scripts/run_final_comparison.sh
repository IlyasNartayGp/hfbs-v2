#!/bin/bash
set +e

cd /opt/hfbs

REPORT_DIR="/opt/hfbs-v2/scripts/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "╔══════════════════════════════════════════════════╗"
echo "║   HFBS — Финальное тестирование всех сервисов   ║"
echo "╚══════════════════════════════════════════════════╝"
echo "100 пользователей / 30 секунд / каждый тест"
echo ""

# ── Тестовые файлы ────────────────────────────────────
cat > /tmp/t_v1django.py << 'LOCEOF'
from locust import HttpUser, task, between
import random

class User(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def events_list(self):
        self.client.get("/api/v1/events/", name="GET /events/")

    @task(2)
    def event_detail(self):
        self.client.get(f"/api/v1/events/{random.randint(1,3)}/", name="GET /events/{id}/")

    @task(3)
    def seats(self):
        self.client.get("/api/v1/seats/?event_id=1", name="GET /seats/")

    @task(2)
    def reserve(self):
        self.client.post(
            f"/api/v1/seats/{random.randint(1,50)}/reserve/",
            json={}, headers={"Content-Type": "application/json"},
            name="POST /seats/reserve/",
        )

    @task(1)
    def orders(self):
        self.client.get("/api/v1/orders/", name="GET /orders/")

    @task(1)
    def ticket(self):
        self.client.get(f"/api/v1/tickets/{random.randint(1,10)}/", name="GET /tickets/{id}/")
LOCEOF

cat > /tmp/t_v1fastapi.py << 'LOCEOF'
from locust import HttpUser, task, between
import random

class User(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def events_list(self):
        self.client.get("/api/v1/events/", name="GET /events/")

    @task(2)
    def event_detail(self):
        self.client.get(f"/api/v1/events/{random.randint(1,3)}/", name="GET /events/{id}/")

    @task(3)
    def seats(self):
        self.client.get("/api/v1/seats/?event_id=1", name="GET /seats/")

    @task(2)
    def reserve(self):
        self.client.post(
            f"/api/v1/seats/{random.randint(1,50)}/reserve/",
            json={}, headers={"Content-Type": "application/json"},
            name="POST /seats/reserve/",
        )

    @task(1)
    def orders(self):
        self.client.get("/api/v1/orders/", name="GET /orders/")

    @task(1)
    def ticket(self):
        self.client.get(f"/api/v1/tickets/{random.randint(1,10)}/", name="GET /tickets/{id}/")
LOCEOF

cat > /tmp/t_v2django.py << 'LOCEOF'
from locust import HttpUser, task, between
import random

class User(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(4)
    def events_list(self):
        self.client.get("/api/events/", name="GET /events/")

    @task(3)
    def event_detail(self):
        self.client.get(f"/api/events/{random.randint(1,3)}/", name="GET /events/{id}/")

    @task(1)
    def ticket_download(self):
        self.client.get(
            f"/api/tickets/test-{random.randint(1,10)}/download/",
            name="GET /tickets/{id}/download/",
        )
LOCEOF

cat > /tmp/t_v2fastapi.py << 'LOCEOF'
from locust import HttpUser, task, between
import random, uuid

class User(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def events_list(self):
        self.client.get("/api/events/", name="GET /events/")

    @task(2)
    def event_detail(self):
        self.client.get(f"/api/events/{random.randint(1,3)}", name="GET /events/{id}/")

    @task(3)
    def seats(self):
        self.client.get(f"/api/events/{random.randint(1,3)}/seats", name="GET /seats/")

    @task(2)
    def book(self):
        self.client.post("/api/bookings/", json={
            "event_id": random.choice([1,2,3]),
            "seat_id":  random.randint(1, 400),
            "user_id":  str(uuid.uuid4()),
        }, headers={"Content-Type": "application/json"}, name="POST /bookings/")

    @task(1)
    def ticket(self):
        self.client.get(
            f"/api/bookings/00000000-0000-0000-0000-{random.randint(100000000000,999999999999)}/ticket",
            name="GET /bookings/{id}/ticket",
        )
LOCEOF

# ── Запуск тестов ─────────────────────────────────────
echo "▶ [1/4] v1 Django sync :8000..."
locust -f /tmp/t_v1django.py \
    --host=http://localhost:8000 \
    --users 100 --spawn-rate 30 --run-time 30s \
    --headless --csv="${REPORT_DIR}/fc_v1d_${TIMESTAMP}" 2>/dev/null
echo "   ✓ $(wc -l < ${REPORT_DIR}/fc_v1d_${TIMESTAMP}_stats.csv) строк"

echo "▶ [2/4] v1 FastAPI async :8001..."
locust -f /tmp/t_v1fastapi.py \
    --host=http://localhost:8001 \
    --users 100 --spawn-rate 30 --run-time 30s \
    --headless --csv="${REPORT_DIR}/fc_v1f_${TIMESTAMP}" 2>/dev/null
echo "   ✓ $(wc -l < ${REPORT_DIR}/fc_v1f_${TIMESTAMP}_stats.csv) строк"

echo "▶ [3/4] v2 Django sync :9202..."
locust -f /tmp/t_v2django.py \
    --host=http://localhost:9202 \
    --users 100 --spawn-rate 30 --run-time 30s \
    --headless --csv="${REPORT_DIR}/fc_v2d_${TIMESTAMP}" 2>/dev/null
echo "   ✓ $(wc -l < ${REPORT_DIR}/fc_v2d_${TIMESTAMP}_stats.csv) строк"

echo "▶ [4/4] v2 FastAPI async :9101..."
locust -f /tmp/t_v2fastapi.py \
    --host=http://localhost:9101 \
    --users 100 --spawn-rate 30 --run-time 30s \
    --headless --csv="${REPORT_DIR}/fc_v2f_${TIMESTAMP}" 2>/dev/null
echo "   ✓ $(wc -l < ${REPORT_DIR}/fc_v2f_${TIMESTAMP}_stats.csv) строк"

# ── Вывод в консоль + сбор аргументов для PDF ────────
python3 - << PYEOF
import csv, subprocess, sys

def load(path):
    try:
        with open(path) as f: return list(csv.DictReader(f))
    except: return []

def find(rows, substr):
    for r in rows:
        if substr.lower() in r.get('Name','').lower(): return r
    return {}

def g(rows, substr, col):
    r = find(rows, substr)
    vals = list(r.values())
    try: return vals[col].strip() or "0"
    except: return "0"

def fmt(v, s=""):
    try:
        f = float(v)
        return f"{f:.1f}{s}" if f > 0 else "—"
    except: return f"{v}{s}" if v and v != "0" else "—"

RD = "${REPORT_DIR}"
TS = "${TIMESTAMP}"
RPS, P50, P95 = 9, 10, 15

v1d = load(f"{RD}/fc_v1d_{TS}_stats.csv")
v1f = load(f"{RD}/fc_v1f_{TS}_stats.csv")
v2d = load(f"{RD}/fc_v2d_{TS}_stats.csv")
v2f = load(f"{RD}/fc_v2f_{TS}_stats.csv")

def table(title, a, la, b, lb, eps):
    print(f"\n{'═'*88}")
    print(f"  {title}")
    print(f"{'═'*88}")
    print(f"{'Эндпоинт':<32} {la:>12}                {lb:>12}")
    print(f"{'':32} {'RPS':>7} {'P50':>6} {'P95':>6}    {'RPS':>7} {'P50':>6} {'P95':>6}  Лучше")
    print(f"{'-'*88}")
    for na, nb, label in eps:
        ra = find(a, na); rb = find(b, nb)
        arps = float(ra.get('Requests/s',0)); brps = float(rb.get('Requests/s',0))
        win = f"{la[:7]}◀" if arps > brps else (f"{lb[:7]}▶" if brps > arps else "=")
        print(f"{label:<32} {fmt(arps):>7} {fmt(ra.get('50%','—'),'ms'):>6} {fmt(ra.get('95%','—'),'ms'):>6}    {fmt(brps):>7} {fmt(rb.get('50%','—'),'ms'):>6} {fmt(rb.get('95%','—'),'ms'):>6}  {win}")
    ag_a = find(a,"Aggregated"); ag_b = find(b,"Aggregated")
    print(f"{'-'*88}")
    print(f"{'ИТОГО':<32} {fmt(ag_a.get('Requests/s',0)):>7} {fmt(ag_a.get('50%','—'),'ms'):>6} {fmt(ag_a.get('95%','—'),'ms'):>6}    {fmt(ag_b.get('Requests/s',0)):>7} {fmt(ag_b.get('50%','—'),'ms'):>6} {fmt(ag_b.get('95%','—'),'ms'):>6}")

table(
    "СРАВНЕНИЕ 1 — v1 Django sync vs v1 FastAPI async",
    v1d, "Django sync", v1f, "FastAPI async",
    [
        ("GET /events/",        "GET /events/",        "GET /events/"),
        ("GET /events/{id}/",   "GET /events/{id}/",   "GET /events/{id}/"),
        ("GET /seats/",         "GET /seats/",         "GET /seats/"),
        ("POST /seats/reserve/","POST /seats/reserve/","POST /seats/reserve/"),
        ("GET /orders/",        "GET /orders/",        "GET /orders/"),
        ("GET /tickets/{id}/",  "GET /tickets/{id}/",  "GET /tickets/{id}/"),
    ]
)

table(
    "СРАВНЕНИЕ 2 — v1 FastAPI async vs v2 FastAPI async",
    v1f, "v1 FastAPI", v2f, "v2 FastAPI",
    [
        ("GET /events/",        "GET /events/",               "GET /events/"),
        ("GET /events/{id}/",   "GET /events/{id}/",          "GET /events/{id}/"),
        ("GET /seats/",         "GET /seats/",                "GET /seats/"),
        ("POST /seats/reserve/","POST /bookings/",            "POST /reserve → /bookings/"),
        ("GET /tickets/{id}/",  "GET /bookings/{id}/ticket",  "GET /tickets/"),
    ]
)

print(f"\n{'═'*60}")
print(f"  v2 Django sync :9202 — admin сервис")
print(f"{'═'*60}")
print(f"{'Эндпоинт':<38} {'RPS':>7} {'P50':>6} {'P95':>6}")
print(f"{'-'*60}")
for r in v2d:
    if r.get('Name') == 'Aggregated': continue
    print(f"{r.get('Name',''):<38} {fmt(r.get('Requests/s',0)):>7} {fmt(r.get('50%','—'),'ms'):>6} {fmt(r.get('95%','—'),'ms'):>6}")
ag = find(v2d,"Aggregated")
print(f"{'-'*60}")
print(f"{'ИТОГО':<38} {fmt(ag.get('Requests/s',0)):>7} {fmt(ag.get('50%','—'),'ms'):>6} {fmt(ag.get('95%','—'),'ms'):>6}")

# Собрать аргументы для PDF
args = []
for prefix, rows in [("d", v1d), ("f", v1f)]:
    for ep, name in [("events","GET /events/"), ("eventid","GET /events/{id}/"),
                     ("seats","GET /seats/"), ("reserve","POST /seats/reserve/"),
                     ("orders","GET /orders/"), ("ticket","GET /tickets/{id}/")]:
        for ci, m in [(RPS,"rps"),(P50,"p50"),(P95,"p95")]:
            args.append(f"--{prefix}-{ep}-{m}={g(rows, name, ci)}")
    ag = find(rows,"Aggregated"); vals = list(ag.values())
    for ci, m in [(RPS,"rps"),(P50,"p50"),(P95,"p95")]:
        try: args.append(f"--{prefix}-total-{m}={vals[ci].strip()}")
        except: args.append(f"--{prefix}-total-{m}=0")

for prefix, rows in [("v1", v1f), ("v2", v2f)]:
    for ep, name in [("events","GET /events/"), ("eventid","GET /events/{id}/"),
                     ("seats","GET /seats/"), ("ticket","GET /tickets/{id}/")]:
        for ci, m in [(RPS,"rps"),(P50,"p50"),(P95,"p95")]:
            args.append(f"--{prefix}-{ep}-{m}={g(rows, name, ci)}")
    for ep, name in [("reserve","POST /seats/reserve/"), ("bookings","POST /bookings/")]:
        for ci, m in [(RPS,"rps"),(P50,"p50"),(P95,"p95")]:
            args.append(f"--{prefix}-{ep}-{m}={g(rows, name, ci)}")
    if prefix == "v2":
        for ci, m in [(RPS,"rps"),(P50,"p50"),(P95,"p95")]:
            args.append(f"--v2-ticket-{m}={g(rows, 'GET /bookings/{id}/ticket', ci)}")
    ag = find(rows,"Aggregated"); vals = list(ag.values())
    for ci, m in [(RPS,"rps"),(P50,"p50"),(P95,"p95")]:
        try: args.append(f"--{prefix}-total-{m}={vals[ci].strip()}")
        except: args.append(f"--{prefix}-total-{m}=0")

args.append(f"--output={RD}/FINAL_{TS}.pdf")
with open('/tmp/final_pdf_args.txt','w') as f:
    f.write(' '.join(args))
print("\n✓ аргументы для PDF собраны")
PYEOF

# ── Генерация PDF ─────────────────────────────────────
echo ""
echo "▶ Генерация PDF отчёта..."
python3 /opt/hfbs-v2/scripts/generate_final_report.py \
    $(cat /tmp/final_pdf_args.txt)

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Готово!                                         ║"
echo "║  PDF: ${REPORT_DIR}/FINAL_${TIMESTAMP}.pdf"
echo "╚══════════════════════════════════════════════════╝"
