# VRP-Agent: Autonomous Options Trading

**Alpaca Paper Account ID**: PA3D4EOEK0PA
**Competition Account Created**: September 2, 2026 (within hackathon window)

**Hackathon**: Alpaca AI Trading Agents Hackathon
**Track**: Options Trading
**Author**: Aman

## 1. The Core Pitch: Institutional Rigor > LLM Hallucination

Most AI trading hackathon projects fall into one of two traps: 
1. They use "bull/bear/neutral" LLM debates that drift into emotional consensus and hallucinate alpha (see TiMi, ICLR 2026).
2. They present frictionless, overfitted backtests to hide the fact that their edge vanishes in the real world.

**VRP-Agent takes the opposite approach.** We built a deterministic, mechanical LangGraph agent to harvest Volatility Risk Premium (VRP). More importantly, we built a full suite of institutional-grade validation tooling (Deflated Sharpe Ratio, discrete bootstrapping, walk-forward splits, transaction cost modeling, and a tamper-proof verifiable log). 

When we subjected our own VRP strategy to this rigor, the edge vanished. **Instead of p-hacking the data to present a fake win, we used our tooling to correctly reject the strategy.** VRP-Agent is a demonstration of mathematically proven risk management and uncompromising intellectual honesty.

## 2. Architecture & Risk Gates

VRP-Agent executes via a strictly non-LLM risk gate (`src/risk/gate.py`) that cannot be bypassed:
- **Per-Trade Max Loss**: Hard cap at ≤ 2% of account equity.
- **VIX-Scaled Portfolio Cap**: 25% exposure below VIX 22; 15% between VIX 22-30; 5% above VIX 30.
- **Circuit Breaker**: Halts trading entirely if daily drawdown > 3%.
- **Macro Avoidance**: No entries within 24h of scheduled Fed/macro prints.

The LLM does not make directional bets. It orchestrates the pipeline, queries the Alpaca API, and appends to a hash-chained verifiable log.

## 3. Backtest Results: The Rigor Pass

Our backtest spans 2007–Present. 
**Gross vs. Net of Costs**: A standard $10-wide iron condor lost >28% of its credit to friction ($0.48 round trip per contract). We structurally widened the wings to $20-wide to halve the transaction cost drag. Even with optimized execution, the results were sobering:

| Model | Gross Sharpe | Net Sharpe | DSR | Bootstrap 95% CI (Sharpe) |
|---|---|---|---|---|
| Unconditional | 1.62 | -0.05 | 0.00% | [-1.33, 1.00] |
| Regime-Filtered | 0.85 | -0.24 | 0.00% | [-2.74, 0.08] |

**Verdict**: The Deflated Sharpe Ratio (DSR) is 0.00%. The bootstrap CIs straddle or fall below zero. **The core systematic VRP strategy has negative expectancy and is officially rejected.** 

## 4. Crisis Period Stress Tests (Risk Management)

While the strategy yields no alpha net of costs, the regime filter behaves exactly as designed—it excels at protecting tail risk during black swan events compared to unconditional selling and holding SPY:
- **2008 Financial Crisis**: SPY (-47.17%), Unconditional VRP (-1.73%), Regime-Filtered VRP **(-1.09%)**
- **2018 Volmageddon**: SPY (-19.20%), Unconditional VRP (-3.45%), Regime-Filtered VRP **(-2.13%)**
- **2020 COVID Crash**: SPY (-33.72%), Unconditional VRP (-3.90%), Regime-Filtered VRP **(-2.14%)**

Our live execution demonstrates risk management, not alpha generation.

## 5. The Live Play: LULU Earnings Crush

Because the systematic VRP strategy is rejected, our live P&L for the hackathon (Aug 31–Sep 4) rests on an uncorrelated, single-name opportunistic trade:
- **Earnings IV-Crush Sleeve**: Proposes symmetric iron condors 1-3 days before confirmed earnings prints, sizing strikes strictly outside the straddle-implied move. 
- **The Setup**: Only one liquid opportunity exists this week—**LULU (Sep 3 AMC)**. 
- **Consistency in Rigor**: We applied the exact same friction model ($0.48 round trip per contract) to our LULU earnings backtest (N=24 historical prints). 
  - *Result*: While LULU boasts a 79.2% gross win rate, the **Net Sharpe is -0.28**. 
  - We explicitly note that 24 events is far too thin a sample size for DSR/bootstrap confidence, but even within this limited proxy, transaction costs erase the edge.

The agent will size and execute the LULU trade purely as a live orchestration demonstration of the risk gate. We do not claim this will generate expected alpha.

## 6. Verifiable Log (Tamper-Detection)
Every agent decision is appended to a hash-chained JSON log (`data/verifiable_log.json`). Judges can run `make verify` (or `python verify_log.py`) locally. If a single byte of past decision-making is altered post-trade, the cryptographic chain loudly fails. Trust is proven mathematically, not promised.

## 7. Future Work: Execution Algorithms (Unvalidated Projection)
We built a Time-Weighted Average Price (TWAP) execution node (src/orchestration/twap_executor.py) that systematically walks limit orders toward the aggressive side of the spread over a 15-minute window rather than firing an immediate market order.

If this algorithm were to successfully recapture just 1/3 of the bid-ask spread (.02 per leg), our projected Net Sharpe would swing from -0.05 to +0.17. However, **this is an unvalidated hypothesis.** Fill behavior is highly dependent on real-time order book liquidity, which cannot be modeled accurately without live empirical data.

Because we could not validate this execution improvement against live market hours over multiple sessions prior to the hackathon deadline, we refuse to report this projection as a finding. The official, mathematically validated stance of this project remains that the systematic VRP strategy yields negative expectancy (DSR=0.00%) due to spread friction. The TWAP node is strictly experimental future work.
