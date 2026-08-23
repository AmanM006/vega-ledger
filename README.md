# VRP + Regime-Filtered Options Agent
Alpaca AI Trading Agents Hackathon — build log

See `research/PREREGISTRATION.md` for the locked thesis (committed before any
backtest code — check `git log`).

## Status

- [x] Thesis pre-registered and committed (2026-08-23)
- [x] Deterministic risk gate — written + tested (8/8 passing, `pytest tests/`)
- [x] Regime filter module — written, not yet backtested
- [ ] Historical data pulled + backtest run
- [ ] Earnings sleeve wired to Alpaca corporate-actions/earnings tool
- [ ] LangGraph orchestration (gather → regime check → risk gate → execute → log)
- [ ] Signed/hash-chained decision log
- [ ] Live dashboard (Streamlit, minimum viable)
- [ ] One-pager write-up
- [ ] Fresh paper account opened, $100k, on Aug 28 kickoff

## Confirmed earnings inside the live trading window (Aug 31 – Sep 4, 2026)

Thu Sep 3 and Fri Sep 4 both have earnings prints scheduled (checked against
public earnings calendars). Confirm exact tickers + times again closer to the
date, but this de-risks the earnings sleeve having zero material to trade —
it won't be empty.

## Important limitation — read before running anything

This sandbox's network is restricted to package registries (pypi, npm, github) —
it cannot reach Yahoo Finance, Alpaca's API, or any live market data source.
Everything here was written and unit-tested offline. **Data pulls, the actual
backtest run, and Alpaca connectivity all need to happen on your own machine**
with your Alpaca paper keys and a real data source (yfinance for
underlying price history is fine for the equity leg; for historical IV you'll
likely need to approximate via realized-vol proxies unless you find a free
options-chain history source — flag this honestly in the write-up per
PREREGISTRATION.md §6, don't hide it).

## 5-day prep plan (before Aug 28 kickoff)

**Day 1 (today):** thesis locked ✅, risk gate + regime filter built & tested ✅.
Next: pull SPY + VIX daily history locally, compute IV rank/percentile proxy.

**Day 2:** run the regime-filtered vs. unconditional VRP backtest. This is the
evidence — without a real backtest curve in the submission you're just
claiming an edge, not showing one. Save the equity curve + Sharpe/drawdown
table as an artifact for the write-up.

**Day 3:** wire the Alpaca MCP server locally (paper account, exploratory —
NOT the fresh hackathon account yet). Confirm multi-leg option order
placement works end-to-end in paper mode. Wire the earnings-sleeve data
source.

**Day 4:** LangGraph orchestration loop tying regime check → risk gate →
execution → logging together. Build the minimal live dashboard.

**Day 5:** dry run the full loop against paper data. Fix bugs. Draft the
one-pager and start the README/demo video outline. Do NOT touch the strategy
logic today — lock it.

**Aug 28, kickoff:** open the brand-new dedicated paper account, set balance
to $100,000, switch all config to it, go live for real.
