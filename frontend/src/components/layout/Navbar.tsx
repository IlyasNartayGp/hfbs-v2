"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!localStorage.getItem("token"));
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    setLoggedIn(false);
    router.push("/login");
  };

  return (
    <nav className="border-b border-white/10 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link href="/" className="text-white font-bold text-xl">🎟 HFBS</Link>
        <div className="flex items-center gap-4">
          <Link href="/events" className="text-white/60 hover:text-white text-sm transition-colors">
            События
          </Link>
          <Link href="/dashboard" className="text-white/60 hover:text-white text-sm transition-colors">
            Dashboard
          </Link>
          {loggedIn ? (
            <>
              <Link href="/profile" className="text-white/60 hover:text-white text-sm transition-colors">
                Мои билеты
              </Link>
              <button onClick={logout} className="text-white/40 hover:text-white text-sm transition-colors">
                Выйти
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-1.5 rounded-lg transition-colors text-sm"
            >
              Войти
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
