import Link from "next/link";
import { ArrowRight, Zap, Shield, Ticket } from "lucide-react";

async function getEvents() {
  try {
    const res = await fetch("http://fastapi:8001/api/events/", {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

const TAG_COLORS: Record<string, string> = {
  "Barys Arena":        "from-violet-900 to-indigo-900",
  "Almaty Arena":       "from-rose-900 to-purple-900",
  "Congress Hall":      "from-amber-900 to-orange-900",
  "default":            "from-slate-800 to-slate-900",
};

export default async function HomePage() {
  const events = await getEvents();

  return (
    <main>
      {/* Hero */}
      <section className="bg-gradient-to-b from-violet-950/50 to-slate-950">
        <div className="max-w-6xl mx-auto px-6 py-24 text-center">
          <p className="text-violet-400 text-xs font-semibold tracking-widest uppercase mb-5">
            Система бронирования
          </p>
          <h1 className="text-5xl font-bold text-white mb-5 leading-tight">
            Билеты на лучшие события
          </h1>
          <p className="text-white/50 text-lg mb-10 max-w-xl mx-auto">
            Быстрое бронирование, защита от ботов в реальном времени
          </p>
          <Link
            href="/events"
            className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white px-8 py-3.5 rounded-xl font-semibold transition-colors"
          >
            Все события <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* Events from API */}
      {events.length > 0 && (
        <section className="max-w-6xl mx-auto px-6 pb-16">
          <h2 className="text-lg font-semibold text-white/70 mb-5">Ближайшие события</h2>
          <div className="grid grid-cols-3 gap-4">
            {events.slice(0, 3).map((e: any) => {
              const gradientKey = Object.keys(TAG_COLORS).find(k => e.venue?.includes(k)) ?? "default";
              const gradient = TAG_COLORS[gradientKey];
              const date = new Date(e.date);
              const avail = e.available_seats / e.total_seats;
              return (
                <Link key={e.id} href={`/events/${e.id}`}>
                  <div className="group border border-white/10 hover:border-violet-500/50 rounded-2xl overflow-hidden transition-all hover:scale-[1.02]">
                    <div className={`h-40 bg-gradient-to-br ${gradient} flex flex-col justify-between p-4`}>
                      <span className="self-start text-xs bg-black/30 text-white/70 px-2.5 py-1 rounded-full">
                        {date.toLocaleString("ru", { day: "numeric", month: "long" })}
                      </span>
                      <span className={`self-end text-xs px-2 py-0.5 rounded-full ${
                        avail > 0.5 ? "bg-emerald-900/60 text-emerald-300" :
                        avail > 0.15 ? "bg-amber-900/60 text-amber-300" :
                        "bg-red-900/60 text-red-300"
                      }`}>
                        {e.available_seats} мест
                      </span>
                    </div>
                    <div className="bg-slate-900 p-4">
                      <p className="font-semibold text-white group-hover:text-violet-300 transition-colors truncate">
                        {e.name}
                      </p>
                      <p className="text-white/40 text-sm mt-1 truncate">{e.venue}</p>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Stats */}
      <section className="border-t border-white/10 bg-slate-900/50">
        <div className="max-w-6xl mx-auto px-6 py-14 grid grid-cols-3 gap-8 text-center">
          {[
            { icon: Zap,    value: "10 000+", label: "Запросов/сек",    sub: "FastAPI async" },
            { icon: Shield, value: "94%",     label: "Точность AI",     sub: "RandomForest + GB" },
            { icon: Ticket, value: "<50ms",   label: "Блокировка бота", sub: "Redis + ML" },
          ].map(({ icon: Icon, value, label, sub }) => (
            <div key={label}>
              <Icon size={22} className="text-violet-400 mx-auto mb-3" />
              <div className="text-3xl font-bold text-white">{value}</div>
              <div className="text-white/60 text-sm mt-1">{label}</div>
              <div className="text-white/30 text-xs mt-0.5">{sub}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
