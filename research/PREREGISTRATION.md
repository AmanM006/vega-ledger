# Pre-Registration — VRP + Regime-Filtered Options Agent

**Timestamp (UTC):** 2026-08-23T13:00:11Z
**Author:** Aman
**Status:** Written BEFORE any backtest code exists in this repo. Git history proves this.

This document locks the thesis, entry/exit rules, and risk limits before touching
historical data. Nothing below may be changed after backtest code is written without
a dated addendum explaining why — edits to this file after backtest results exist are
the definition of p-hacking.

---

## 1. Core thesis

Implied volatility on SPY options is priced above subsequently realized volatility
on average (documented VRP, ~2-4 IV points, decades of literature). Selling
defined-risk premium captures this gap. The edge is NOT "predict direction" — it's
"collect a persistent structural mispricing while capping tail risk."

## 2. Primary strategy — VRP premium selling

- **Instrument:** SPY iron condors / credit spreads, 30-45 DTE at entry
- **Entry filter (regime-conditional — this is the whole point):**
  - IV rank > 50 AND IV percentile > 50 on SPY
  - VIX below its own 200-day moving average AND not rising >5% over prior 5 sessions
  - No entry if VIX > 30
- **Sizing:** total short-vol exposure capped at 20-25% of buying power. VIX 22-30 →
  cap reduced to 15%. VIX > 30 → 5% or flat.
- **Exit:** 50% max-profit target OR 21 DTE remaining OR stop at 2x credit received,
  whichever comes first.
- **Strikes:** ~16-delta short strikes (defined-risk wings beyond expected move).

## 3. Secondary strategy — earnings IV crush

- **Trigger:** confirmed earnings date inside the trading window for a liquid,
  optionable name (checked against corporate-actions/earnings calendar via MCP).
- **Structure:** iron condor placed 1-3 days pre-earnings, strikes beyond the
  straddle-implied expected move.
- **Exit:** close immediately after the print (IV crush captured), do not hold
  directional risk overnight past the event.
- **Purpose:** uncorrelated sleeve so the agent has legitimate activity even in a
  quiet, low-VIX week where the primary strategy stays flat.

## 4. Risk gate (deterministic, non-LLM, cannot be overridden by any model output)

- Per-trade max loss ≤ 2% of account equity
- Portfolio short-vol exposure cap per §2
- Daily loss circuit breaker: halt new entries if daily drawdown > X% (set X during
  backtest calibration, document the chosen value here once fixed)
- Kill switch: manual + automatic (drawdown-triggered) full-halt capability
- No new short-vol entries within 24h of a scheduled Fed/macro print unless already
  inside an earnings-sleeve trade

## 5. What would falsify this thesis

- If backtest shows the regime filter does NOT improve Sharpe / drawdown vs.
  unconditional selling, the regime-filter differentiation claim is dropped and
  reported honestly, not hidden.
- If the earnings sleeve shows negative expectancy in backtest, it is cut before
  the hackathon, not run live "for demo purposes."

## 6. Known limitations (disclosed up front)

- Backtest options data quality/availability is limited on free sources — actual
  historical IV surfaces may be approximated via realized-vol proxies where
  necessary. This will be stated explicitly in the write-up, not glossed over.
- Live trading window is ~4.5 sessions (Aug 31 – Sep 4). Not enough trades for the
  VRP edge to prove out statistically in-sample; the backtest is the actual evidence
  base, the live week is a demonstration, not a proof.
- Early assignment risk on short legs is a known, documented gap — not fully
  simulated in paper trading.
