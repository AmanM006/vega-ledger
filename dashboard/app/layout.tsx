import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VEGA LEDGER // VRP-AGENT — Autonomous Institutional Risk Governor",
  description: "Alpaca AI Trading Agents Hackathon — LangGraph, Scikit-Learn Random Forest, DSR Statistical Rigor, Ethereum Sepolia Audit Trail.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-black text-zinc-100 min-h-screen antialiased selection:bg-emerald-500/30 selection:text-emerald-200 font-[family-name:var(--font-space-grotesk)]">
        {children}
      </body>
    </html>
  );
}
