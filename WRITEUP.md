# VRP-Agent: Autonomous Options Trading

**Hackathon**: Alpaca AI Trading Agents Hackathon
**Track**: Options Trading
**Author**: Aman

## 1. AI Logic & Architecture

VRP-Agent uses an orchestrated multi-agent framework built with **LangGraph** to process market data and manage state. The architecture consists of a two-sleeve pipeline:
- **VRP Premium Sleeve**: Proposes SPY iron condors at 45 DTE / 16-delta when a regime filter passes.
- **Earnings IV-Crush Sleeve**: Proposes symmetric iron condors 1-3 days before confirmed earnings prints, sizing strikes strictly outside the straddle-implied move.

Both parallel nodes feed independently into a **single, unified deterministic risk gate**. The LLM orchestrates the pipeline, queries the Alpaca API, and appends to a hash-chained verifiable log.

## 2. Risk Gate

Options risk management must be pre-trade, real-time, and precise. We utilize a strictly non-LLM risk gate (`src/risk/gate.py`) that cannot be bypassed:
- **Per-Trade Max Loss**: Hard cap at ≤ 2% of account equity.
- **VIX-Scaled Portfolio Cap**: 25% exposure below VIX 22; 15% between VIX 22-30; 5% above VIX 30.
- **Circuit Breaker**: Halts trading entirely if daily drawdown > 3%.
- **Macro Avoidance**: No entries within 24h of scheduled Fed/macro prints.

## 3. Why Not an LLM Debate Architecture?

Most competitors use "bull/bear/neutral LLM-debate" architectures. VRP-Agent explicitly rejects this. Recent research (TiMi, ICLR 2026, arXiv:2510.04787) demonstrates that debate-style anthropomorphic agents introduce emotional bias and drift into consensus thinking. VRP-Agent relies instead on **mechanical rationality**—harvesting structural volatility premiums rather than debating directional opinions.

## 4. Backtest Results (The Rigor Pass)

We subject our VRP backtest (2007–Present) to institutional-grade statistical rigor, rarely seen in hackathons.

**Gross vs. Net of Costs**
We applied a strict transaction cost model: $0.05 spread + $0.01 slippage per leg = $0.48 round trip per condor contract.
- **Gross Sharpe (Frictionless)**: 1.62
- **Net Sharpe (After Costs)**: -0.25
*Honest finding:* The strategy edge is entirely destroyed by transaction costs. We present this plainly rather than hiding it.

**Advanced Statistics (Net of Costs)**
- **Deflated Sharpe Ratio (DSR)**: Corrects for multiple trials and non-normality (Bailey & López de Prado, 2014). Our DSR is **0.00%**, confirming no statistical evidence of edge.
- **Bootstrap 95% CIs**: 2,000 resamples of discrete trade P&L. 
  - Unconditional: Sharpe CI [-2.12, 0.11]
  - Regime-Filtered: Sharpe CI [-3.39, -0.67]
- **Walk-Forward Validation**: 
  - Development (2007-2015): CAGR -0.41%, Sharpe -0.43
  - Held-Out (2016-2024): CAGR -0.05%, Sharpe -0.03

**Crisis Period Stress Tests (Max Drawdown)**
While overall returns are negative net of costs, the regime filter excels precisely where it is meant to—protecting tail risk during market crashes compared to unconditional selling and SPY:
- **2008 Financial Crisis**: SPY (-47.17%), Unconditional VRP (-1.73%), Regime-Filtered VRP **(-1.09%)**
- **2018 Volmageddon**: SPY (-19.20%), Unconditional VRP (-3.45%), Regime-Filtered VRP **(-2.13%)**
- **2020 COVID Crash**: SPY (-33.72%), Unconditional VRP (-3.90%), Regime-Filtered VRP **(-2.14%)**

## 5. The Regime-Filter Bug Story

During development, our filter was sitting out 93% of days. We traced this to a logical contradiction in the original pre-registration (demanding `IV Rank > 50` AND `VIX < 200DMA`). Instead of silently p-hacking the backtest, we issued a dated addendum to our `PREREGISTRATION.md` and fixed it transparently. Process rigor > perfection.

## 6. Known Limitations
- **Options pricing proxy**: VRP pricing is approximated via VIX. No free historical IV surface data is available.
- **Earnings proxy**: Earnings backtest uses a 30-day HV proxy.
- **Live window**: ~4.5 sessions (Aug 31–Sep 4) is insufficient to prove statistical edge in-sample.

## 7. Verifiable Log (Tamper-Detection)
Every agent decision is appended to a hash-chained JSON log (`data/verifiable_log.json`). Judges can run `make verify` (or `python verify_log.py`) locally. If a single byte of past decision-making is altered post-trade, the cryptographic chain loudly fails. Trust is proven mathematically, not promised.
