"use client";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useStore } from "@/store";
import { Ticket, LayoutDashboard, LogOut, User } from "lucide-react";

export function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, setUser } = useStore();

  const logout = () => {
    setUser(null);
    router.push("/login");
  };

  const link = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-sm transition-colors ${
        pathname === href ? "text-white font-medium" : "text-white/50 hover:text-white"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="border-b border-white/10 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-white">
          <Ticket size={20} className="text-violet-400" />
          HFBS
        </Link>

        <nav className="flex items-center gap-6">
          {link("/events", "События")}
          {link("/dashboard", "Dashboard")}

          {user ? (
            <>
              {link("/profile", "Мои билеты")}
              <button
                onClick={logout}
                className="text-white/40 hover:text-white transition-colors"
              >
                <LogOut size={16} />
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="bg-violet-600 hover:bg-violet-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors"
            >
              Войти
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
