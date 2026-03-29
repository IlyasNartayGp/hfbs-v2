"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Calendar, MapPin } from "lucide-react";

interface Event {
  id: number;
  name: string;
  venue: string;
  date: string;
  total_seats: number;
  available_seats: number;
}

function availability(avail: number, total: number) {
  const pct = avail / total;
  if (pct > 0.5)  return { color: "text-emerald-400", label: "Много мест" };
  if (pct > 0.15) return { color: "text-amber-400",   label: "Мало мест" };
  return           { color: "text-red-400",            label: "Почти нет" };
}

export default function EventsPage() {
  const [events, setEvents]   = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const [error, setError]     = useState("");

  useEffect(() => {
    fetch("/api/events/")
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json(); })
      .then(setEvents)
      .catch(e => setError("Не удалось загрузить события: " + e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = events.filter(e =>
    e.name.toLowerCase().includes(search.toLowerCase()) ||
    e.venue.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">События</h1>
        <input
          type="text"
          placeholder="Поиск по названию или месту..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="input w-64"
        />
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-800/30 rounded-xl px-4 py-3 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-3">
          {[1,2,3].map(i => <div key={i} className="h-24 bg-white/5 rounded-2xl animate-pulse" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-white/30 text-center py-20">
          {search ? "Ничего не найдено" : "Нет доступных событий"}
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map(event => {
            const avail = availability(event.available_seats, event.total_seats);
            const date  = new Date(event.date);
            return (
              <Link key={event.id} href={`/events/${event.id}`}>
                <div className="group bg-white/5 hover:bg-white/10 border border-white/10 hover:border-violet-500/30 rounded-2xl p-5 transition-all flex items-center gap-6">
                  {/* Date badge */}
                  <div className="shrink-0 w-14 text-center bg-violet-950/60 border border-violet-800/30 rounded-xl py-2">
                    <div className="text-violet-400 text-xs uppercase">
                      {date.toLocaleString("ru", { month: "short" })}
                    </div>
                    <div className="text-white font-bold text-xl leading-none">
                      {date.getDate()}
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-white group-hover:text-violet-300 transition-colors truncate">
                      {event.name}
                    </p>
                    <div className="flex items-center gap-4 mt-1.5 text-white/40 text-sm">
                      <span className="flex items-center gap-1">
                        <MapPin size={12} /> {event.venue}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar size={12} />
                        {date.toLocaleString("ru", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  </div>

                  {/* Seats */}
                  <div className="shrink-0 text-right">
                    <div className={`text-lg font-bold ${avail.color}`}>
                      {event.available_seats}
                    </div>
                    <div className="text-white/30 text-xs">из {event.total_seats}</div>
                    <div className={`text-xs mt-0.5 ${avail.color}`}>{avail.label}</div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </main>
  );
}
