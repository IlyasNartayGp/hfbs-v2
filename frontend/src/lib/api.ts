const BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  let token: string | null = null;
  if (typeof window !== "undefined") {
    try {
      token = JSON.parse(localStorage.getItem("hfbs-store") ?? "{}").state?.user?.token ?? null;
    } catch {}
  }

  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...opts,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw { status: res.status, detail: err.detail ?? "Ошибка запроса" };
  }
  return res.json();
}

export const api = {
  events: {
    list: () => req<Event[]>("/events/"),
    detail: (id: number) => req<EventDetail>(`/events/${id}/`),
    seats: (id: number) => req<Seat[]>(`/events/${id}/seats`),
  },
  bookings: {
    create: (body: BookingBody) => req<BookingResult>("/bookings/", {
      method: "POST",
      body: JSON.stringify(body),
    }),
    cancel: (id: string) => req(`/bookings/${id}`, { method: "DELETE" }),
  },
  auth: {
    login: (email: string, password: string) =>
      req<{ access: string; user_id: string }>("/auth/login/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
  },
};

export interface Event {
  id: number;
  name: string;
  venue: string;
  date: string;
  image_url?: string;
  total_seats: number;
  available_seats: number;
  description?: string;
}

export interface EventDetail extends Event {
  categories: { name: string; price: number; color: string }[];
}

export interface Seat {
  id: number;
  row: string;
  number: number;
  price: number;
  status: "available" | "booked";
  category?: string;
}

export interface BookingBody {
  event_id: number;
  seat_id: number;
  user_id: string;
}

export interface BookingResult {
  booking_id: string;
  status: string;
  message: string;
}
