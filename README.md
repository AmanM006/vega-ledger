# VRP-Agent: Institutional-Grade Autonomous Options Trading

> **Alpaca AI Trading Agents Hackathon** | Account: `PA3D4EOEK0PA` | Strategy: Volatility Risk Premium + ML Momentum

An **autonomous, multi-strategy AI trading agent** built on LangGraph. It combines a **Deflated Sharpe Ratio (DSR)** validated options strategy, a **Scikit-Learn Random Forest** ML momentum sleeve, a deterministic risk gate, and an on-chain cryptographic audit trail anchored to the **Ethereum blockchain**.

### Key Architecture
| Module | Technology | Description |
|--------|-----------|-------------|
| Orchestration | LangGraph | Multi-node DAG: 3 parallel strategy sleeves → Risk Gate → Execution |
| VRP Sleeve | Black-Scholes + DSR | Sells overpriced IV; rejected by math when edge is negative |
| ML Sleeve | Scikit-Learn RF | Random Forest trained on 5yr SPY/VIX data, fires live trades |
| Risk Gate | Custom `evaluate()` | Hard circuit breakers: VIX regime, daily P&L limits, exposure caps |
| Audit Trail | SHA-256 Hash Chain | Every decision is logged and root hash anchored to Ethereum Sepolia |
| MCP Server | FastMCP | Exposes agent tools to any MCP-compatible LLM client |
| CLI | `cli.py` | Full command-line interface for all agent operations |
| Dashboard | Next.js + TypeScript | Real-time dark-themed UI with live Alpaca data |



## Structure
- `data/`: Contains downloaded historical market data and backtest results.
- `src/app/`: Streamlit dashboard.
- `src/backtest/`: Backtesting engine and metrics calculator.
- `src/data/`: Data pipeline for pulling historical SPY and VIX data.
- `src/risk/`: Deterministic risk gate.
- `src/strategy/`: Regime filtering and pricing logic.
- `src/orchestration/`: LangGraph multi-agent orchestration and MCP integration.
- `research/`: Pre-registration thesis and risk limits.

## Machine Learning Momentum Sleeve
In addition to the options strategy, the agent features a **Random Forest** predictor (`src/strategy/ml_predictor.py`) that trains dynamically on 5 years of SPY and VIX data. It predicts next-day directionality to execute micro-hedges and momentum trades, satisfying the ML requirement for advanced market context.

## MCP Server Integration
This project natively implements the **Model Context Protocol (MCP)**.
To start the MCP server:
```bash
python cli.py mcp
# or: python src/orchestration/mcp_server.py
```
Tools exposed:
- `get_verifiable_log`: Retrieves the cryptographically verifiable trade history.
- `run_evaluation`: Forces the agent to evaluate the market and execute immediately.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your credentials:
   ```env
   ALPACA_API_KEY=your_paper_key
   ALPACA_SECRET_KEY=your_paper_secret
   GEMINI_API_KEY=your_gemini_key
   ```
3. Run the background agent via the CLI:
   ```bash
   python cli.py daemon
   ```
4. Launch the Next.js visual dashboard:
   ```bash
   python cli.py dashboard
   # or for legacy Streamlit UI: python cli.py dashboard --legacy
   ```

## Running the Project
1. **Data Pipeline**: Download data and compute regimes.
   ```bash
   python src/data/pipeline.py
   ```
2. **Backtest**: Run the regime-filtered and unconditional backtests.
   ```bash
   python src/backtest/run.py
   python src/backtest/stats.py
   ```
3. **Agent execution**: Run the LangGraph orchestration layer.
   ```bash
   python src/orchestration/agent.py
   ```
4. **Dashboard**: View live execution state and backtest curves.
   ```bash
   streamlit run src/app/dashboard.py
   ```
