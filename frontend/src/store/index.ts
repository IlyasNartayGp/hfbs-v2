import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  token: string;
}

interface Seat {
  id: number;
  row: string;
  number: number;
  price: number;
  status: "available" | "booked" | "selected";
}

interface AppState {
  user: User | null;
  setUser: (u: User | null) => void;
  selectedSeat: Seat | null;
  setSelectedSeat: (s: Seat | null) => void;
  bookingId: string | null;
  setBookingId: (id: string | null) => void;
  currentEventId: number | null;
  setCurrentEventId: (id: number | null) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      selectedSeat: null,
      setSelectedSeat: (selectedSeat) => set({ selectedSeat }),
      bookingId: null,
      setBookingId: (bookingId) => set({ bookingId }),
      currentEventId: null,
      setCurrentEventId: (currentEventId) => set({ currentEventId }),
    }),
    {
      name: "hfbs-store",
      partialize: (s) => ({ user: s.user }),
    }
  )
);
