# VRP-Agent: Autonomous Options Trading

**Hackathon**: Alpaca AI Trading Agents Hackathon
**Track**: Options Trading
**Author**: Aman

## 1. AI Logic & Orchestration

VRP-Agent uses an orchestrated multi-agent framework built with **LangGraph** to process market data and manage state. 

Unlike many competitors who use a "bull/bear/neutral LLM-debate" architecture, VRP-Agent explicitly rejects LLM debate for directional positioning. Recent research (TiMi, ICLR 2026, arXiv:2510.04787) demonstrates that debate-style anthropomorphic agents introduce emotional bias and drift into consensus thinking. Instead, VRP-Agent relies on **deterministic, mechanical rationality**. The agent pulls structured market data via the **Alpaca MCP server**, applies a strict regime-conditional filter for Variance Risk Premium (VRP) harvesting, and computes optimal strikes using Black-Scholes. The LLM's role is strictly orchestrating the pipeline, summarizing the regime status, and appending to a hash-chained, verifiable log.

## 2. Infrastructure: Alpaca MCP Server

The entire data and execution layer runs through the **Alpaca MCP Server**:
1. **Market Data Retrieval**: Fetching current SPY pricing, VIX metrics, and implied volatility (via option chains).
2. **Order Execution**: Submitting multi-leg options orders (iron condors/credit spreads) to a funded Alpaca paper trading account.
3. **Corporate Actions**: Querying the earnings calendar for our secondary IV-crush strategy.

Every step runs autonomously, and Alpaca-py wraps the raw data payloads cleanly into our LangGraph StateGraph.

## 3. Risk Gates (Deterministic)

VRP-Agent features a rigorous, non-LLM risk gate that cannot be bypassed:
- **Per-Trade Max Loss**: Capped at ≤ 2% of account equity.
- **VIX-Scaled Portfolio Cap**: 25% exposure below VIX 22; 15% between VIX 22-30; 5% above VIX 30.
- **Circuit Breaker**: Halts trading if daily drawdown hits limits.
- **Macro Avoidance**: No entries within 24 hours of scheduled Fed/macro prints.

## 4. Backtest Results

We ran two backtests over history to validate the VRP strategy:
- **Unconditional Selling**: Sells VRP continuously regardless of market conditions.
- **Regime-Filtered (Our Model)**: Only sells VRP when IV Rank > 25, VIX is not rising >5% over 5 days, and VIX < 30.

**Results (2007 - Present)**:
- **Unconditional Metrics**: CAGR: 1.67%, Sharpe: 1.62, Max Drawdown: -2.0%
- **Regime-Filtered Metrics**: CAGR: 0.76%, Sharpe: 0.85, Max Drawdown: -2.1%

*Honest finding*: In this specific simulation, the regime filter underperformed continuous selling. By strictly sitting out during extended low-VIX periods or brief spikes, the agent missed substantial premium collection that out-earned the drawdowns in the unconditional approach. However, because our pre-registration locks the strategy, we present these results unmodified to avoid p-hacking.

## 5. Known Limitations (per Pre-Registration)
- Backtest options data quality/availability is limited on free sources — historical IV surfaces were approximated using VIX. 
- The live trading window is ~4.5 sessions (Aug 31 - Sep 4). Not enough trades for the VRP edge to prove out statistically in-sample; the backtest is the evidence base, the live week is a demonstration.
- Early assignment risk on short legs is not fully simulated in paper trading.
- Historical earnings sleeve backtests were omitted due to lack of free historical earnings calendar data.
