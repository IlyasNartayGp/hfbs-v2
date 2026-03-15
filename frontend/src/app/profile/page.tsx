"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

interface Booking {
  id: string;
  event_name: string;
  venue: string;
  date: string;
  row: string;
  number: number;
  price: number;
  status: string;
  created_at: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"tickets" | "info">("tickets");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }

    const headers = { Authorization: `Bearer ${token}` };

    Promise.all([
      fetch("/api/auth/me", { headers }).then(r => r.json()),
      fetch("/api/auth/me/bookings", { headers }).then(r => r.json()),
    ])
      .then(([u, b]) => {
        setUser(u);
        setBookings(Array.isArray(b) ? b : []);
      })
      .catch(() => {
        // Мок данные для демо
        setUser({ id: "1", email: "demo@example.com", name: "Демо Пользователь", created_at: new Date().toISOString() });
        setBookings([
          { id: "abc-123", event_name: "Imagine Dragons — Almaty Tour", venue: "Barys Arena", date: "2025-06-15T20:00:00", row: "C", number: 14, price: 15000, status: "confirmed", created_at: new Date().toISOString() },
          { id: "def-456", event_name: "Dimash World Tour 2025", venue: "Almaty Arena", date: "2025-07-20T19:00:00", row: "F", number: 7, price: 10000, status: "confirmed", created_at: new Date().toISOString() },
        ]);
      })
      .finally(() => setLoading(false));
  }, [router]);

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      confirmed: "bg-green-900/50 text-green-300",
      pending:   "bg-amber-900/50 text-amber-300",
      cancelled: "bg-red-900/50 text-red-300",
    };
    return map[status] ?? "bg-white/10 text-white/50";
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white/40">Загрузка...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="text-white font-bold text-xl">🎟 HFBS</Link>
          <div className="flex items-center gap-4">
            <span className="text-white/50 text-sm">{user?.email}</span>
            <button onClick={logout} className="text-white/40 hover:text-white text-sm transition-colors">
              Выйти
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Profile header */}
        <div className="flex items-center gap-5 mb-8">
          <div className="w-16 h-16 rounded-full bg-purple-600/30 border border-purple-500/30 flex items-center justify-center text-2xl font-bold text-purple-300">
            {user?.name?.[0]?.toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{user?.name}</h1>
            <p className="text-white/40 text-sm">{user?.email}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white/5 rounded-xl p-1 w-fit mb-8">
          {(["tickets", "info"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === t ? "bg-purple-600 text-white" : "text-white/50 hover:text-white"
              }`}
            >
              {t === "tickets" ? `Мои билеты (${bookings.length})` : "Профиль"}
            </button>
          ))}
        </div>

        {tab === "tickets" ? (
          bookings.length === 0 ? (
            <div className="text-center py-20 text-white/30">
              <div className="text-5xl mb-4">🎟</div>
              <p>У вас пока нет билетов</p>
              <Link href="/events" className="text-purple-400 hover:text-purple-300 text-sm mt-2 inline-block">
                Посмотреть события →
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {bookings.map(b => (
                <div key={b.id} className="bg-white/5 border border-white/10 rounded-2xl p-5 flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="font-semibold">{b.event_name}</h3>
                    <p className="text-white/40 text-sm">{b.venue}</p>
                    <p className="text-white/30 text-sm">
                      {new Date(b.date).toLocaleString("ru-RU", { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                  <div className="text-center shrink-0">
                    <div className="text-lg font-bold">Ряд {b.row}, №{b.number}</div>
                    <div className="text-purple-400 font-semibold text-sm">{Number(b.price).toLocaleString()} ₸</div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusBadge(b.status)}`}>
                      {b.status === "confirmed" ? "Подтверждён" : b.status === "pending" ? "Ожидает" : "Отменён"}
                    </span>
                    <a
                      href={`/api/tickets/${b.id}/download/`}
                      className="text-white/40 hover:text-white text-xs transition-colors"
                    >
                      📥 PDF
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6 max-w-md space-y-4">
            <h2 className="font-semibold mb-2">Информация об аккаунте</h2>
            {[
              { label: "Имя", value: user?.name },
              { label: "Email", value: user?.email },
              { label: "Регистрация", value: user?.created_at ? new Date(user.created_at).toLocaleDateString("ru-RU") : "—" },
              { label: "Билетов", value: String(bookings.length) },
            ].map(row => (
              <div key={row.label} className="flex justify-between">
                <span className="text-white/40 text-sm">{row.label}</span>
                <span className="text-sm">{row.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
