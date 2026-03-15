"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

interface Event {
  id: number;
  name: string;
  venue: string;
  date: string;
  total_seats: number;
  available_seats: number;
}

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/events/")
      .then((r) => r.json())
      .then(setEvents)
      .catch(() =>
        setEvents([
          { id: 1, name: "Imagine Dragons — Almaty Tour", venue: "Barys Arena, Алматы", date: "2025-06-15T20:00:00", total_seats: 500, available_seats: 342 },
          { id: 2, name: "Dimash World Tour 2025", venue: "Almaty Arena", date: "2025-07-20T19:00:00", total_seats: 1000, available_seats: 871 },
          { id: 3, name: "Comedy Club Astana", venue: "Congress Hall, Астана", date: "2025-05-10T18:00:00", total_seats: 200, available_seats: 55 },
        ])
      )
      .finally(() => setLoading(false));
  }, []);

  const availabilityColor = (avail: number, total: number) => {
    const pct = avail / total;
    if (pct > 0.5) return "text-green-400";
    if (pct > 0.2) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="text-white font-bold text-xl">🎟 HFBS</Link>
          <Link href="/dashboard" className="text-white/60 hover:text-white text-sm transition-colors">
            Antifrod Dashboard
          </Link>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold mb-8">Предстоящие события</h1>

        {loading ? (
          <div className="text-white/40 text-center py-20">Загрузка...</div>
        ) : (
          <div className="grid gap-4">
            {events.map((event) => (
              <Link href={`/events/${event.id}`} key={event.id}>
                <div className="bg-white/5 hover:bg-white/8 border border-white/10 hover:border-purple-500/40 rounded-2xl p-6 transition-all cursor-pointer group">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-xl font-semibold group-hover:text-purple-300 transition-colors">
                        {event.name}
                      </h2>
                      <p className="text-white/50 mt-1">{event.venue}</p>
                      <p className="text-white/40 text-sm mt-1">
                        {new Date(event.date).toLocaleString("ru-RU", {
                          day: "numeric", month: "long", year: "numeric",
                          hour: "2-digit", minute: "2-digit",
                        })}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${availabilityColor(event.available_seats, event.total_seats)}`}>
                        {event.available_seats}
                      </div>
                      <div className="text-white/40 text-sm">из {event.total_seats} мест</div>
                    </div>
                  </div>

                  <div className="mt-4 bg-white/5 rounded-full h-1.5">
                    <div
                      className="bg-purple-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${((event.total_seats - event.available_seats) / event.total_seats) * 100}%` }}
                    />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
