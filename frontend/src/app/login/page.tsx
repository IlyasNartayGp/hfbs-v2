"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ email: "", name: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = async () => {
    setError("");
    setLoading(true);
    try {
      let res;
      if (mode === "login") {
        const body = new URLSearchParams({
          username: form.email,
          password: form.password,
        });
        res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });
      } else {
        res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: form.email, name: form.name, password: form.password }),
        });
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ошибка");
      localStorage.setItem("token", data.access_token);
      router.push("/events");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="text-white font-bold text-2xl">🎟 HFBS</Link>
          <p className="text-white/40 mt-2 text-sm">Система бронирования билетов</p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-8">
          {/* Tabs */}
          <div className="flex bg-white/5 rounded-xl p-1 mb-6">
            {(["login", "register"] as const).map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(""); }}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  mode === m
                    ? "bg-purple-600 text-white"
                    : "text-white/50 hover:text-white"
                }`}
              >
                {m === "login" ? "Войти" : "Регистрация"}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="text-white/60 text-sm block mb-1">Имя</label>
                <input
                  type="text"
                  placeholder="Иван Иванов"
                  value={form.name}
                  onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                  className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            )}
            <div>
              <label className="text-white/60 text-sm block mb-1">Email</label>
              <input
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
            <div>
              <label className="text-white/60 text-sm block mb-1">Пароль</label>
              <input
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                className="w-full bg-white/10 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            {error && (
              <div className="bg-red-900/30 border border-red-700/30 rounded-xl p-3 text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handle}
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-500 disabled:bg-white/10 disabled:text-white/30 text-white py-3 rounded-xl font-medium transition-colors mt-2"
            >
              {loading ? "Загрузка..." : mode === "login" ? "Войти" : "Создать аккаунт"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
