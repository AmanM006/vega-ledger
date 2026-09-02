"use client";

import { useEffect, useState } from "react";

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
  entry: {
    timestamp: string;
    market_data: {
      spy_price: number;
      vix_now: number;
      iv_rank: number;
      account_equity: number;
    };
    vrp: { regime_signal: { tradeable: boolean; reasons: string[] }; execution_result: { status: string } };
    ml_momentum?: { signal: { signal: string; confidence: number; reason: string }; execution: { status: string } };
    earnings: { setups: Array<{ ticker: string; tradeable: boolean; reject_reason?: string }> };
  };
  hash: string;
}

const ETHERSCAN_TX = "0x711b6ea9f659a094a8c929c5f6fdd707ccb6c50de2e8c3d3e76515df94d64daf";

function Stat({ label, value, color = "text-white" }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-[#12121a] rounded-xl p-4 border border-gray-800">
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-bold font-mono ${color}`}>{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    executed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    skipped: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-mono ${colors[status] ?? "bg-gray-700 text-gray-300"}`}>
      {status.toUpperCase()}
    </span>
  );
}

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [accountData, setAccountData] = useState<{ account: Record<string, string>; positions: Position[]; orders: Order[] } | null>(null);
  const [logData, setLogData] = useState<{ entries: LogEntry[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchAll = async () => {
    try {
      const [acc, log] = await Promise.all([
        fetch("/api/account").then((r) => r.json()),
        fetch("/api/log").then((r) => r.json()),
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
    const interval = setInterval(fetchAll, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm font-mono">Initializing Vega Ledger Dashboard...</p>
        </div>
      </div>
    );
  }

  const acc = accountData?.account;
  const positions = accountData?.positions ?? [];
  const orders = accountData?.orders ?? [];
  const logEntries = logData?.entries ?? [];
  const latestEntry = logEntries[0]?.entry;

  const equity = parseFloat(acc?.equity ?? "100000");
  const pnl = equity - 100000;
  const pnlColor = pnl >= 0 ? "text-emerald-400" : "text-red-400";
  const pnlStr = `${pnl >= 0 ? "+" : ""}$${pnl.toFixed(2)}`;

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Header */}
      <div className="border-b border-gray-800 bg-[#0d0d14]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-sm font-bold">V</div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">VRP-Agent</h1>
              <p className="text-xs text-gray-500">Institutional Autonomous Trading · PA3D4EOEK0PA</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-gray-400">Live · Paper Trading</span>
            </div>
            <button onClick={fetchAll} className="text-xs text-gray-500 hover:text-gray-300 transition px-3 py-1.5 rounded-lg border border-gray-800 hover:border-gray-600">
              Refresh
            </button>
            <span className="text-xs text-gray-600">Updated {lastRefresh ? lastRefresh.toLocaleTimeString() : "..."}</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p>Loading live data...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Account Stats */}
            <section>
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Account Overview</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Stat label="Total Equity" value={`$${parseFloat(acc?.equity ?? "0").toLocaleString("en-US", { minimumFractionDigits: 2 })}`} />
                <Stat label="Total P&L" value={pnlStr} color={pnlColor} />
                <Stat label="Cash" value={`$${parseFloat(acc?.cash ?? "0").toLocaleString("en-US", { minimumFractionDigits: 2 })}`} />
                <Stat label="Buying Power" value={`$${parseFloat(acc?.buying_power ?? "0").toLocaleString("en-US", { minimumFractionDigits: 2 })}`} />
              </div>
            </section>

            {/* Live Market Snapshot */}
            {latestEntry && (
              <section>
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Live Market Snapshot</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Stat label="SPY Price" value={`$${latestEntry.market_data.spy_price.toFixed(2)}`} />
                  <Stat label="VIX" value={latestEntry.market_data.vix_now.toFixed(2)} />
                  <Stat label="IV Rank" value={`${latestEntry.market_data.iv_rank.toFixed(1)}%`} />
                  <Stat label="Account Equity" value={`$${latestEntry.market_data.account_equity.toLocaleString()}`} />
                </div>
              </section>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              {/* Open Positions */}
              <section>
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Open Positions</h2>
                <div className="bg-[#12121a] rounded-xl border border-gray-800 overflow-hidden">
                  {positions.length === 0 ? (
                    <div className="p-8 text-center text-gray-600">
                      <p>No open positions · Agent in cash-preservation mode</p>
                    </div>
                  ) : (
                    <table className="w-full text-sm">
                      <thead className="border-b border-gray-800">
                        <tr className="text-xs text-gray-500 uppercase">
                          <th className="px-4 py-3 text-left">Symbol</th>
                          <th className="px-4 py-3 text-right">Qty</th>
                          <th className="px-4 py-3 text-right">Market Value</th>
                          <th className="px-4 py-3 text-right">Unrealized P&L</th>
                        </tr>
                      </thead>
                      <tbody>
                        {positions.map((p) => {
                          const pl = parseFloat(p.unrealized_pl);
                          return (
                            <tr key={p.symbol} className="border-b border-gray-800/50">
                              <td className="px-4 py-3 font-mono font-bold text-blue-400">{p.symbol}</td>
                              <td className="px-4 py-3 text-right text-gray-300">{p.qty}</td>
                              <td className="px-4 py-3 text-right font-mono">${parseFloat(p.market_value).toFixed(2)}</td>
                              <td className={`px-4 py-3 text-right font-mono ${pl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                                {pl >= 0 ? "+" : ""}${pl.toFixed(2)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  )}
                </div>
              </section>

              {/* Recent Orders */}
              <section>
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Recent Orders</h2>
                <div className="bg-[#12121a] rounded-xl border border-gray-800 overflow-hidden">
                  {orders.length === 0 ? (
                    <div className="p-8 text-center text-gray-600">No orders yet</div>
                  ) : (
                    <table className="w-full text-sm">
                      <thead className="border-b border-gray-800">
                        <tr className="text-xs text-gray-500 uppercase">
                          <th className="px-4 py-3 text-left">Symbol</th>
                          <th className="px-4 py-3 text-left">Side</th>
                          <th className="px-4 py-3 text-right">Qty</th>
                          <th className="px-4 py-3 text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.slice(0, 8).map((o, i) => (
                          <tr key={i} className="border-b border-gray-800/50">
                            <td className="px-4 py-3 font-mono text-blue-400 text-xs">{o.symbol.slice(0, 18)}</td>
                            <td className={`px-4 py-3 text-xs ${o.side === "buy" ? "text-emerald-400" : "text-red-400"}`}>{o.side.toUpperCase()}</td>
                            <td className="px-4 py-3 text-right font-mono">{o.filled_qty || o.qty}</td>
                            <td className="px-4 py-3 text-right"><StatusBadge status={o.status} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </section>
            </div>

            {/* Agent Decision Log */}
            <section>
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">
                Verifiable Decision Log · {logData?.total ?? 0} total entries
              </h2>
              <div className="space-y-3">
                {logEntries.slice(0, 5).map((item, i) => {
                  const e = item.entry;
                  const ml = e.ml_momentum;
                  const vrp = e.vrp;
                  return (
                    <div key={i} className="bg-[#12121a] rounded-xl border border-gray-800 p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <p className="text-xs text-gray-400 font-mono">{new Date(e.timestamp).toLocaleString()}</p>
                          <p className="text-xs text-gray-600 font-mono mt-0.5">Hash: {item.hash.slice(0, 20)}...{item.hash.slice(-8)}</p>
                        </div>
                        <div className="flex gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${vrp.regime_signal.tradeable ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-gray-700 text-gray-400 border-gray-600"}`}>
                            VRP: {vrp.regime_signal.tradeable ? "TRADE" : "HOLD"}
                          </span>
                          {ml && (
                            <span className={`text-xs px-2 py-0.5 rounded-full border ${ml.signal?.signal === "BUY" ? "bg-blue-500/20 text-blue-400 border-blue-500/30" : "bg-gray-700 text-gray-400 border-gray-600"}`}>
                              ML: {ml.signal?.signal ?? "HOLD"}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-xs text-gray-500">
                        <div>SPY: <span className="text-gray-300 font-mono">${e.market_data.spy_price.toFixed(2)}</span></div>
                        <div>VIX: <span className="text-gray-300 font-mono">{e.market_data.vix_now.toFixed(2)}</span></div>
                        <div>IV Rank: <span className="text-gray-300 font-mono">{e.market_data.iv_rank.toFixed(1)}%</span></div>
                      </div>
                      {!vrp.regime_signal.tradeable && (
                        <p className="text-xs text-gray-600 mt-2 font-mono">Reason: {vrp.regime_signal.reasons?.[0]}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Strategy Performance */}
            <section>
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">Validated Strategy Performance</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-[#12121a] rounded-xl border border-red-900/30 p-5">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-sm">VRP Options Strategy</h3>
                      <p className="text-xs text-gray-500 mt-0.5">Sell IV overpricing via Iron Condors</p>
                    </div>
                    <span className="text-xs bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">BENCHED</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-gray-500">Gross Sharpe</span><span className="font-mono text-yellow-400">+0.89</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Net Sharpe (after $0.48/sh friction)</span><span className="font-mono text-red-400">-0.05</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Deflated Sharpe Ratio (DSR)</span><span className="font-mono text-red-400">0.00%</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Walk-Forward Pass</span><span className="font-mono text-red-400">FAIL</span></div>
                  </div>
                  <p className="text-xs text-gray-600 mt-4 border-t border-gray-800 pt-3">Strategy correctly rejected: edge destroyed by transaction friction.</p>
                </div>
                <div className="bg-[#12121a] rounded-xl border border-blue-900/30 p-5">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-sm">ML Momentum Sleeve</h3>
                      <p className="text-xs text-gray-500 mt-0.5">Random Forest on 5yr SPY/VIX data</p>
                    </div>
                    <span className="text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full">ACTIVE</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    {latestEntry?.ml_momentum ? (
                      <>
                        <div className="flex justify-between"><span className="text-gray-500">Current Signal</span><span className="font-mono text-blue-400">{latestEntry.ml_momentum.signal?.signal ?? "—"}</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Confidence</span><span className="font-mono text-blue-400">{((latestEntry.ml_momentum.signal?.confidence ?? 0) * 100).toFixed(1)}%</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Last Execution</span><StatusBadge status={latestEntry.ml_momentum.execution?.status ?? "unknown"} /></div>
                      </>
                    ) : (
                      <p className="text-gray-600 text-xs">No ML data in log yet. Run agent to generate.</p>
                    )}
                    <div className="flex justify-between"><span className="text-gray-500">Features</span><span className="font-mono text-gray-300 text-xs">SMA5, SMA20, VIX-ret, SPY-ret</span></div>
                  </div>
                </div>
              </div>
            </section>

            {/* Blockchain Anchor */}
            <section>
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4">On-Chain Cryptographic Audit Trail</h2>
              <div className="bg-[#12121a] rounded-xl border border-emerald-900/30 p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg shrink-0">⛓</div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-emerald-400">Ethereum Sepolia Anchor — Verified Live</h3>
                    <p className="text-xs text-gray-500 mt-1">The SHA-256 root hash of every agent decision log is anchored to the Ethereum Sepolia testnet. This makes the log tamper-evident and cryptographically immutable.</p>
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center gap-3 bg-[#0a0a0f] rounded-lg p-3 border border-gray-800">
                        <span className="text-xs text-gray-500 shrink-0">TX Hash:</span>
                        <a href={`https://sepolia.etherscan.io/tx/${ETHERSCAN_TX}`} target="_blank" rel="noopener noreferrer" className="text-xs font-mono text-emerald-400 hover:underline truncate">
                          {ETHERSCAN_TX}
                        </a>
                      </div>
                      <div className="flex items-center gap-3 bg-[#0a0a0f] rounded-lg p-3 border border-gray-800">
                        <span className="text-xs text-gray-500 shrink-0">Latest Log Hash:</span>
                        <span className="text-xs font-mono text-gray-300 truncate">{logEntries[0]?.hash ?? "—"}</span>
                      </div>
                    </div>
                    <a href={`https://sepolia.etherscan.io/tx/${ETHERSCAN_TX}`} target="_blank" rel="noopener noreferrer" className="mt-4 inline-flex items-center gap-2 text-xs text-emerald-400 hover:text-emerald-300 transition">
                      View on Etherscan →
                    </a>
                  </div>
                </div>
              </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-gray-800 pt-6 pb-2 text-center text-xs text-gray-700">
              VRP-Agent · Alpaca AI Trading Agents Hackathon · Account PA3D4EOEK0PA · Built with LangGraph, Scikit-Learn, MCP, Next.js
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
