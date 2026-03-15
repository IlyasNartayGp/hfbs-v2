import os
import pickle
import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)


# Известные User-Agent строки ботов
BOT_UA_SIGNATURES = [
    "python-requests", "curl", "wget", "httpx", "aiohttp",
    "scrapy", "selenium", "playwright", "puppeteer",
    "bot", "crawler", "spider", "headless",
]

# Известные подозрительные ASN/IP диапазоны (примеры)
SUSPICIOUS_IP_PREFIXES = [
    "185.220.", "185.100.", "162.247.", "171.25.",
    "199.87.", "193.169.", "198.98.",
]


class AntifrodModel:
    """
    Antifrod ML модель для HFBS v2.

    Алгоритм: RandomForest + GradientBoosting (ансамбль).
    Фичи: поведенческие + технические + временные паттерны.

    Пороги:
        > 0.80 — точно бот, блокируем
        0.50-0.80 — подозрительно, ставим капчу (TODO)
        < 0.50 — человек, пропускаем

    Для диплома:
        Метрики модели печатаются при обучении — использовать в главе 3.
    """

    FEATURE_NAMES = [
        # Поведенческие фичи
        "requests_per_minute",       # кол-во запросов с IP за 60 сек
        "seat_attempts",             # попыток на одно место
        "unique_seats_tried",        # сколько разных мест пробовал
        "session_duration_sec",      # время с первого запроса сессии
        # Технические фичи
        "has_user_agent",            # есть ли User-Agent вообще
        "is_known_bot_ua",           # совпадает с известными bot UA
        "is_suspicious_ip",          # IP из подозрительных диапазонов
        # Временные фичи
        "secs_after_sale_open",      # секунд прошло с открытия продаж
        "hour_of_day",               # час суток (боты часто ночью)
        # Финансовые фичи
        "avg_price_targeted",        # средняя цена мест которые пробовал
        "always_front_row",          # всегда целится в дорогие места
    ]

    MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/antifrod_model.pkl")
    BOT_THRESHOLD = 0.80
    SUSPICIOUS_THRESHOLD = 0.50

    def __init__(self):
        self.metrics: dict = {}
        if os.path.exists(self.MODEL_PATH):
            self._load()
        else:
            print("Модель не найдена, обучаем на синтетических данных...")
            X, y = self._generate_dataset(n=5000)
            self._train(X, y)
            self._save()

    # ──────────────────────────────────────────────
    # Генерация синтетических данных
    # ──────────────────────────────────────────────
    def _generate_dataset(self, n: int = 5000):
        """
        Генерируем реалистичные синтетические данные.
        3 типа акторов: обычные люди, скальперы-боты, медленные боты.
        """
        np.random.seed(42)
        half = n // 3

        # 1. Обычные люди
        humans = np.column_stack([
            np.random.randint(1, 8, half),           # requests_per_minute
            np.random.randint(1, 3, half),            # seat_attempts
            np.random.randint(1, 4, half),            # unique_seats_tried
            np.random.uniform(10, 600, half),         # session_duration_sec
            np.ones(half),                             # has_user_agent
            np.zeros(half),                            # is_known_bot_ua
            np.zeros(half),                            # is_suspicious_ip
            np.random.uniform(30, 500, half),          # secs_after_sale_open
            np.random.randint(8, 23, half),            # hour_of_day
            np.random.uniform(3000, 15000, half),      # avg_price_targeted
            np.zeros(half),                            # always_front_row
        ])
        y_humans = np.zeros(half)

        # 2. Быстрые скальперы-боты
        fast_bots = np.column_stack([
            np.random.randint(60, 200, half),         # много запросов
            np.random.randint(10, 50, half),           # много попыток
            np.random.randint(5, 30, half),            # много разных мест
            np.random.uniform(0.1, 5, half),           # очень короткая сессия
            np.random.choice([0, 1], half, p=[0.4, 0.6]),
            np.random.choice([0, 1], half, p=[0.2, 0.8]),  # часто bot UA
            np.random.choice([0, 1], half, p=[0.3, 0.7]),  # часто suspicious IP
            np.random.uniform(0, 3, half),             # сразу после открытия
            np.random.randint(0, 24, half),            # любое время
            np.random.uniform(10000, 15000, half),     # только дорогие
            np.ones(half),                             # always_front_row=1
        ])
        y_fast_bots = np.ones(half)

        # 3. Медленные боты (сложнее поймать)
        slow_bots = np.column_stack([
            np.random.randint(10, 25, half),          # умеренные запросы
            np.random.randint(3, 8, half),             # умеренные попытки
            np.random.randint(3, 10, half),            # несколько мест
            np.random.uniform(2, 30, half),            # короткая сессия
            np.ones(half),                             # есть UA (маскируются)
            np.random.choice([0, 1], half, p=[0.6, 0.4]),
            np.random.choice([0, 1], half, p=[0.5, 0.5]),
            np.random.uniform(0, 15, half),            # быстро после открытия
            np.random.choice([1, 2, 3, 23, 0], half), # ночное время
            np.random.uniform(8000, 15000, half),      # дорогие места
            np.random.choice([0, 1], half, p=[0.3, 0.7]),
        ])
        y_slow_bots = np.ones(half)

        X = np.vstack([humans, fast_bots, slow_bots])
        y = np.concatenate([y_humans, y_fast_bots, y_slow_bots])
        return X, y

    # ──────────────────────────────────────────────
    # Обучение ансамбля
    # ──────────────────────────────────────────────
    def _train(self, X: np.ndarray, y: np.ndarray):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.scaler = StandardScaler()
        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        # Основная модель — RandomForest
        self.rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        self.rf.fit(X_train_s, y_train)

        # Вспомогательная — GradientBoosting (для ансамбля)
        self.gb = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )
        self.gb.fit(X_train_s, y_train)

        # Ансамбль: среднее вероятностей
        rf_proba = self.rf.predict_proba(X_test_s)[:, 1]
        gb_proba = self.gb.predict_proba(X_test_s)[:, 1]
        ensemble_proba = (rf_proba + gb_proba) / 2
        ensemble_pred = (ensemble_proba >= self.BOT_THRESHOLD).astype(int)

        # Метрики
        self.metrics = {
            "accuracy":  round(accuracy_score(y_test, ensemble_pred), 4),
            "precision": round(precision_score(y_test, ensemble_pred), 4),
            "recall":    round(recall_score(y_test, ensemble_pred), 4),
            "f1":        round(f1_score(y_test, ensemble_pred), 4),
            "roc_auc":   round(roc_auc_score(y_test, ensemble_proba), 4),
            "confusion_matrix": confusion_matrix(y_test, ensemble_pred).tolist(),
            "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "features": self.FEATURE_NAMES,
        }

        # Feature importance (только RF)
        importances = self.rf.feature_importances_
        self.metrics["feature_importance"] = {
            name: round(float(imp), 4)
            for name, imp in sorted(
                zip(self.FEATURE_NAMES, importances),
                key=lambda x: x[1], reverse=True
            )
        }

        print("\n=== Antifrod Model Metrics ===")
        print(f"  Accuracy:  {self.metrics['accuracy']}")
        print(f"  Precision: {self.metrics['precision']}")
        print(f"  Recall:    {self.metrics['recall']}")
        print(f"  F1 Score:  {self.metrics['f1']}")
        print(f"  ROC-AUC:   {self.metrics['roc_auc']}")
        print(f"  Confusion Matrix: {self.metrics['confusion_matrix']}")
        print("==============================\n")

    # ──────────────────────────────────────────────
    # Предсказание
    # ──────────────────────────────────────────────
    def predict(self, features: dict) -> tuple[bool, float, str]:
        """
        Возвращает (is_bot, confidence, verdict)
        verdict: 'blocked' | 'suspicious' | 'allowed'
        """
        X = np.array([[features.get(f, 0) for f in self.FEATURE_NAMES]])
        X_scaled = self.scaler.transform(X)

        rf_proba = self.rf.predict_proba(X_scaled)[0][1]
        gb_proba = self.gb.predict_proba(X_scaled)[0][1]
        confidence = round(float((rf_proba + gb_proba) / 2), 4)

        if confidence >= self.BOT_THRESHOLD:
            return True, confidence, "blocked"
        elif confidence >= self.SUSPICIOUS_THRESHOLD:
            return False, confidence, "suspicious"
        else:
            return False, confidence, "allowed"

    # ──────────────────────────────────────────────
    # Переобучение на новых данных (online learning)
    # ──────────────────────────────────────────────
    def retrain(self, new_X: list, new_y: list) -> dict:
        """
        Дообучение модели на новых размеченных данных.
        Вызывается через API /api/antifrod/retrain
        """
        X_new = np.array(new_X)
        y_new = np.array(new_y)

        # Добавляем синтетические данные чтобы не забыть старое
        X_base, y_base = self._generate_dataset(n=2000)
        X_combined = np.vstack([X_base, X_new])
        y_combined = np.concatenate([y_base, y_new])

        self._train(X_combined, y_combined)
        self._save()
        return self.metrics

    # ──────────────────────────────────────────────
    # Утилиты
    # ──────────────────────────────────────────────
    @staticmethod
    def extract_features(
        ip: str,
        user_agent: str,
        requests_count: int,
        seat_attempts: int,
        unique_seats: int,
        session_start: float,
        sale_open_time: float,
        avg_price: float = 5000.0,
        front_row_count: int = 0,
        total_attempts: int = 1,
    ) -> dict:
        """
        Хелпер — формирует словарь фичей из сырых данных запроса.
        Используется в antifrod/app/main.py
        """
        now = time.time()
        return {
            "requests_per_minute": requests_count,
            "seat_attempts": seat_attempts,
            "unique_seats_tried": unique_seats,
            "session_duration_sec": now - session_start,
            "has_user_agent": int(bool(user_agent and len(user_agent) > 5)),
            "is_known_bot_ua": int(any(
                sig in user_agent.lower() for sig in BOT_UA_SIGNATURES
            )),
            "is_suspicious_ip": int(any(
                ip.startswith(prefix) for prefix in SUSPICIOUS_IP_PREFIXES
            )),
            "secs_after_sale_open": now - sale_open_time,
            "hour_of_day": int(time.strftime("%H")),
            "avg_price_targeted": avg_price,
            "always_front_row": int(
                front_row_count > 0 and front_row_count == total_attempts
            ),
        }

    def _save(self):
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({
                "rf": self.rf,
                "gb": self.gb,
                "scaler": self.scaler,
                "metrics": self.metrics,
            }, f)
        print(f"Модель сохранена: {self.MODEL_PATH}")

    def _load(self):
        with open(self.MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        self.rf = data["rf"]
        self.gb = data["gb"]
        self.scaler = data["scaler"]
        self.metrics = data.get("metrics", {})
        print(f"Модель загружена: {self.MODEL_PATH}")
        if self.metrics:
            print(f"  F1={self.metrics.get('f1')} ROC-AUC={self.metrics.get('roc_auc')}")
