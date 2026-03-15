"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

interface Stats {
  blocked_total: number;
  allowed_total: number;
  total_requests: number;
  block_rate: number;
  model_metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1?: number;
    roc_auc?: number;
    trained_at?: string;
    feature_importance?: Record<string, number>;
  };
}

interface LogEntry {
  ip: string;
  is_bot: boolean;
  confidence: number;
  verdict: string;
  event_id: number;
  seat_id: number;
  ts: number;
}

const MOCK_LOGS: LogEntry[] = [
  { ip: "185.220.101.x", is_bot: true,  confidence: 0.97, verdict: "blocked",    event_id: 1, seat_id: 1,  ts: Date.now() / 1000 - 2 },
  { ip: "91.108.4.x",    is_bot: true,  confidence: 0.91, verdict: "blocked",    event_id: 1, seat_id: 1,  ts: Date.now() / 1000 - 5 },
  { ip: "213.87.x.x",    is_bot: false, confidence: 0.08, verdict: "allowed",    event_id: 1, seat_id: 7,  ts: Date.now() / 1000 - 8 },
  { ip: "77.234.x.x",    is_bot: true,  confidence: 0.88, verdict: "blocked",    event_id: 2, seat_id: 3,  ts: Date.now() / 1000 - 12 },
  { ip: "95.165.x.x",    is_bot: false, confidence: 0.12, verdict: "allowed",    event_id: 1, seat_id: 14, ts: Date.now() / 1000 - 15 },
  { ip: "178.62.x.x",    is_bot: false, confidence: 0.55, verdict: "suspicious", event_id: 2, seat_id: 2,  ts: Date.now() / 1000 - 20 },
];

const MOCK_STATS: Stats = {
  blocked_total: 142,
  allowed_total: 1893,
  total_requests: 2035,
  block_rate: 6.97,
  model_metrics: {
    accuracy: 0.9612,
    precision: 0.9534,
    recall: 0.9701,
    f1: 0.9617,
    roc_auc: 0.9889,
    trained_at: "2025-03-15 14:00:00",
    feature_importance: {
      requests_per_minute: 0.2341,
      secs_after_sale_open: 0.1987,
      seat_attempts: 0.1654,
      session_duration_sec: 0.1123,
      is_known_bot_ua: 0.0987,
      unique_seats_tried: 0.0876,
      always_front_row: 0.0654,
      avg_price_targeted: 0.0234,
      is_suspicious_ip: 0.0098,
      hour_of_day: 0.0046,
    },
  },
};

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>(MOCK_STATS);
  const [logs, setLogs] = useState<LogEntry[]>(MOCK_LOGS);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [statsRes, logsRes] = await Promise.all([
          fetch("/api/antifrod/stats"),
          fetch("/api/antifrod/logs?limit=20"),
        ]);
        if (statsRes.ok) setStats(await statsRes.json());
        if (logsRes.ok) {
          const data = await logsRes.json();
          if (data.logs?.length) setLogs(data.logs);
        }
      } catch {}
    };
    fetchAll();
    const interval = setInterval(fetchAll, 3000);
    return () => clearInterval(interval);
  }, []);

  const verdictBadge = (verdict: string) => {
    if (verdict === "blocked")    return "bg-red-900/50 text-red-300";
    if (verdict === "suspicious") return "bg-amber-900/50 text-amber-300";
    return "bg-green-900/50 text-green-300";
  };

  const verdictLabel = (verdict: string) => {
    if (verdict === "blocked")    return "БОТ";
    if (verdict === "suspicious") return "ПОДОЗР.";
    return "OK";
  };

  const fi = stats.model_metrics?.feature_importance ?? {};
  const fiEntries = Object.entries(fi).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxFi = fiEntries[0]?.[1] ?? 1;

  return (
    <main className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <h1 className="text-2xl font-bold">Antifrod Dashboard</h1>
            <span className="text-white/30 text-sm">live · обновление каждые 3с</span>
          </div>
          <Link href="/events" className="text-white/40 hover:text-white text-sm transition-colors">
            ← к событиям
          </Link>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Всего запросов",  value: stats.total_requests.toLocaleString(), color: "text-white" },
            { label: "Заблокировано",   value: stats.blocked_total.toLocaleString(),  color: "text-red-400" },
            { label: "Пропущено",       value: stats.allowed_total.toLocaleString(),  color: "text-green-400" },
            { label: "Процент ботов",   value: `${stats.block_rate}%`,                color: "text-amber-400" },
          ].map(s => (
            <div key={s.label} className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="text-white/40 text-xs mb-1">{s.label}</div>
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6">

          {/* Model metrics */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Метрики модели</h2>
              <span className="text-white/30 text-xs">RF + GBM ансамбль</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Accuracy",  value: stats.model_metrics?.accuracy },
                { label: "Precision", value: stats.model_metrics?.precision },
                { label: "Recall",    value: stats.model_metrics?.recall },
                { label: "F1 Score",  value: stats.model_metrics?.f1 },
                { label: "ROC-AUC",   value: stats.model_metrics?.roc_auc },
              ].map(m => (
                <div key={m.label} className="bg-white/5 rounded-lg p-3">
                  <div className="text-white/40 text-xs">{m.label}</div>
                  <div className="text-lg font-bold text-purple-300">
                    {m.value ? (m.value * 100).toFixed(1) + "%" : "—"}
                  </div>
                </div>
              ))}
            </div>
            <div className="text-white/20 text-xs">
              Обучено: {stats.model_metrics?.trained_at ?? "—"}
            </div>
          </div>

          {/* Feature importance */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3">
            <h2 className="font-semibold">Важность признаков</h2>
            {fiEntries.map(([name, val]) => (
              <div key={name}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/60">{name}</span>
                  <span className="text-white/40">{(val * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-white/10 rounded-full h-1.5">
                  <div
                    className="bg-purple-500 h-1.5 rounded-full"
                    style={{ width: `${(val / maxFi) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live log */}
        <div className="bg-white/5 border border-white/10 rounded-xl">
          <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
            <h2 className="font-semibold text-sm">Последние запросы</h2>
            <span className="text-white/30 text-xs">{logs.length} записей</span>
          </div>
          <div className="divide-y divide-white/5">
            {logs.map((log, i) => (
              <div key={i} className="px-5 py-2.5 flex items-center gap-4 text-sm hover:bg-white/3 transition-colors">
                <span className="text-white/25 text-xs w-20 shrink-0">
                  {new Date(log.ts * 1000).toLocaleTimeString("ru")}
                </span>
                <span className="font-mono text-white/60 w-36 shrink-0">{log.ip}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium shrink-0 ${verdictBadge(log.verdict)}`}>
                  {verdictLabel(log.verdict)}
                </span>
                <span className="text-white/35 text-xs shrink-0">
                  {(log.confidence * 100).toFixed(0)}% уверенность
                </span>
                <span className="text-white/25 text-xs">
                  event#{log.event_id} seat#{log.seat_id}
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </main>
  );
}
