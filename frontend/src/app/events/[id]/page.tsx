"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Seat {
  id: number;
  row: string;
  number: number;
  price: number;
  status: "available" | "booked";
}

export default function EventDetailPage() {
  const params = useParams();
  const eventId = params.id;
  const [seats, setSeats] = useState<Seat[]>([]);
  const [selected, setSelected] = useState<Seat | null>(null);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState<"idle" | "loading" | "success" | "error" | "bot">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch(`/api/events/${eventId}/seats`)
      .then((r) => r.json())
      .then(setSeats)
      .catch(() => {
        // Мок данные
        const mock: Seat[] = [];
        ["A","B","C","D","E","F","G","H"].forEach(row => {
          for (let n = 1; n <= 20; n++) {
            mock.push({
              id: mock.length + 1,
              row, number: n,
              price: row <= "C" ? 15000 : row <= "F" ? 10000 : 5000,
              status: Math.random() > 0.3 ? "available" : "booked",
            });
          }
        });
        setSeats(mock);
      })
      .finally(() => setLoading(false));
  }, [eventId]);

  const rows = [...new Set(seats.map(s => s.row))].sort();

  const handleBook = async () => {
    if (!selected) return;
    setBooking("loading");
    try {
      const res = await fetch("/api/bookings/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: Number(eventId),
          seat_id: selected.id,
          user_id: "user-demo",
          user_email: "demo@example.com",
        }),
      });
      const data = await res.json();
      if (res.status === 429) {
        setBooking("bot");
        setMessage("Обнаружена подозрительная активность. Попробуйте позже.");
      } else if (res.status === 409) {
        setBooking("error");
        setMessage("Место уже занято. Выберите другое.");
      } else if (res.ok) {
        setBooking("success");
        setMessage(`Бронирование подтверждено! ID: ${data.booking_id}`);
        setSeats(prev => prev.map(s => s.id === selected.id ? {...s, status: "booked"} : s));
      } else {
        setBooking("error");
        setMessage(data.detail || "Ошибка бронирования");
      }
    } catch {
      setBooking("error");
      setMessage("Сервер недоступен");
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <Link href="/events" className="text-white/50 hover:text-white text-sm">← События</Link>
          <span className="text-white/20">/</span>
          <span className="text-white/70 text-sm">Выбор места</span>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-10 flex gap-8">
        {/* Seat map */}
        <div className="flex-1">
          <div className="text-center mb-6">
            <div className="inline-block bg-white/10 rounded-lg px-12 py-2 text-white/40 text-sm mb-6">
              СЦЕНА
            </div>
          </div>

          {loading ? (
            <div className="text-white/40 text-center py-20">Загрузка карты мест...</div>
          ) : (
            <div className="space-y-2">
              {rows.map(row => (
                <div key={row} className="flex items-center gap-2">
                  <span className="text-white/30 text-xs w-5 text-right">{row}</span>
                  <div className="flex gap-1 flex-wrap">
                    {seats.filter(s => s.row === row).sort((a,b) => a.number - b.number).map(seat => (
                      <button
                        key={seat.id}
                        disabled={seat.status === "booked"}
                        onClick={() => setSelected(seat)}
                        className={`w-7 h-7 rounded text-xs font-medium transition-all ${
                          seat.status === "booked"
                            ? "bg-white/10 text-white/20 cursor-not-allowed"
                            : selected?.id === seat.id
                            ? "bg-purple-500 text-white scale-110"
                            : "bg-white/20 hover:bg-purple-500/50 text-white/70 hover:text-white cursor-pointer"
                        }`}
                      >
                        {seat.number}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Legend */}
          <div className="flex gap-6 mt-6 text-sm text-white/40">
            <span className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-white/20 inline-block"/>Свободно</span>
            <span className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-purple-500 inline-block"/>Выбрано</span>
            <span className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-white/10 inline-block"/>Занято</span>
          </div>
        </div>

        {/* Booking panel */}
        <div className="w-72 shrink-0">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6 sticky top-6">
            <h3 className="font-semibold mb-4">Ваш выбор</h3>

            {selected ? (
              <>
                <div className="bg-white/5 rounded-xl p-4 mb-4">
                  <div className="text-white/50 text-sm">Место</div>
                  <div className="text-xl font-bold">Ряд {selected.row}, место {selected.number}</div>
                  <div className="text-purple-400 font-semibold mt-1">
                    {selected.price.toLocaleString()} ₸
                  </div>
                </div>

                {booking === "success" && (
                  <div className="bg-green-900/30 border border-green-700/30 rounded-xl p-3 mb-4 text-green-300 text-sm">
                    ✓ {message}
                  </div>
                )}
                {booking === "bot" && (
                  <div className="bg-red-900/30 border border-red-700/30 rounded-xl p-3 mb-4 text-red-300 text-sm">
                    🤖 {message}
                  </div>
                )}
                {booking === "error" && (
                  <div className="bg-amber-900/30 border border-amber-700/30 rounded-xl p-3 mb-4 text-amber-300 text-sm">
                    ⚠ {message}
                  </div>
                )}

                <button
                  onClick={handleBook}
                  disabled={booking === "loading" || booking === "success"}
                  className="w-full bg-purple-600 hover:bg-purple-500 disabled:bg-white/10 disabled:text-white/30 text-white py-3 rounded-xl font-medium transition-colors"
                >
                  {booking === "loading" ? "Бронируем..." : booking === "success" ? "Забронировано ✓" : "Забронировать"}
                </button>
              </>
            ) : (
              <div className="text-white/30 text-sm text-center py-8">
                Выберите место на карте
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
