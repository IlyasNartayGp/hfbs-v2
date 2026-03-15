"use client";
import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navbar */}
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <span className="text-white font-bold text-xl">🎟 HFBS</span>
          <div className="flex gap-4">
            <Link href="/events" className="text-white/70 hover:text-white transition-colors">
              События
            </Link>
            <Link href="/dashboard" className="text-white/70 hover:text-white transition-colors">
              Dashboard
            </Link>
            <Link
              href="/login"
              className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-1.5 rounded-lg transition-colors text-sm"
            >
              Войти
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <div className="inline-block bg-purple-500/20 text-purple-300 text-sm px-3 py-1 rounded-full mb-6 border border-purple-500/30">
          Защита от ботов в реальном времени
        </div>
        <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
          Билеты без очередей <br />
          <span className="text-purple-400">и без ботов</span>
        </h1>
        <p className="text-white/60 text-xl mb-10 max-w-2xl mx-auto">
          Высоконагруженная система бронирования. FastAPI async обрабатывает
          тысячи запросов одновременно, AI блокирует ботов до момента оплаты.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/events"
            className="bg-purple-600 hover:bg-purple-500 text-white px-8 py-3 rounded-xl font-medium transition-colors"
          >
            Смотреть события
          </Link>
          <Link
            href="/dashboard"
            className="border border-white/20 hover:border-white/40 text-white px-8 py-3 rounded-xl font-medium transition-colors"
          >
            Antifrod Dashboard
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-6xl mx-auto px-6 pb-24 grid grid-cols-3 gap-6">
        {[
          { label: "Запросов/сек", value: "10,000+", desc: "FastAPI async" },
          { label: "Точность AI", value: "94%", desc: "sklearn RandomForest" },
          { label: "Время блокировки", value: "<50ms", desc: "Redis + ML" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center"
          >
            <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
            <div className="text-purple-400 font-medium mb-1">{stat.label}</div>
            <div className="text-white/40 text-sm">{stat.desc}</div>
          </div>
        ))}
      </section>
    </main>
  );
}
