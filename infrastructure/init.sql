-- Инициализация БД для HFBS v2

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    venue VARCHAR(255) NOT NULL,
    date TIMESTAMP NOT NULL,
    total_seats INT NOT NULL DEFAULT 100,
    available_seats INT NOT NULL DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seats (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id),
    row VARCHAR(5) NOT NULL,
    number INT NOT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 5000.00
);

CREATE TABLE IF NOT EXISTS bookings (
    id UUID PRIMARY KEY,
    event_id INT REFERENCES events(id),
    seat_id INT REFERENCES seats(id),
    user_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Тестовые данные
INSERT INTO events (name, venue, date, total_seats, available_seats) VALUES
    ('Imagine Dragons — Almaty Tour', 'Barys Arena, Алматы', '2025-06-15 20:00:00', 500, 500),
    ('Dimash World Tour 2025', 'Almaty Arena', '2025-07-20 19:00:00', 1000, 1000),
    ('Comedy Club Astana', 'Congress Hall, Астана', '2025-05-10 18:00:00', 200, 200)
ON CONFLICT DO NOTHING;

-- Генерация мест для всех событий
INSERT INTO seats (event_id, row, number, price)
SELECT e.id, chr(64 + row_num), seat_num,
    CASE WHEN row_num <= 5 THEN 15000 WHEN row_num <= 10 THEN 10000 ELSE 5000 END
FROM events e,
     generate_series(1, 20) row_num,
     generate_series(1, 25) seat_num
ON CONFLICT DO NOTHING;

-- Индексы для производительности (важно для нагрузочных тестов!)
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_event_seat ON bookings(event_id, seat_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_seats_event_id ON seats(event_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Демо пользователь (пароль: demo1234)
INSERT INTO users (id, email, name, password_hash) VALUES
    ('00000000-0000-0000-0000-000000000001',
     'demo@hfbs.kz',
     'Демо Пользователь',
     '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW')
ON CONFLICT DO NOTHING;
