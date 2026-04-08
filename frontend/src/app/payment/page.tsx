"use client";
import { Suspense, useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Lock, CheckCircle, Download, Loader } from "lucide-react";

function fmt4(v: string) { return v.replace(/\D/g,"").slice(0,16).replace(/(.{4})/g,"$1 ").trim(); }
function fmtExp(v: string) { return v.replace(/\D/g,"").slice(0,4).replace(/(\d{2})(\d)/,"$1/$2"); }

function PaymentContent() {
  const p = useSearchParams();
  const router = useRouter();
  const bookingId = p.get("booking_id") ?? "—";
  const price     = Number(p.get("price") ?? 5000);
  const seat      = p.get("seat") ?? "—";

  const gatewayBase =
    typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}:8880`
      : "http://localhost:8880";
  const ticketDownloadUrl = `${gatewayBase}/api/tickets/${bookingId}/download/`;

  const [card, setCard]       = useState({ number:"", expiry:"", cvv:"", name:"" });
  const [loading, setLoading] = useState(false);
  const [done, setDone]       = useState(false);
  const [error, setError]     = useState("");
  const [pdfReady, setPdfReady] = useState(false);
  const [checking, setChecking] = useState(false);

  // Проверять готовность PDF после оплаты
  useEffect(() => {
    if (!done || bookingId === "—") return;
    setChecking(true);
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const res = await fetch(`/api/bookings/${bookingId}/ticket`, { method: "HEAD" });
        if (res.ok) {
          setPdfReady(true);
          setChecking(false);
          clearInterval(interval);
        }
      } catch {}
      if (attempts > 10) {
        setChecking(false);
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [done, bookingId]);

  const handlePay = async () => {
    if (!card.number || !card.expiry || !card.cvv || !card.name) {
      setError("Заполните все поля"); return;
    }
    setLoading(true); setError("");
    await new Promise(r => setTimeout(r, 1400));
    setDone(true); setLoading(false);
  };

  if (done) return (
    <main className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="text-center max-w-sm">
        <CheckCircle size={56} className="text-emerald-400 mx-auto mb-5" />
        <h1 className="text-2xl font-bold text-white mb-2">Оплата прошла!</h1>
        <p className="text-white/40 text-sm mb-1">Билет генерируется...</p>
        <p className="text-white/20 text-xs font-mono mb-6">{bookingId}</p>

        {/* PDF статус */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4 mb-6">
          {pdfReady ? (
            <a
              href={ticketDownloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 text-white py-3 px-6 rounded-xl font-medium transition-colors w-full"
            >
              <Download size={16} />
              Скачать PDF билет
            </a>
          ) : (
            <div className="flex items-center justify-center gap-2 text-white/40 text-sm py-2">
              <Loader size={14} className="animate-spin" />
              {checking ? "Генерируем билет..." : "Билет будет готов через несколько секунд"}
            </div>
          )}
        </div>

        <div className="flex gap-3 justify-center">
          <Link href="/profile" className="bg-white/10 hover:bg-white/20 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
            Мои билеты
          </Link>
          <Link href="/events" className="border border-white/15 hover:border-white/30 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
            К событиям
          </Link>
        </div>
      </div>
    </main>
  );

  return (
    <main className="max-w-3xl mx-auto px-6 py-12 grid grid-cols-[1fr_300px] gap-8">
      <div>
        <h2 className="text-lg font-semibold mb-5">Ваш заказ</h2>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-4 mb-4">
          <Row label="Место"  value={`Ряд ${seat}`} />
          <Row label="Бронь"  value={<span className="font-mono text-xs text-white/50">{bookingId}</span>} />
          <div className="border-t border-white/10 pt-4 flex justify-between items-center">
            <span className="text-white/50 text-sm">Итого</span>
            <span className="text-xl font-bold text-violet-400">{price.toLocaleString()} ₸</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800/20 rounded-xl px-4 py-3">
          <Lock size={12} /> Место заблокировано на 10 минут
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-5">Оплата</h2>
        <div className="space-y-3">
          <Field label="Номер карты">
            <input placeholder="0000 0000 0000 0000" value={card.number}
              onChange={e => setCard(p => ({...p, number: fmt4(e.target.value)}))}
              className="input font-mono" />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Срок">
              <input placeholder="MM/YY" value={card.expiry}
                onChange={e => setCard(p => ({...p, expiry: fmtExp(e.target.value)}))}
                className="input font-mono" />
            </Field>
            <Field label="CVV">
              <input placeholder="•••" type="password" maxLength={3} value={card.cvv}
                onChange={e => setCard(p => ({...p, cvv: e.target.value.replace(/\D/g,"").slice(0,3)}))}
                className="input font-mono" />
            </Field>
          </div>
          <Field label="Имя">
            <input placeholder="IVAN IVANOV" value={card.name}
              onChange={e => setCard(p => ({...p, name: e.target.value.toUpperCase()}))}
              className="input" />
          </Field>

          {error && (
            <div className="bg-red-950/40 border border-red-800/30 rounded-xl px-3 py-2 text-red-300 text-xs">
              {error}
            </div>
          )}

          <button onClick={handlePay} disabled={loading}
            className="w-full bg-violet-600 hover:bg-violet-500 disabled:bg-white/10 disabled:text-white/20 text-white py-3 rounded-xl font-semibold transition-colors">
            {loading ? "Обработка..." : `Оплатить ${price.toLocaleString()} ₸`}
          </button>
          <p className="text-white/20 text-xs text-center">Тестовый режим — деньги не списываются</p>
        </div>
      </div>
    </main>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-white/40 text-sm">{label}</span>
      <span className="text-white text-sm font-medium">{value}</span>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-white/40 text-xs block mb-1">{label}</label>
      {children}
    </div>
  );
}

export default function PaymentPage() {
  return (
    <Suspense fallback={<div className="text-white/30 text-center py-20">Загрузка...</div>}>
      <PaymentContent />
    </Suspense>
  );
}
