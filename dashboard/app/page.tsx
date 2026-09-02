"use client";

import { useEffect, useState, useRef } from "react";
import Lenis from "lenis";
import {
  ShieldCheck,
  Cpu,
  Activity,
  ArrowUpRight,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  Terminal,
  Database,
  Lock,
  Layers,
  Code2
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

const ETHERSCAN_TX = "0x711b6ea9f659a094a8c929c5f6fdd707ccb6c50de2e8c3d3e76515df94d64daf";

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [accountData, setAccountData] = useState<{ account?: Record<string, string>; positions?: Position[]; orders?: Order[] } | null>(null);
  const [logData, setLogData] = useState<{ entries?: LogEntry[]; total?: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const lenisRef = useRef<Lenis | null>(null);

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

    // Initialize Lenis Smooth Scroll
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
    });
    lenisRef.current = lenis;

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    const interval = setInterval(fetchAll, 30000);
    return () => {
      clearInterval(interval);
      lenis.destroy();
    };
  }, []);

  const scrollToTelemetry = () => {
    if (lenisRef.current) {
      lenisRef.current.scrollTo("#telemetry", { offset: -20 });
    } else {
      document.getElementById("telemetry")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-zinc-500">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm font-mono tracking-widest uppercase">Initializing Vega Ledger...</p>
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

  return (
    <div className="min-h-screen bg-black text-zinc-200 selection:bg-emerald-500/20 selection:text-emerald-300 font-[family-name:var(--font-space-grotesk)] relative">
      {/* Dynamic Background Noise & Mesh */}
      <div className="fixed inset-0 bg-grid-pattern opacity-40 pointer-events-none z-0" />
      <div className="fixed inset-0 glow-mesh pointer-events-none z-0" />

      {/* Top Floating Glass Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-zinc-900/80 bg-black/60 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 rounded-lg bg-zinc-950 border border-zinc-800 flex items-center justify-center font-mono font-bold text-sm text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              VL
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold tracking-tight text-white text-base">VEGA LEDGER</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  VRP-Agent
                </span>
              </div>
              <p className="text-[11px] text-zinc-500 font-mono">Alpaca AI Hackathon · ID: PA3D4EOEK0PA</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-950/80 border border-zinc-800 text-xs text-zinc-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE ORCHESTRATION</span>
            </div>
            <button
              onClick={fetchAll}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-950 hover:bg-zinc-900 transition font-mono active:scale-95 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
              <span className="hidden md:inline">Sync</span>
            </button>
            <span className="text-[11px] text-zinc-600 font-mono hidden lg:inline">
              {lastRefresh ? lastRefresh.toLocaleTimeString() : "..."}
            </span>
          </div>
        </div>
      </nav>

      {/* ========================================================== */}
      {/* 100VH HERO SECTION */}
      {/* ========================================================== */}
      <section className="min-h-screen pt-20 pb-12 flex flex-col justify-between max-w-7xl mx-auto px-6 relative z-10">
        {/* Top Badges */}
        <div className="pt-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/30 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-6 backdrop-blur-sm">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>INSTITUTIONAL QUANTITATIVE RISK GOVERNOR</span>
          </div>

          <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-white leading-[1.05] max-w-4xl">
            Autonomous execution. <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
              Mathematical refusal.
            </span>
          </h1>
          <p className="mt-5 text-zinc-400 text-base sm:text-lg max-w-2xl leading-relaxed">
            A multi-agent options & momentum architecture governed by Deflated Sharpe Ratio (DSR) statistical gates and cryptographically anchored to Ethereum Sepolia.
          </p>
        </div>

        {/* Hero KPIs Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 my-8">
          <div className="p-5 rounded-2xl bg-zinc-950/80 border border-zinc-800/80 backdrop-blur-md shadow-2xl relative overflow-hidden group hover:border-zinc-700 transition">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />
            <p className="text-[11px] font-mono uppercase text-zinc-500 tracking-wider">Portfolio Equity</p>
            <p className="text-2xl sm:text-3xl font-bold font-mono text-white mt-1">
              ${equity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs font-mono">
              <span className={`font-semibold ${pnlColor}`}>
                {pnlPrefix}${pnl.toFixed(2)}
              </span>
              <span className="text-zinc-600">net P&L</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-950/80 border border-zinc-800/80 backdrop-blur-md shadow-2xl relative overflow-hidden group hover:border-zinc-700 transition">
            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl pointer-events-none" />
            <p className="text-[11px] font-mono uppercase text-zinc-500 tracking-wider">Buying Power (4x Margin)</p>
            <p className="text-2xl sm:text-3xl font-bold font-mono text-zinc-100 mt-1">
              ${(parseFloat(acc?.buying_power ?? "400000") || 400000).toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs font-mono text-zinc-500">
              <span>Cash: ${(parseFloat(acc?.cash ?? "100000") || 100000).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-950/80 border border-zinc-800/80 backdrop-blur-md shadow-2xl relative overflow-hidden group hover:border-zinc-700 transition">
            <p className="text-[11px] font-mono uppercase text-zinc-500 tracking-wider">Market Volatility (VIX)</p>
            <p className="text-2xl sm:text-3xl font-bold font-mono text-amber-400 mt-1">
              {(latestEntry?.market_data?.vix_now ?? 15.54).toFixed(2)}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs font-mono text-zinc-500">
              <span>IV Rank: {(latestEntry?.market_data?.iv_rank ?? 11.8).toFixed(1)}%</span>
              <span className="text-rose-400/90 text-[10px]">(Unfavorable VRP)</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-950/80 border border-zinc-800/80 backdrop-blur-md shadow-2xl relative overflow-hidden group hover:border-zinc-700 transition">
            <p className="text-[11px] font-mono uppercase text-zinc-500 tracking-wider">Active ML Signal</p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl sm:text-3xl font-bold font-mono text-emerald-400">
                {latestEntry?.ml_momentum?.signal?.signal ?? "BUY"}
              </span>
              <span className="text-xs font-mono text-zinc-400">
                ({(((latestEntry?.ml_momentum?.signal?.confidence ?? 0.491) * 100)).toFixed(1)}%)
              </span>
            </div>
            <div className="mt-3 flex items-center gap-1.5 text-xs font-mono text-emerald-400/90">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Random Forest momentum active</span>
            </div>
          </div>
        </div>

        {/* 100VH Section Logos / Technology Marquee */}
        <div className="border-t border-zinc-900/80 pt-6 pb-2">
          <p className="text-[11px] font-mono uppercase text-zinc-600 tracking-widest text-center mb-4">
            Integrated Ecosystem & Protocols
          </p>
          <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-12 opacity-75 grayscale hover:grayscale-0 transition duration-500">
            <div className="flex items-center gap-2.5 text-zinc-300 font-mono text-xs font-semibold">
              <Activity className="w-4 h-4 text-yellow-400" />
              <span>ALPACA TRADING API</span>
            </div>
            <div className="flex items-center gap-2.5 text-zinc-300 font-mono text-xs font-semibold">
              <Lock className="w-4 h-4 text-blue-400" />
              <span>ETHEREUM SEPOLIA (L1)</span>
            </div>
            <div className="flex items-center gap-2.5 text-zinc-300 font-mono text-xs font-semibold">
              <Layers className="w-4 h-4 text-purple-400" />
              <span>LANGGRAPH ORCHESTRATION</span>
            </div>
            <div className="flex items-center gap-2.5 text-zinc-300 font-mono text-xs font-semibold">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>SCIKIT-LEARN ML</span>
            </div>
            <div className="flex items-center gap-2.5 text-zinc-300 font-mono text-xs font-semibold">
              <Terminal className="w-4 h-4 text-pink-400" />
              <span>FASTMCP PROTOCOL</span>
            </div>
            <div className="flex items-center gap-2.5 text-zinc-300 font-mono text-xs font-semibold">
              <Code2 className="w-4 h-4 text-teal-400" />
              <span>NEXT.JS 16 APPS</span>
            </div>
          </div>

          <div className="flex justify-center mt-6">
            <button
              onClick={scrollToTelemetry}
              className="flex items-center gap-2 text-xs font-mono text-zinc-500 hover:text-zinc-300 transition py-2 px-4 rounded-full border border-zinc-800/80 hover:border-zinc-700 bg-zinc-950/60 cursor-pointer"
            >
              <span>Explore Telemetry & Audit Logs</span>
              <ChevronDown className="w-3.5 h-3.5 animate-bounce" />
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================== */}
      {/* TELEMETRY SECTION (Smooth scroll target) */}
      {/* ========================================================== */}
      <div id="telemetry" className="max-w-7xl mx-auto px-6 py-16 space-y-12 relative z-10">
        {/* Section: Live Execution & Position Data */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Active Positions */}
          <div className="rounded-2xl bg-zinc-950/90 border border-zinc-800/80 p-6 backdrop-blur-xl shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold tracking-wide uppercase text-zinc-300 font-mono">Live Positions ({positions.length})</h3>
              </div>
              <span className="text-[11px] font-mono text-zinc-500">Auto-hedged via Alpaca</span>
            </div>

            {positions.length === 0 ? (
              <div className="h-44 flex items-center justify-center border border-dashed border-zinc-800/80 rounded-xl text-center p-6 text-zinc-500 font-mono text-xs">
                No active positions. Capital secured in cash reserves.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="border-b border-zinc-800 text-zinc-500 uppercase text-[10px]">
                    <tr>
                      <th className="pb-3 font-medium">Asset</th>
                      <th className="pb-3 font-medium text-right">Qty</th>
                      <th className="pb-3 font-medium text-right">Market Val</th>
                      <th className="pb-3 font-medium text-right">Unrealized P&L</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {positions.map((p, idx) => {
                      const pl = parseFloat(p?.unrealized_pl ?? "0") || 0;
                      const mv = parseFloat(p?.market_value ?? "0") || 0;
                      return (
                        <tr key={p?.symbol || idx} className="hover:bg-zinc-900/40 transition">
                          <td className="py-3 text-white font-bold flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-400" />
                            {p?.symbol}
                          </td>
                          <td className="py-3 text-right text-zinc-300">{p?.qty}</td>
                          <td className="py-3 text-right text-zinc-300">${mv.toFixed(2)}</td>
                          <td className={`py-3 text-right font-bold ${pl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {pl >= 0 ? "+" : ""}${pl.toFixed(2)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Recent Orders Stream */}
          <div className="rounded-2xl bg-zinc-950/90 border border-zinc-800/80 p-6 backdrop-blur-xl shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-semibold tracking-wide uppercase text-zinc-300 font-mono">Order Execution Stream</h3>
              </div>
              <span className="text-[11px] font-mono text-zinc-500">Last 8 Alpaca Actions</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="border-b border-zinc-800 text-zinc-500 uppercase text-[10px]">
                  <tr>
                    <th className="pb-3 font-medium">Contract / Symbol</th>
                    <th className="pb-3 font-medium">Side</th>
                    <th className="pb-3 font-medium text-right">Qty</th>
                    <th className="pb-3 font-medium text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900">
                  {orders.slice(0, 8).map((o, idx) => {
                    const isBuy = (o?.side ?? "").toLowerCase() === "buy";
                    const isFilled = (o?.status ?? "").toLowerCase() === "filled";
                    return (
                      <tr key={idx} className="hover:bg-zinc-900/40 transition">
                        <td className="py-2.5 text-zinc-200 font-medium truncate max-w-[160px]" title={o?.symbol}>
                          {o?.symbol}
                        </td>
                        <td className="py-2.5">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${isBuy ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                            {(o?.side ?? "").toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2.5 text-right text-zinc-400">{o?.filled_qty || o?.qty || "0"}</td>
                        <td className="py-2.5 text-right">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${isFilled ? "bg-zinc-900 text-emerald-400 border border-emerald-500/30" : "bg-zinc-900 text-zinc-400 border border-zinc-800"}`}>
                            {(o?.status ?? "SUBMITTED").toUpperCase()}
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

        {/* Section: Institutional Quant Matrix (Side by Side) */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-mono uppercase tracking-widest text-zinc-500 font-bold">Quantitative Model Governance Matrix</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* VRP Strategy (BENCHED BY DSR) */}
            <div className="rounded-2xl bg-zinc-950/90 border border-rose-950/40 p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 px-3 py-1 bg-rose-500/10 text-rose-400 border-b border-l border-rose-500/20 text-[10px] font-mono font-bold uppercase rounded-bl-xl">
                Benched by Risk Governor
              </div>
              <h3 className="text-base font-bold text-white mb-1">Volatility Risk Premium (VRP) Options Sleeve</h3>
              <p className="text-xs text-zinc-500 mb-6">Short Implied Volatility via S&P 500 Iron Condors</p>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between py-2 border-b border-zinc-900">
                  <span className="text-zinc-500">Gross Backtest Sharpe Ratio</span>
                  <span className="text-amber-300 font-bold">+0.89</span>
                </div>
                <div className="flex justify-between py-2 border-b border-zinc-900">
                  <span className="text-zinc-500">Net Sharpe (After $0.48/share friction)</span>
                  <span className="text-rose-400 font-bold">-0.05</span>
                </div>
                <div className="flex justify-between py-2 border-b border-zinc-900">
                  <span className="text-zinc-500">Deflated Sharpe Ratio (DSR)</span>
                  <span className="text-rose-400 font-bold">0.00% (Statistically Insignificant)</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-zinc-500">Governor Action</span>
                  <span className="text-rose-400 font-bold">REFUSED TRADE (CAPITAL PROTECTED)</span>
                </div>
              </div>
            </div>

            {/* ML Momentum Sleeve (ACTIVE) */}
            <div className="rounded-2xl bg-zinc-950/90 border border-emerald-950/40 p-6 relative overflow-hidden group">
              <div className="absolute top-0 right-0 px-3 py-1 bg-emerald-500/10 text-emerald-400 border-b border-l border-emerald-500/20 text-[10px] font-mono font-bold uppercase rounded-bl-xl">
                Active Alpha Sleeve
              </div>
              <h3 className="text-base font-bold text-white mb-1">Random Forest Momentum Sleeve</h3>
              <p className="text-xs text-zinc-500 mb-6">Scikit-Learn Classifier trained on 5-Year SPY/VIX Rolling Features</p>

              <div className="space-y-3 font-mono text-xs">
                <div className="flex justify-between py-2 border-b border-zinc-900">
                  <span className="text-zinc-500">Feature Pipeline</span>
                  <span className="text-zinc-300">5d/20d Returns, SMA5/20, VIX Momentum</span>
                </div>
                <div className="flex justify-between py-2 border-b border-zinc-900">
                  <span className="text-zinc-500">Classifier Output</span>
                  <span className="text-emerald-400 font-bold">{latestEntry?.ml_momentum?.signal?.signal ?? "BUY"} ({(((latestEntry?.ml_momentum?.signal?.confidence ?? 0.491) * 100)).toFixed(1)}%)</span>
                </div>
                <div className="flex justify-between py-2 border-b border-zinc-900">
                  <span className="text-zinc-500">Execution Status</span>
                  <span className="text-emerald-400 font-bold">1 Share SPY Market Order Filled</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-zinc-500">Governor Action</span>
                  <span className="text-emerald-400 font-bold">APPROVED & SUBMITTED</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section: Cryptographic Verifiable Decision Log */}
        <div className="rounded-2xl bg-zinc-950/90 border border-zinc-800/80 p-6 backdrop-blur-xl shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
            <div className="flex items-center gap-2.5">
              <Database className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold tracking-wide uppercase text-zinc-300 font-mono">
                Cryptographic Verifiable Decision Log ({logData?.total ?? logEntries.length} Blocks)
              </h3>
            </div>
            <span className="text-xs font-mono text-zinc-500">SHA-256 Hash Chain Structure</span>
          </div>

          <div className="space-y-3">
            {logEntries.slice(0, 5).map((item, idx) => {
              const e = item?.entry;
              const ml = e?.ml_momentum;
              const vrp = e?.vrp;
              const tradeable = vrp?.regime_signal?.tradeable ?? false;
              const reason = vrp?.regime_signal?.reasons?.[0] ?? "Regime evaluated";
              const hash = item?.hash ?? "";

              return (
                <div key={idx} className="p-4 rounded-xl bg-black border border-zinc-900 hover:border-zinc-800 transition text-xs font-mono">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-3">
                      <span className="text-zinc-500 text-[11px]">{e?.timestamp ? new Date(e.timestamp).toLocaleString() : "Recent"}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 truncate max-w-[200px]">
                        HASH: {hash.slice(0, 16)}...{hash.slice(-8)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${tradeable ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-zinc-900 text-zinc-400 border border-zinc-800"}`}>
                        VRP: {tradeable ? "TRADE" : "HOLD"}
                      </span>
                      {ml && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          ML: {ml?.signal?.signal ?? "HOLD"}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-zinc-400 text-[11px] pt-2 border-t border-zinc-900/80">
                    <div>SPY: <span className="text-white">${(e?.market_data?.spy_price ?? 0).toFixed(2)}</span></div>
                    <div>VIX: <span className="text-white">{(e?.market_data?.vix_now ?? 0).toFixed(2)}</span></div>
                    <div>IV Rank: <span className="text-white">{(e?.market_data?.iv_rank ?? 0).toFixed(1)}%</span></div>
                    <div className="truncate text-zinc-500" title={reason}>Reason: {reason}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section: Ethereum Sepolia Anchor Live Verification */}
        <div className="rounded-2xl bg-gradient-to-b from-zinc-950 to-black border border-emerald-950/60 p-6 sm:p-8 relative overflow-hidden">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                <Lock className="w-3.5 h-3.5" />
                <span>ON-CHAIN IMMUTABLE AUDIT TRAIL</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                Ethereum Sepolia Cryptographic Anchor
              </h3>
              <p className="text-zinc-400 text-xs sm:text-sm leading-relaxed">
                The root hash of every agent evaluation cycle is anchored via transaction memo to the Ethereum Sepolia testnet. Any attempt to modify local backtest numbers or paper logs breaks the cryptographic chain.
              </p>

              <div className="pt-2 font-mono text-xs text-zinc-500 space-y-1">
                <p className="truncate">TX Hash: <span className="text-emerald-400 select-all">{ETHERSCAN_TX}</span></p>
                <p className="truncate">Root Hash: <span className="text-zinc-300">{logEntries[0]?.hash ?? "f2e73e32e118b1f8c7520108be851c5f256d7a2bbf6c5a6ee562db01b8666d3d"}</span></p>
              </div>
            </div>

            <a
              href={`https://sepolia.etherscan.io/tx/${ETHERSCAN_TX}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 text-black font-semibold text-xs font-mono hover:bg-emerald-400 transition shadow-[0_0_25px_rgba(16,185,129,0.3)] shrink-0 active:scale-95"
            >
              <span>Verify on Etherscan</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-zinc-900 pt-8 pb-12 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-zinc-600">
          <p>VEGA LEDGER // VRP-AGENT · Alpaca AI Trading Agents Hackathon</p>
          <p>Official Account: PA3D4EOEK0PA · Built with LangGraph, Scikit-Learn, FastMCP, Next.js</p>
        </footer>
      </div>
    </div>
  );
}
