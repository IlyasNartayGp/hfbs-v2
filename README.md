# HFBS v2 — High-Frequency Booking System

Дипломный проект. Микросервисная архитектура с тремя сервисами.

## Архитектура

```
Client → Nginx → Frontend (Next.js)
              → FastAPI  (async, бронирование)
              → Django   (sync, PDF + admin)
              → Antifrod (ML, защита от ботов)

FastAPI / Django → PostgreSQL
FastAPI / Antifrod → Redis
Django → RabbitMQ → Celery Worker
```

## Запуск

```bash
# Клонируем и запускаем
cd /opt/hfbs-v2
docker-compose up --build -d

# Инициализация БД
docker-compose exec postgres psql -U hfbs -d hfbs -f /docker-entrypoint-initdb.d/init.sql
```

## Сервисы

| Сервис     | Порт  | Описание                        |
|------------|-------|---------------------------------|
| Frontend   | 3737  | Next.js + Tailwind + shadcn     |
| Nginx      | 8880  | API Gateway                     |
| FastAPI    | 9101  | Async бронирование              |
| Django     | 9202  | Sync PDF генерация + admin      |
| Antifrod   | 9303  | ML антифрод (sklearn RF)        |
| PostgreSQL | 6543  | Основная БД                     |
| Redis      | 6380  | Locks + cache                   |
| RabbitMQ   | 15892 | Очередь (UI на 15892)           |

## Для диплома

- **Старый проект** `/opt/hfbs` — сравнение sync vs async
- **Этот проект** `/opt/hfbs-v2` — полная микросервисная архитектура

### Нагрузочные тесты (Locust)

```bash
cd scripts
locust -f locustfile.py --host=http://localhost
```
