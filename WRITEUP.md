# VRP-Agent: Autonomous Options Trading

**Hackathon**: Alpaca AI Trading Agents Hackathon
**Track**: Options Trading
**Author**: Aman

## 1. AI Logic & Architecture

VRP-Agent uses an orchestrated multi-agent framework built with **LangGraph** to process market data and manage state. The architecture consists of a two-sleeve pipeline:
- **VRP Premium Sleeve**: Proposes SPY iron condors at 45 DTE / 16-delta when a regime filter passes.
- **Earnings IV-Crush Sleeve**: Proposes symmetric iron condors 1-3 days before confirmed earnings prints, sizing strikes strictly outside the straddle-implied move.

Both parallel nodes feed independently into a **single, unified deterministic risk gate**. The LLM's role is strictly orchestrating the pipeline, pulling structured market data via the Alpaca API, summarizing the regime status, and appending to a hash-chained, verifiable log.

## 2. Risk Gate

We utilize a rigorously tested, non-LLM risk gate (`src/risk/gate.py`) that cannot be bypassed. This includes:
- **Per-Trade Max Loss**: Hard cap at ≤ 2% of account equity.
- **VIX-Scaled Portfolio Cap**: 25% exposure below VIX 22; 15% between VIX 22-30; 5% above VIX 30.
- **Circuit Breaker**: Halts trading entirely if daily drawdown > 3%.
- **Macro Avoidance**: No entries within 24h of scheduled Fed/macro prints.

Why deterministic? Options risk management must be pre-trade, real-time, and mathematically precise. It is a mathematical domain, not a semantic one.

## 3. Why Not a Bull/Bear/Neutral Debate Architecture?

Unlike many competitors who use a "bull/bear/neutral LLM-debate" architecture to establish directional bias, VRP-Agent explicitly rejects this. Recent research (TiMi, ICLR 2026, arXiv:2510.04787) demonstrates that debate-style anthropomorphic agents introduce emotional bias and drift into consensus thinking. VRP-Agent relies instead on **mechanical rationality**—trading premium structural advantages rather than debating directional opinions.

## 4. Backtest Results

**VRP Sleeve** (2007–Present)
| Model | CAGR | Sharpe | Max Drawdown |
|---|---|---|---|
| Unconditional selling | 1.67% | 1.62 | -2.06% |
| Regime-filtered (our model) | 0.76% | 0.85 | -2.14% |

*Honest finding*: The regime filter does NOT improve Sharpe or reduce drawdown vs unconditional selling. The claim that "regime filtering improves risk-adjusted returns" is explicitly dropped from our pitch. The pitch instead relies on our pre-registered honesty, deterministic risk gates, and an uncorrelated second sleeve.

**Earnings Sleeve** (LULU, 24 historical events)
Backtested win rate is **79.2%** (averaging $26/event, Sharpe 0.34). 
*Note*: The live week only yields **one** liquid, high-conviction opportunity (LULU Sep 3 AMC). This is a focused, single-name trade sized per the risk gate, not a broad daily "sleeve".

## 5. The Regime-Filter Bug Story

During backtesting, we discovered the regime filter was sitting out 93% of trading days. We traced this to a logical contradiction in the original pre-registration: it demanded `IV Rank > 50` (VIX elevated) AND `VIX < 200DMA` (VIX low/crashing). 
Instead of silently changing the backtest to p-hack a better result, we issued a dated addendum to our `PREREGISTRATION.md`, dropped the 200DMA requirement, and replaced it with a `VIX_5d_ROC < 5%` rule to avoid vol expansion. This process rigor is a core differentiator: we build in public and fix bugs transparently.

## 6. Known Limitations
- **Options pricing proxy**: VRP backtest options pricing is approximated via VIX. No free historical IV surface data is available.
- **Earnings proxy**: Earnings backtest uses a 30-day HV proxy, not actual pre-earnings implied volatility.
- **Live window**: The live trading window is ~4.5 sessions (Aug 31–Sep 4). This is insufficient to prove statistical edge in-sample; the backtest serves as our evidence base, while the live week is an orchestration demonstration.
- **Assignment Risk**: Early assignment risk on short legs is not fully simulated in paper trading.

## 7. Verifiable Log (Tamper-Detection)
Every decision made by the LangGraph agent is appended to a hash-chained JSON log (`data/verifiable_log.json`), where each entry hashes the previous entry's signature. 
Judges can run `make verify` (or `python verify_log.py`) locally. If a single byte of past decision-making is altered to look better post-trade, the chain verification will loudly fail, providing a mathematically guaranteed trust signal.
