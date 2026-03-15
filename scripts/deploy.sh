#!/bin/bash
# Скрипт деплоя hfbs-v2 на сервер
set -e

echo "=== HFBS v2 Deploy ==="

docker-compose down --remove-orphans 2>/dev/null || true

echo "Building containers..."
docker-compose up --build -d

echo "Waiting for PostgreSQL..."
sleep 12

echo "Initializing database..."
docker-compose exec -T postgres psql -U hfbs -d hfbs -f /docker-entrypoint-initdb.d/init.sql 2>/dev/null || \
docker-compose exec -T postgres psql -U hfbs -d hfbs < infrastructure/init.sql || true

echo "Running Django migrations..."
docker-compose exec -T django python manage.py migrate || true

echo "Creating Django superuser..."
docker-compose exec -T django python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@hfbs.kz', 'admin1234')
    print('Superuser created: admin / admin1234')
else:
    print('Superuser already exists')
" || true

echo "Installing locust for load tests..."
pip install locust --quiet 2>/dev/null || true

echo ""
echo "=== Готово! ==="
echo ""
echo "  Сайт:         http://localhost:8880"
echo "  FastAPI docs: http://localhost:9101/docs"
echo "  Django admin: http://localhost:9202/admin  (admin / admin1234)"
echo "  Antifrod:     http://localhost:9303/docs"
echo "  RabbitMQ UI:  http://localhost:15892       (guest / guest)"
echo "  PostgreSQL:   localhost:6543"
echo "  Redis:        localhost:6380"
echo ""
echo "  Нагрузочные тесты:"
echo "  cd scripts && locust -f locustfile.py --host=http://localhost:8880"
echo ""
echo "  Демо аккаунт: demo@hfbs.kz / demo1234"
