"use client";

import { useEffect, useState, useRef } from "react";
import Lenis from "lenis";
import {
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Activity,
  ArrowUpRight,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  Terminal,
  Database,
  Lock,
  Layers,
  Code2,
  CheckCircle2,
  XCircle,
  Clock,
  Play
} from "lucide-react";

interface Position {
  symbol: string;
  qty: string;
  market_value: string;
  unrealized_pl: string;
  unrealized_plpc: string;
}

interface Order {
  symbol: string;
  side: string;
  qty: string;
  filled_qty: string;
  status: string;
  submitted_at: string;
  filled_avg_price: string | null;
}

interface LogEntry {
  entry?: {
    timestamp?: string;
    market_data?: {
      spy_price?: number;
      vix_now?: number;
      iv_rank?: number;
      account_equity?: number;
    };
    vrp?: {
      regime_signal?: { tradeable?: boolean; reasons?: string[] };
      execution_result?: { status?: string };
    };
    ml_momentum?: {
      signal?: { signal?: string; confidence?: number; reason?: string };
      execution?: { status?: string };
    };
    earnings?: {
      setups?: Array<{ ticker?: string; tradeable?: boolean; reject_reason?: string }>;
    };
  };
  hash?: string;
}

const ETHERSCAN_TX = "0x46f3ce0bdb9e343a4d2c85b57146a5c2fca5c5dd861c9aadab00f21bb75f396d";

export default function TerminalDashboard() {
  const [mounted, setMounted] = useState(false);
  const [accountData, setAccountData] = useState<{ account?: Record<string, string>; positions?: Position[]; orders?: Order[] } | null>(null);
  const [logData, setLogData] = useState<{ entries?: LogEntry[]; total?: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [selectedBlockIndex, setSelectedBlockIndex] = useState<number>(0);
  const [logFilter, setLogFilter] = useState<"official" | "all">("official");

  const fetchAll = async () => {
    try {
      const [acc, log] = await Promise.all([
        fetch("/api/account").then((r) => r.json()).catch(() => ({})),
        fetch("/api/log").then((r) => r.json()).catch(() => ({ entries: [] })),
      ]);
      setAccountData(acc);
      setLogData(log);
      setLastRefresh(new Date());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    setLastRefresh(new Date());
    fetchAll();

    const lenis = new Lenis({
      duration: 1.0,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    const interval = setInterval(fetchAll, 25000);
    return () => {
      clearInterval(interval);
      lenis.destroy();
    };
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-zinc-500 font-mono text-xs">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span>INITIALIZING WORKSTATION...</span>
        </div>
      </div>
    );
  }

  const acc = accountData?.account;
  const positions = Array.isArray(accountData?.positions) ? accountData.positions : [];
  const orders = Array.isArray(accountData?.orders) ? accountData.orders : [];
  const logEntries = Array.isArray(logData?.entries) ? logData.entries : [];
  const latestEntry = logEntries[0]?.entry;

  const equity = parseFloat(acc?.equity ?? "100000") || 100000;
  const pnl = equity - 100000;
  const pnlColor = pnl >= 0 ? "text-emerald-400" : "text-rose-400";
  const pnlPrefix = pnl >= 0 ? "+" : "";

  const selectedBlock = logEntries[selectedBlockIndex] || logEntries[0];

  return (
    <div className="min-h-screen bg-black text-zinc-300 selection:bg-emerald-500/20 selection:text-emerald-300 font-[family-name:var(--font-jetbrains-mono)] flex flex-col antialiased">
      {/* Dynamic Background Noise */}
      <div className="fixed inset-0 bg-grid-pattern opacity-30 pointer-events-none z-0" />

      {/* TOP DENSE WORKSTATION HEADER */}
      <header className="sticky top-0 z-50 border-b border-zinc-900 bg-black/95 backdrop-blur-md px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Brand & Account Identifier */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
            <h1 className="font-bold tracking-tight text-white font-mono text-sm">VEGA LEDGER</h1>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
              TERMINAL v2.4
            </span>
          </div>
          <span className="text-zinc-700">|</span>
          <div className="flex items-center gap-2 text-[11px] text-zinc-400">
            <span className="text-zinc-500 uppercase">Account:</span>
            <span className="text-white font-bold bg-zinc-900/90 px-2 py-0.5 rounded border border-zinc-800">
              PA3LL11TFH7L
            </span>
            <span className="text-emerald-400 text-[10px] border border-emerald-500/30 bg-emerald-500/10 px-1.5 py-0.5 rounded">
              COMPETITION VERIFIED
            </span>
          </div>
        </div>

        {/* Right Tools & Sync */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-zinc-500 hidden sm:inline">
            SYNC: {lastRefresh ? lastRefresh.toLocaleTimeString() : "--:--:--"}
          </span>
          <button
            onClick={fetchAll}
            disabled={loading}
            className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition active:scale-95 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            <span>REFRESH</span>
          </button>
          <a
            href={`https://sepolia.etherscan.io/tx/${ETHERSCAN_TX}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded bg-emerald-950/40 hover:bg-emerald-900/50 border border-emerald-500/30 text-emerald-400 transition"
          >
            <span>ETHERSCAN</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </header>

      {/* TOP FINANCIAL TICKER STRIP */}
      <section className="border-b border-zinc-900 bg-zinc-950/80 px-4 py-2 text-xs relative z-10">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">Total Equity</p>
            <p className="font-bold text-white text-sm tracking-tight">${equity.toLocaleString("en-US", { minimumFractionDigits: 2 })}</p>
          </div>
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">Net Return</p>
            <p className={`font-bold text-sm ${pnlColor}`}>{pnlPrefix}${pnl.toFixed(2)}</p>
          </div>
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">Cash Reserve</p>
            <p className="font-bold text-zinc-300 text-sm">${(parseFloat(acc?.cash ?? "100000") || 100000).toLocaleString("en-US", { minimumFractionDigits: 2 })}</p>
          </div>
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">Buying Power (4x)</p>
            <p className="font-bold text-zinc-300 text-sm">${(parseFloat(acc?.buying_power ?? "400000") || 400000).toLocaleString("en-US", { minimumFractionDigits: 2 })}</p>
          </div>
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">SPY Spot</p>
            <p className="font-bold text-white text-sm">${(latestEntry?.market_data?.spy_price ?? 765.55).toFixed(2)}</p>
          </div>
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">VIX Level</p>
            <p className="font-bold text-amber-400 text-sm">{(latestEntry?.market_data?.vix_now ?? 15.54).toFixed(2)}</p>
          </div>
          <div className="border-r border-zinc-900/80 pr-2">
            <p className="text-[10px] uppercase text-zinc-500">IV Rank</p>
            <p className="font-bold text-zinc-300 text-sm">{(latestEntry?.market_data?.iv_rank ?? 11.8).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-[10px] uppercase text-zinc-500">ML Directional</p>
            <div className="flex items-center gap-1.5 font-bold text-amber-400 text-sm">
              <span>BENCHED</span>
              <span className="text-[10px] font-normal text-zinc-500">
                (DSR unvalidated)
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* WORKSPACE MULTI-PANEL GRID */}
      <main className="flex-1 p-4 grid grid-cols-1 lg:grid-cols-12 gap-4 relative z-10 max-w-[1700px] w-full mx-auto">
        {/* ========================================================================= */}
        {/* LEFT COLUMN: LIVE EXECUTION, POSITIONS & ALPACA ORDERS (4 COLS) */}
        {/* ========================================================================= */}
        <div className="lg:col-span-4 space-y-4 flex flex-col">
          {/* Active Positions Panel */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-950 p-3.5 flex-1 flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-900 text-xs">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-bold text-white uppercase text-[11px]">Active Positions ({positions.length})</span>
              </div>
              <span className="text-[10px] text-zinc-500">Auto-Hedged</span>
            </div>

            {positions.length === 0 ? (
              <div className="py-8 text-center text-zinc-600 text-xs border border-dashed border-zinc-900 rounded-lg">
                NO OPEN POSITIONS · 100% CAPITAL SECURED IN CASH
              </div>
            ) : (
              <div className="space-y-2 flex-1">
                {positions.map((p, idx) => {
                  const pl = parseFloat(p?.unrealized_pl ?? "0") || 0;
                  const mv = parseFloat(p?.market_value ?? "0") || 0;
                  return (
                    <div key={idx} className="p-3 rounded-lg bg-black border border-zinc-900 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-white text-sm flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          {p?.symbol}
                        </span>
                        <span className={`font-bold font-mono ${pl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {pl >= 0 ? "+" : ""}${pl.toFixed(2)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px] text-zinc-400 mt-2 pt-2 border-t border-zinc-900">
                        <div>Quantity: <span className="text-white">{p?.qty}</span></div>
                        <div className="text-right">Mkt Value: <span className="text-white">${mv.toFixed(2)}</span></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Alpaca Order Execution Book */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-950 p-3.5 flex-1 flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-900 text-xs">
              <div className="flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-bold text-white uppercase text-[11px]">Order Execution Book</span>
              </div>
              <span className="text-[10px] text-zinc-500">Live Alpaca Stream</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead className="border-b border-zinc-900 text-zinc-500 text-[10px] uppercase">
                  <tr>
                    <th className="pb-2">Contract</th>
                    <th className="pb-2">Side</th>
                    <th className="pb-2 text-right">Qty</th>
                    <th className="pb-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900/60">
                  {orders.slice(0, 7).map((o, idx) => {
                    const isBuy = (o?.side ?? "").toLowerCase() === "buy";
                    const isFilled = (o?.status ?? "").toLowerCase() === "filled";
                    return (
                      <tr key={idx} className="hover:bg-zinc-900/30">
                        <td className="py-2 text-zinc-300 font-bold truncate max-w-[130px]" title={o?.symbol}>
                          {o?.symbol}
                        </td>
                        <td className="py-2">
                          <span className={`text-[9px] px-1 py-0.5 rounded font-bold ${isBuy ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                            {(o?.side ?? "").toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2 text-right text-zinc-400">{o?.filled_qty || o?.qty || "0"}</td>
                        <td className="py-2 text-right">
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${isFilled ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : "bg-zinc-900 text-zinc-400"}`}>
                            {(o?.status ?? "SENT").toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* CENTER COLUMN: MODEL GOVERNANCE & QUANT DSR MATRIX (4 COLS) */}
        {/* ========================================================================= */}
        <div className="lg:col-span-4 space-y-4 flex flex-col">
          {/* ML Momentum Random Forest Telemetry */}
          <div className="rounded-xl border border-amber-950/60 bg-zinc-950 p-4 relative overflow-hidden">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-bold text-white uppercase text-[11px]">Directional ML Engine (Experimental)</span>
              </div>
              <span className="text-[9px] px-1.5 py-0.5 rounded font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                BENCHED BY RISK GATE
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Model Architecture</span>
                <span className="text-white font-bold">Random Forest (5yr Rolling Features)</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Raw Model Probability</span>
                <span className="text-zinc-300">p = {(latestEntry?.ml_momentum?.signal?.confidence ?? 0.491).toFixed(2)} (Neutral / Noise Regime)</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Walk-Forward DSR Validation</span>
                <span className="text-rose-400 font-bold">UNVALIDATED (Fails DSR &gt; 0.95 Hurdle)</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-zinc-500">Governor Directive</span>
                <span className="text-amber-400 font-bold">REFUSED TRADE · NO LIVE EXPOSURE</span>
              </div>
            </div>
          </div>

          {/* VRP Strategy Gate (BENCHED BY DSR) */}
          <div className="rounded-xl border border-rose-950/60 bg-zinc-950 p-4 relative overflow-hidden">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span className="font-bold text-white uppercase text-[11px]">Volatility Risk Premium (VRP) Gate</span>
              </div>
              <span className="text-[9px] px-1.5 py-0.5 rounded font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                BENCHED BY RISK GATE
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Target Strategy</span>
                <span className="text-zinc-300">SPY 4-Leg Iron Condors</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Gross Backtest Sharpe</span>
                <span className="text-amber-400 font-bold">+0.89</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Friction Net Sharpe ($0.48/sh)</span>
                <span className="text-rose-400 font-bold">-0.05 (Negative Expectancy)</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-zinc-900/80">
                <span className="text-zinc-500">Deflated Sharpe Ratio (DSR)</span>
                <span className="text-rose-400 font-bold">0.00% (Statistically Rejected)</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-zinc-500">Governor Directive</span>
                <span className="text-rose-400 font-bold">REFUSED TRADE · STAND DOWN</span>
              </div>
            </div>
          </div>

          {/* Crisis Drawdown Filter Stats */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-950 p-4">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-900 text-[11px] font-bold text-zinc-300 uppercase">
              <span>Historical Crisis Regime Filtering</span>
              <span className="text-zinc-500">Deterministic Protection</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs pt-1">
              <div className="p-2 rounded bg-black border border-zinc-900">
                <p className="text-[10px] text-zinc-500">2008 GFC</p>
                <p className="font-bold text-emerald-400 mt-0.5">-1.09%</p>
                <p className="text-[9px] text-zinc-600">vs -47% SPY</p>
              </div>
              <div className="p-2 rounded bg-black border border-zinc-900">
                <p className="text-[10px] text-zinc-500">2018 Volmageddon</p>
                <p className="font-bold text-emerald-400 mt-0.5">-2.13%</p>
                <p className="text-[9px] text-zinc-600">vs -19% SPY</p>
              </div>
              <div className="p-2 rounded bg-black border border-zinc-900">
                <p className="text-[10px] text-zinc-500">2020 COVID</p>
                <p className="font-bold text-emerald-400 mt-0.5">-2.14%</p>
                <p className="text-[9px] text-zinc-600">vs -34% SPY</p>
              </div>
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT COLUMN: CRYPTOGRAPHIC HASH CHAIN & ON-CHAIN ANCHOR (4 COLS) */}
        {/* ========================================================================= */}
        <div className="lg:col-span-4 space-y-4 flex flex-col">
          {/* Ethereum Sepolia Cryptographic Anchor Panel */}
          <div className="rounded-xl border border-emerald-950/80 bg-zinc-950 p-4 relative overflow-hidden">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-bold text-white uppercase text-[11px]">Ethereum Sepolia Cryptographic Anchor</span>
              </div>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>

            <p className="text-[11px] text-zinc-400 leading-relaxed mb-3">
              The SHA-256 root hash of the verifiable decision log is anchored via transaction memo to the Ethereum Sepolia blockchain. Any post-hoc edits to trades immediately invalidate the chain.
            </p>

            <div className="space-y-2 text-[11px] bg-black p-3 rounded-lg border border-zinc-900">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Transaction Hash (Sepolia L1):</span>
                <a
                  href={`https://sepolia.etherscan.io/tx/${ETHERSCAN_TX}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-400 font-bold hover:underline break-all"
                >
                  {ETHERSCAN_TX}
                </a>
              </div>
              <div className="pt-2 border-t border-zinc-900">
                <span className="text-zinc-500 block text-[10px] uppercase">Anchored Root Hash:</span>
                <span className="text-zinc-300 break-all">
                  {logEntries[0]?.hash || "c54f1a609a82a5d6009ad12931b41d73cd4ba4ed7fddd5aa1c4cfc5d14660c1a"}
                </span>
              </div>
            </div>

            <a
              href={`https://sepolia.etherscan.io/tx/${ETHERSCAN_TX}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 w-full py-2 rounded bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs flex items-center justify-center gap-1.5 transition"
            >
              <span>INSPECT ON ETHERSCAN</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Verifiable Decision Hash Chain Inspector */}
          <div className="rounded-xl border border-zinc-900 bg-zinc-950 p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-purple-400" />
                <span className="font-bold text-white uppercase text-[11px]">
                  Verifiable Decision Log ({logData?.total ?? logEntries.length} Blocks)
                </span>
              </div>
              <div className="flex items-center gap-1 bg-black border border-zinc-800 p-0.5 rounded text-[10px]">
                <button
                  onClick={() => setLogFilter("official")}
                  className={`px-2 py-0.5 rounded transition ${
                    logFilter === "official"
                      ? "bg-zinc-800 text-emerald-400 font-bold"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  PA3LL11TFH7L
                </button>
                <button
                  onClick={() => setLogFilter("all")}
                  className={`px-2 py-0.5 rounded transition ${
                    logFilter === "all"
                      ? "bg-zinc-800 text-zinc-200 font-bold"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  All Blocks
                </button>
              </div>
            </div>

            <div className="space-y-2 overflow-y-auto max-h-[340px] pr-1">
              {logEntries
                .filter((item) => {
                  if (logFilter === "official") {
                    const eq = item?.entry?.market_data?.account_equity;
                    return eq === 100000.0;
                  }
                  return true;
                })
                .map((item, idx) => {
                  const e = item?.entry;
                  const ml = e?.ml_momentum;
                  const vrp = e?.vrp;
                  const tradeable = vrp?.regime_signal?.tradeable ?? false;
                  const reason = vrp?.regime_signal?.reasons?.[0] ?? "Regime evaluated";
                  const isSelected = selectedBlockIndex === idx;
                  const isOfficial = e?.market_data?.account_equity === 100000.0;

                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedBlockIndex(idx)}
                      className={`p-2.5 rounded-lg border transition cursor-pointer text-[11px] ${
                        isSelected
                          ? "bg-zinc-900/90 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.1)]"
                          : "bg-black border-zinc-900 hover:border-zinc-800"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-zinc-500 text-[10px]">
                            {e?.timestamp ? new Date(e.timestamp).toLocaleTimeString() : `Block #${idx}`}
                          </span>
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                              isOfficial
                                ? "bg-emerald-950/80 text-emerald-400 border border-emerald-500/30"
                                : "bg-zinc-900 text-zinc-500 border border-zinc-800"
                            }`}
                          >
                            {isOfficial ? "OFFICIAL" : "SANDBOX"}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <span className={`text-[9px] px-1 py-0.2 rounded font-bold ${tradeable ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-900 text-zinc-500"}`}>
                            VRP:{tradeable ? "GO" : "STAND DOWN"}
                          </span>
                          {ml && (
                            <span className="text-[9px] px-1 py-0.2 rounded font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              ML:BENCHED
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="text-zinc-400 text-[10px] font-mono truncate">
                        HASH: {item?.hash || "Pending..."}
                      </p>
                      <p className="text-zinc-500 text-[10px] truncate mt-0.5">
                        Equity: ${e?.market_data?.account_equity?.toLocaleString() ?? "100,000"} · {reason}
                      </p>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      </main>

      {/* FOOTER TERMINAL STATUS LINE */}
      <footer className="border-t border-zinc-900 bg-black px-4 py-2 text-[11px] flex flex-wrap items-center justify-between gap-2 text-zinc-500">
        <div className="flex items-center gap-4">
          <span className="text-zinc-400 font-bold">CLI COMMANDS:</span>
          <span>python cli.py daemon</span>
          <span>·</span>
          <span>python cli.py run</span>
          <span>·</span>
          <span>python cli.py mcp</span>
          <span>·</span>
          <span>python cli.py drift</span>
        </div>
        <div className="flex items-center gap-3">
          <span>ETH SEPOLIA ANCHOR LIVE</span>
          <span>·</span>
          <span>ALPACA PA3LL11TFH7L</span>
        </div>
      </footer>
    </div>
  );
}
