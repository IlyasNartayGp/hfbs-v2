import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "HFBS — Система бронирования билетов",
  description: "Высоконагруженная система бронирования с защитой от ботов",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
