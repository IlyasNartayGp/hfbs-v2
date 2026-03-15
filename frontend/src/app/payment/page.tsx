"use client";
import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";

function PaymentContent() {
  const params = useSearchParams();
  const router = useRouter();
  const bookingId = params.get("booking_id");
  const eventName = params.get("event") ?? "Мероприятие";
  const seat = params.get("seat") ?? "—";
  const price = params.get("price") ?? "5000";

  const [card, setCard] = useState({ number: "", expiry: "", cvv: "", name: "" });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const formatCard = (val: string) =>
    val.replace(/\D/g, "").slice(0, 16).replace(/(\d{4})/g, "$1 ").trim();

  const formatExpiry = (val: string) =>
    val.replace(/\D/g, "").slice(0, 4).replace(/(\d{2})(\d)/, "$1/$2");

  const handlePay = async () => {
    if (!card.number || !card.expiry || !card.cvv || !card.name) {
      setError("Заполните все поля");
      return;
    }
    setLoading(true);
    setError("");
    // Симуляция оплаты (в реальном проекте — интеграция с Kaspi/Stripe)
    await new Promise(r => setTimeout(r, 1500));
    setSuccess(true);
    setLoading(false);
  };

  if (success) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-6">🎉</div>
          <h1 className="text-3xl font-bold text-white mb-3">Оплата прошла!</h1>
          <p className="text-white/50 mb-2">Билет отправлен на ваш email.</p>
          <p className="text-white/30 text-sm mb-8">Номер брони: {bookingId}</p>
          <div className="flex gap-3 justify-center">
            <Link
              href="/profile"
              className="bg-purple-600 hover:bg-purple-500 text-white px-6 py-3 rounded-xl font-medium transition-colors"
            >
              Мои билеты
            </Link>
            <Link
              href="/events"
              className="border border-white/20 hover:border-white/40 text-white px-6 py-3 rounded-xl font-medium transition-colors"
            >
              К событиям
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <Link href="/events" className="text-white/50 hover:text-white text-sm">← Назад</Link>
          <span className="text-white/20">/</span>
          <span className="text-white/60 text-sm">Оплата</span>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-12 grid grid-cols-2 gap-8">
        {/* Order summary */}
        <div>
          <h2 className="text-xl font-bold mb-6">Ваш заказ</h2>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4">
            <div>
              <div className="text-white/40 text-sm">Мероприятие</div>
              <div className="font-semibold">{eventName}</div>
            </div>
            <div>
              <div className="text-white/40 text-sm">Место</div>
              <div className="font-semibold">{seat}</div>
            </div>
            <div>
              <div className="text-white/40 text-sm">Номер брони</div>
              <div className="font-mono text-sm text-white/60">{bookingId}</div>
            </div>
            <div className="border-t border-white/10 pt-4 flex justify-between items-center">
              <span className="text-white/60">Итого</span>
              <span className="text-2xl font-bold text-purple-400">
                {Number(price).toLocaleString()} ₸
              </span>
            </div>
          </div>

          <div className="mt-4 bg-green-900/20 border border-green-700/20 rounded-xl p-4 text-sm text-green-300">
            🔒 Место заблокировано на 10 минут. Оплатите сейчас.
          </div>
        </div>

        {/* Payment form */}
        <div>
          <h2 className="text-xl font-bold mb-6">Данные карты</h2>
          <div className="space-y-4">
            <div>
              <label className="text-white/60 text-sm block mb-1">Номер карты</label>
              <input
                type="text"
                placeholder="0000 0000 0000 0000"
                value={card.number}
                onChange={e => setCard(p => ({ ...p, number: formatCard(e.target.value) }))}
                className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors font-mono"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-white/60 text-sm block mb-1">Срок действия</label>
                <input
                  type="text"
                  placeholder="MM/YY"
                  value={card.expiry}
                  onChange={e => setCard(p => ({ ...p, expiry: formatExpiry(e.target.value) }))}
                  className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors font-mono"
                />
              </div>
              <div>
                <label className="text-white/60 text-sm block mb-1">CVV</label>
                <input
                  type="password"
                  placeholder="•••"
                  maxLength={3}
                  value={card.cvv}
                  onChange={e => setCard(p => ({ ...p, cvv: e.target.value.replace(/\D/g, "").slice(0, 3) }))}
                  className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors font-mono"
                />
              </div>
            </div>
            <div>
              <label className="text-white/60 text-sm block mb-1">Имя на карте</label>
              <input
                type="text"
                placeholder="IVAN IVANOV"
                value={card.name}
                onChange={e => setCard(p => ({ ...p, name: e.target.value.toUpperCase() }))}
                className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            {error && (
              <div className="bg-red-900/30 border border-red-700/30 rounded-xl p-3 text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handlePay}
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-500 disabled:bg-white/10 disabled:text-white/30 text-white py-4 rounded-xl font-bold text-lg transition-colors"
            >
              {loading ? "Обработка..." : `Оплатить ${Number(price).toLocaleString()} ₸`}
            </button>

            <p className="text-white/20 text-xs text-center">
              Тестовая оплата — реальные деньги не списываются
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function PaymentPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white/40">Загрузка...</div>
      </main>
    }>
      <PaymentContent />
    </Suspense>
  );
}
