# VRP-Agent: Autonomous Options Trading

**Hackathon**: Alpaca AI Trading Agents Hackathon
**Track**: Options Trading
**Author**: Aman

## 1. AI Logic & Orchestration

VRP-Agent uses a two-sleeve, multi-node LangGraph pipeline. Both sleeves run independently and converge at a shared deterministic risk gate before any order is submitted.

Unlike many competitors who use a "bull/bear/neutral LLM-debate" architecture, VRP-Agent explicitly rejects LLM debate for directional positioning. Recent research (TiMi, ICLR 2026, arXiv:2510.04787) demonstrates that debate-style anthropomorphic agents introduce emotional bias and drift into consensus thinking. Instead, VRP-Agent relies on **deterministic, mechanical rationality**. The LLM's role is strictly orchestrating the pipeline, summarizing the regime status, and appending to a hash-chained, verifiable log.

**Sleeve 1 — VRP Premium**: SPY iron condors at 45 DTE / 16-delta when regime filter passes (VIX not rising >5%/5d, IV Rank > 25, VIX < 30).

**Sleeve 2 — Earnings IV-Crush**: Iron condors placed 1-3 days before a confirmed earnings print, strikes sized beyond the ATM straddle-implied expected move. Closes immediately after the print. Entry confirmed for LULU (Sep 3 AMC) using live straddle data from yfinance.

## 2. Infrastructure: Alpaca API

The execution and market data layer runs through the **Alpaca Trading API** (`alpaca-py`):
1. **Market Data**: Real-time SPY ask prices via `StockHistoricalDataClient`, VIX regime via yfinance.
2. **Account State**: Live equity and daily P&L from `TradingClient.get_account()`.
3. **Order Execution**: `MarketOrderRequest` / `OptionOrderRequest` submitted to a funded paper account.
4. **Position Monitoring**: `get_all_positions()` used to compute current short-vol exposure before each trade.

Every decision, market state, and execution result is appended to a hash-chained JSON log in `data/verifiable_log.json`.

## 3. Risk Gates (Deterministic — cannot be bypassed)

One gate, one source of truth (`src/risk/gate.py`). Every proposed trade passes through `evaluate()`:

- **Per-Trade Max Loss**: ≤ 2% of account equity.
- **VIX-Scaled Portfolio Cap**: 25% exposure below VIX 22; 15% between VIX 22-30; 5% above VIX 30.
- **Circuit Breaker**: Halts if daily drawdown > 3%.
- **Macro Avoidance**: No entries within 24h of scheduled Fed/macro prints.
- **Earnings Sleeve Bypass**: `is_earnings_sleeve=True` on `ProposedTrade` skips the VIX-regime veto and standard exposure cap — earnings trades have their own uncorrelated risk profile.

## 4. Backtest Results

### VRP Sleeve (2007–Present, `src/backtest/run.py`)

Two models run over 8,197 trading days using VIX as an IV proxy and Black-Scholes pricing:

| Model | CAGR | Sharpe | Max Drawdown |
|---|---|---|---|
| Unconditional selling | 1.67% | 1.62 | -2.06% |
| Regime-filtered (our model) | 0.76% | 0.85 | -2.14% |

**Honest finding**: The regime filter does NOT improve Sharpe or reduce drawdown vs unconditional selling. The filter reduces participation to ~23% of trading days, sacrificing too much premium. The claim that "regime filtering improves risk-adjusted returns" is **dropped from the pitch**. The pitch instead rests on: pre-registered honesty, deterministic risk gates, and the earnings sleeve as an uncorrelated second income stream.

### Earnings Sleeve (`src/backtest/earnings_backtest.py`)

Historical earnings events for LULU and CIEN, using 30-day realized volatility as an IV proxy (true historical IV surfaces require paid data — limitation explicitly disclosed):

| Ticker | Events | Win Rate | Avg P&L | Sharpe |
|---|---|---|---|---|
| LULU | 24 | **79.2%** | $26/event | 0.34 |
| CIEN | 24 | 20.8% | -$95/event | -0.89 |

**CIEN dropped from live trading**: Avg actual move (9.8%) exceeds the 30-day HV proxy (3.1%) by 3x, meaning CIEN regularly gaps far past the short strikes. CIEN's backtest is a genuine loss in this proxy model. **LULU only** remains in the live earnings sleeve.

**Caveat**: These earnings P&L numbers use credit estimated at 30% of wing width (conservative). True P&L requires live historical IV data. Numbers should be treated as directional proxies, not precise forecasts.

## 5. Known Limitations (per Pre-Registration §6)

- VRP backtest options pricing approximated via VIX (no free historical IV surface data).
- Earnings backtest uses 30-day HV as IV proxy, not actual pre-earnings implied volatility.
- The live trading window is ~4.5 sessions (Aug 31–Sep 4) — insufficient for statistical proof of edge; backtest is the evidence base.
- Early assignment risk on short legs not fully simulated in paper trading.
- The pre-registration required a dated addendum (Aug 23) to fix a logical contradiction in the original regime filter (IV Rank > 50 AND VIX < 200DMA were mutually exclusive conditions that caused 93% sit-out rate).
