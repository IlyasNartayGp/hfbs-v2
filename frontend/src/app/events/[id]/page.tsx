"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useStore } from "@/store";
import { Clock, CreditCard, MapPin, Calendar } from "lucide-react";

interface Seat {
  id: number;
  row: string;
  number: number;
  price: number;
  status: "available" | "booked";
  category?: string;
}

interface EventInfo {
  id: number;
  name: string;
  venue: string;
  date: string;
  total_seats: number;
  available_seats: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  vip:      "bg-amber-500/70 hover:bg-amber-400/90",
  standard: "bg-violet-500/70 hover:bg-violet-400/90",
  economy:  "bg-slate-500/60 hover:bg-slate-400/80",
};

function getCategory(price: number): string {
  if (price >= 15000) return "vip";
  if (price >= 10000) return "standard";
  return "economy";
}

export default function EventDetailPage() {
  const params  = useParams();
  const router  = useRouter();
  const eventId = Number(params.id);
  const { user, setSelectedSeat, setBookingId, setCurrentEventId } = useStore();

  const [event,    setEvent]    = useState<EventInfo | null>(null);
  const [seats,    setSeats]    = useState<Seat[]>([]);
  const [selected, setSelected] = useState<Seat | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [status,   setStatus]   = useState<"idle"|"loading"|"success"|"error"|"bot">("idle");
  const [msg,      setMsg]      = useState("");
  const [ttl,      setTtl]      = useState(600);

  useEffect(() => {
    setCurrentEventId(eventId);
    Promise.all([
      fetch(`/api/events/${eventId}`).then(r => r.ok ? r.json() : null),
      fetch(`/api/events/${eventId}/seats`).then(r => r.ok ? r.json() : []),
    ])
      .then(([ev, st]) => {
        if (ev) setEvent(ev);
        if (Array.isArray(st)) setSeats(st);
        else setError("Не удалось загрузить места");
      })
      .catch(() => setError("Сервер недоступен"))
      .finally(() => setLoading(false));
  }, [eventId]);

  // Countdown таймер
  useEffect(() => {
    if (!selected || status !== "idle") return;
    setTtl(600);
    const t = setInterval(() => setTtl(p => p <= 1 ? (clearInterval(t), 0) : p - 1), 1000);
    return () => clearInterval(t);
  }, [selected?.id]);

  const rows = [...new Set(seats.map(s => s.row))].sort();
  const fmt  = (s: number) => `${Math.floor(s/60)}:${String(s%60).padStart(2,"0")}`;

  const handleBook = async () => {
    if (!selected) return;
    setStatus("loading");
    try {
      const res  = await fetch("/api/bookings/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: eventId,
          seat_id:  selected.id,
          user_id:  user?.id ?? "guest",
        }),
      });
      const data = await res.json();
      if (res.status === 429) {
        setStatus("bot");   setMsg("Подозрительная активность. Подождите.");
      } else if (res.status === 409) {
        setStatus("error"); setMsg("Место уже занято. Выберите другое.");
      } else if (res.ok) {
        setBookingId(data.booking_id);
        setSelectedSeat(selected);
        setStatus("success");
        setSeats(p => p.map(s => s.id === selected.id ? {...s, status: "booked"} : s));
        setTimeout(() => router.push(
          `/payment?booking_id=${data.booking_id}&price=${selected.price}&seat=${selected.row}${selected.number}&event_id=${eventId}`
        ), 700);
      } else {
        setStatus("error"); setMsg(data.detail ?? "Ошибка бронирования");
      }
    } catch {
      setStatus("error"); setMsg("Сервер недоступен");
    }
  };

  return (
    <main className="max-w-6xl mx-auto px-6 py-10">
      {/* Event header */}
      {event && (
        <div className="mb-8 pb-6 border-b border-white/10">
          <h1 className="text-2xl font-bold text-white mb-2">{event.name}</h1>
          <div className="flex items-center gap-5 text-white/40 text-sm">
            <span className="flex items-center gap-1.5">
              <MapPin size={13} /> {event.venue}
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar size={13} />
              {new Date(event.date).toLocaleString("ru", {
                day: "numeric", month: "long", year: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
            </span>
          </div>
        </div>
      )}

      <div className="flex gap-8">
        {/* Seat map */}
        <div className="flex-1">
          <div className="text-center mb-8">
            <div className="inline-block bg-white/5 border border-white/10 rounded-lg px-20 py-2 text-white/25 text-xs tracking-widest uppercase">
              Сцена
            </div>
          </div>

          {loading ? (
            <div className="space-y-2">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-7 bg-white/5 rounded animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="bg-red-950/40 border border-red-800/30 rounded-xl px-4 py-3 text-red-300 text-sm">
              {error}
            </div>
          ) : (
            <div className="space-y-1.5">
              {rows.map(row => (
                <div key={row} className="flex items-center gap-2">
                  <span className="text-white/20 text-xs w-4 text-right shrink-0">{row}</span>
                  <div className="flex gap-1 flex-wrap">
                    {seats
                      .filter(s => s.row === row)
                      .sort((a,b) => a.number - b.number)
                      .map(seat => {
                        const isSelected = selected?.id === seat.id;
                        const isBooked   = seat.status === "booked";
                        const cat        = getCategory(seat.price);
                        return (
                          <button
                            key={seat.id}
                            disabled={isBooked}
                            onClick={() => { setSelected(seat); setStatus("idle"); }}
                            title={`Ряд ${seat.row}, место ${seat.number} — ${seat.price.toLocaleString()} ₸`}
                            className={`w-6 h-6 rounded text-xs transition-all ${
                              isBooked
                                ? "bg-white/10 cursor-not-allowed"
                                : isSelected
                                ? "bg-white scale-110 shadow-lg shadow-white/20"
                                : `${CATEGORY_COLORS[cat]} cursor-pointer`
                            }`}
                          />
                        );
                      })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Legend */}
          {!loading && !error && (
            <div className="flex gap-5 mt-6 text-xs text-white/35">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-500/70 inline-block"/>VIP · 15 000 ₸</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-violet-500/70 inline-block"/>Стандарт · 10 000 ₸</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-slate-500/60 inline-block"/>Эконом · 5 000 ₸</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-white/10 inline-block"/>Занято</span>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="w-64 shrink-0 space-y-3">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wide mb-4">
              Ваш выбор
            </h3>

            {selected ? (
              <>
                <div className="mb-4">
                  <div className="text-2xl font-bold text-white">
                    Ряд {selected.row} · {selected.number}
                  </div>
                  <div className="text-violet-400 font-semibold text-lg mt-1">
                    {selected.price.toLocaleString()} ₸
                  </div>
                  <div className="text-white/30 text-xs mt-1">
                    {getCategory(selected.price) === "vip" ? "VIP" :
                     getCategory(selected.price) === "standard" ? "Стандарт" : "Эконом"}
                  </div>
                </div>

                {status === "idle" && ttl > 0 && (
                  <div className="flex items-center gap-2 text-xs text-white/25 mb-4">
                    <Clock size={11} />
                    <span>Резерв на {fmt(ttl)}</span>
                  </div>
                )}

                {status === "success" && (
                  <div className="bg-emerald-950/50 border border-emerald-800/30 rounded-xl p-3 mb-4 text-emerald-300 text-xs">
                    ✓ Подтверждено, переходим к оплате...
                  </div>
                )}
                {status === "bot" && (
                  <div className="bg-red-950/50 border border-red-800/30 rounded-xl p-3 mb-4 text-red-300 text-xs">
                    🤖 {msg}
                  </div>
                )}
                {status === "error" && (
                  <div className="bg-amber-950/50 border border-amber-800/30 rounded-xl p-3 mb-4 text-amber-300 text-xs">
                    ⚠ {msg}
                  </div>
                )}

                <button
                  onClick={handleBook}
                  disabled={status === "loading" || status === "success"}
                  className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-white/10 disabled:text-white/20 text-white py-3 rounded-xl font-medium transition-colors text-sm"
                >
                  <CreditCard size={14} />
                  {status === "loading" ? "Бронируем..." :
                   status === "success"  ? "Переходим..." : "Забронировать"}
                </button>
              </>
            ) : (
              <div className="text-white/20 text-sm text-center py-10">
                Нажмите на место на карте
              </div>
            )}
          </div>

          {/* Stats */}
          {!loading && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-4 text-xs text-white/35 space-y-2">
              <div className="flex justify-between">
                <span>Свободно</span>
                <span className="text-emerald-400">{seats.filter(s => s.status === "available").length}</span>
              </div>
              <div className="flex justify-between">
                <span>Занято</span>
                <span className="text-red-400">{seats.filter(s => s.status === "booked").length}</span>
              </div>
              <div className="flex justify-between">
                <span>Всего</span>
                <span className="text-white/50">{seats.length}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
