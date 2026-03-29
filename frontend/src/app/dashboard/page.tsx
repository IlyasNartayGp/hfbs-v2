"use client";
import { useEffect, useState } from "react";
import { Shield, TrendingUp, Users, Ban, Activity, RefreshCw } from "lucide-react";

interface Stats {
  blocked_total: number;
  allowed_total: number;
  total_requests: number;
  block_rate: number;
  model_metrics: {
    f1?: number;
    roc_auc?: number;
    accuracy?: number;
    precision?: number;
    recall?: number;
  };
}

interface LogEntry {
  ip: string;
  event_id: number;
  seat_id: number;
  is_bot: boolean;
  confidence: number;
  verdict: string;
  ts: number;
}

const MOCK_STATS: Stats = {
  blocked_total: 1284,
  allowed_total: 9847,
  total_requests: 11131,
  block_rate: 11.54,
  model_metrics: { f1: 0.9312, roc_auc: 0.9748, accuracy: 0.9401, precision: 0.9187, recall: 0.9441 },
};

const MOCK_LOGS: LogEntry[] = [
  { ip: "185.220.101.5", event_id: 1, seat_id: 42, is_bot: true, confidence: 0.97, verdict: "blocked", ts: Date.now() - 12000 },
  { ip: "91.185.23.11", event_id: 1, seat_id: 15, is_bot: false, confidence: 0.12, verdict: "allowed", ts: Date.now() - 34000 },
  { ip: "162.247.72.3", event_id: 2, seat_id: 7, is_bot: true, confidence: 0.89, verdict: "blocked", ts: Date.now() - 61000 },
  { ip: "178.45.12.88", event_id: 1, seat_id: 99, is_bot: false, confidence: 0.08, verdict: "allowed", ts: Date.now() - 90000 },
  { ip: "185.100.87.41", event_id: 3, seat_id: 3, is_bot: true, confidence: 0.94, verdict: "blocked", ts: Date.now() - 120000 },
];

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    try {
      const [s, l] = await Promise.all([
        fetch("/api/antifrod/stats").then(r => r.json()),
        fetch("/api/antifrod/logs?limit=20").then(r => r.json()),
      ]);
      setStats(s);
      setLogs(l.logs ?? []);
    } catch {
      setStats(MOCK_STATS);
      setLogs(MOCK_LOGS);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  const m = stats?.model_metrics ?? {};

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Shield size={22} className="text-violet-400" />
          <div>
            <h1 className="text-xl font-bold">Antifrod Dashboard</h1>
            <p className="text-white/30 text-xs">RandomForest + GradientBoosting ensemble</p>
          </div>
        </div>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 text-xs text-white/40 hover:text-white border border-white/10 hover:border-white/20 px-3 py-1.5 rounded-lg transition-all"
        >
          <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
          Обновить
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[1,2,3,4].map(i => <div key={i} className="h-24 bg-white/5 rounded-2xl animate-pulse" />)}
        </div>
      ) : (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            <StatCard icon={Activity} label="Всего запросов" value={stats!.total_requests.toLocaleString()} color="text-white" />
            <StatCard icon={Ban} label="Заблокировано" value={stats!.blocked_total.toLocaleString()} color="text-red-400" />
            <StatCard icon={Users} label="Пропущено" value={stats!.allowed_total.toLocaleString()} color="text-emerald-400" />
            <StatCard icon={TrendingUp} label="Block rate" value={`${stats!.block_rate}%`} color="text-amber-400" />
          </div>

          {/* Model metrics */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5 mb-6">
            <h2 className="text-sm font-semibold text-white/50 uppercase tracking-wide mb-4">
              Метрики модели
            </h2>
            <div className="grid grid-cols-5 gap-4">
              {[
                ["Accuracy",  m.accuracy],
                ["Precision", m.precision],
                ["Recall",    m.recall],
                ["F1 Score",  m.f1],
                ["ROC-AUC",   m.roc_auc],
              ].map(([label, val]) => (
                <div key={label as string} className="text-center">
                  <div className="text-2xl font-bold text-violet-300">
                    {val ? (val as number * 100).toFixed(1) + "%" : "—"}
                  </div>
                  <div className="text-white/30 text-xs mt-1">{label as string}</div>
                  {/* Mini bar */}
                  <div className="mt-2 h-1 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-violet-500 rounded-full"
                      style={{ width: `${(val as number ?? 0) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Live log */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-white/50 uppercase tracking-wide mb-4">
              Последние запросы
            </h2>
            <div className="space-y-2">
              {logs.slice(0, 10).map((log, i) => (
                <div key={i} className="flex items-center gap-4 text-xs py-2 border-b border-white/5 last:border-0">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${log.is_bot ? "bg-red-400" : "bg-emerald-400"}`} />
                  <span className="font-mono text-white/50 w-32 shrink-0">{log.ip}</span>
                  <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${
                    log.verdict === "blocked"
                      ? "bg-red-950/60 text-red-300 border border-red-800/30"
                      : "bg-emerald-950/60 text-emerald-300 border border-emerald-800/30"
                  }`}>
                    {log.verdict}
                  </span>
                  <span className="text-white/30">событие #{log.event_id} · место {log.seat_id}</span>
                  <span className="ml-auto text-white/20 shrink-0">
                    {Math.round((Date.now() - log.ts * 1000) / 1000)}с назад
                  </span>
                  <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden shrink-0">
                    <div
                      className={`h-full rounded-full ${log.is_bot ? "bg-red-500" : "bg-emerald-500"}`}
                      style={{ width: `${log.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-white/30 w-8 text-right shrink-0">{(log.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </main>
  );
}

function StatCard({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: string; color: string;
}) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
      <Icon size={16} className={`${color} mb-3 opacity-70`} />
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-white/30 text-xs mt-1">{label}</div>
    </div>
  );
}
