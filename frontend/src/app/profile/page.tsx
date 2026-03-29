"use client";
import { useStore } from "@/store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { Ticket, Calendar, MapPin, Download } from "lucide-react";

const MOCK_TICKETS = [
  { id: "bk-001", event: "Imagine Dragons", venue: "Barys Arena", date: "15 июня 2025", seat: "B12", price: 15000, status: "confirmed" },
  { id: "bk-002", event: "Jazz Almaty Festival", venue: "Театральная площадь", date: "2 авг 2025", seat: "F5", price: 5000, status: "confirmed" },
  { id: "bk-003", event: "Comedy Club", venue: "Congress Hall", date: "10 мая 2025", seat: "D8", price: 10000, status: "pending" },
];

export default function ProfilePage() {
  const { user } = useStore();
  const router = useRouter();

  useEffect(() => {
    if (!user) router.push("/login");
  }, [user]);

  if (!user) return null;

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-center gap-4 mb-10">
        <div className="w-12 h-12 rounded-full bg-violet-600/30 border border-violet-500/30 flex items-center justify-center text-violet-300 font-bold text-lg">
          {user.email[0].toUpperCase()}
        </div>
        <div>
          <p className="font-semibold text-white">{user.email}</p>
          <p className="text-white/30 text-sm">ID: {user.id}</p>
        </div>
      </div>

      {/* Tickets */}
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Ticket size={18} className="text-violet-400" /> Мои билеты
      </h2>

      <div className="space-y-3">
        {MOCK_TICKETS.map(ticket => (
          <div key={ticket.id} className="bg-white/5 border border-white/10 rounded-2xl p-5 flex items-center gap-5">
            {/* Status dot */}
            <div className={`w-2 h-2 rounded-full shrink-0 ${
              ticket.status === "confirmed" ? "bg-emerald-400" : "bg-amber-400"
            }`} />

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-white truncate">{ticket.event}</p>
              <div className="flex items-center gap-3 mt-1 text-white/35 text-xs">
                <span className="flex items-center gap-1"><MapPin size={10}/>{ticket.venue}</span>
                <span className="flex items-center gap-1"><Calendar size={10}/>{ticket.date}</span>
              </div>
            </div>

            {/* Seat + price */}
            <div className="text-right shrink-0">
              <p className="text-white/50 text-sm">Место {ticket.seat}</p>
              <p className="text-violet-400 font-semibold text-sm">{ticket.price.toLocaleString()} ₸</p>
            </div>

            {/* Download PDF */}
            <button
              title="Скачать билет"
              className="shrink-0 w-8 h-8 rounded-lg bg-white/5 hover:bg-violet-600/30 border border-white/10 hover:border-violet-500/30 flex items-center justify-center text-white/40 hover:text-violet-300 transition-all"
            >
              <Download size={14} />
            </button>
          </div>
        ))}
      </div>

      <Link
        href="/events"
        className="inline-block mt-6 text-violet-400 hover:text-violet-300 text-sm transition-colors"
      >
        + Купить ещё билеты
      </Link>
    </main>
  );
}
