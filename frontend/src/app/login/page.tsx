"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useStore } from "@/store";
import { Ticket } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useStore();
  const [tab, setTab] = useState<"login"|"register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!email || !password) { setError("Заполните все поля"); return; }
    setLoading(true); setError("");
    try {
      const res = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setUser({ id: data.user_id, email, token: data.access });
        router.push("/events");
      } else {
        // Демо-режим: пускаем с мок токеном
        setUser({ id: "demo-user", email, token: "demo-token" });
        router.push("/events");
      }
    } catch {
      // Сервер недоступен — демо
      setUser({ id: "demo-user", email, token: "demo-token" });
      router.push("/events");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[85vh] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-white font-bold text-xl mb-2">
            <Ticket size={22} className="text-violet-400" /> HFBS
          </div>
          <p className="text-white/30 text-sm">Билеты на лучшие события</p>
        </div>

        {/* Tabs */}
        <div className="flex bg-white/5 rounded-xl p-1 mb-6">
          {(["login","register"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === t ? "bg-violet-600 text-white" : "text-white/40 hover:text-white"
              }`}
            >
              {t === "login" ? "Войти" : "Регистрация"}
            </button>
          ))}
        </div>

        {/* Form */}
        <div className="space-y-3">
          <div>
            <label className="text-white/40 text-xs block mb-1">Email</label>
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSubmit()}
              className="input"
            />
          </div>
          <div>
            <label className="text-white/40 text-xs block mb-1">Пароль</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSubmit()}
              className="input"
            />
          </div>

          {error && (
            <div className="bg-red-950/40 border border-red-800/30 rounded-xl px-3 py-2 text-red-300 text-xs">
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-violet-600 hover:bg-violet-500 disabled:bg-white/8 disabled:text-white/20 text-white py-3 rounded-xl font-semibold transition-colors mt-2"
          >
            {loading ? "Входим..." : tab === "login" ? "Войти" : "Создать аккаунт"}
          </button>

          <p className="text-white/20 text-xs text-center pt-1">
            Демо: любой email + пароль
          </p>
        </div>
      </div>
    </main>
  );
}
