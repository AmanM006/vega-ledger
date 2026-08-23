# VRP-Agent: Autonomous Options Trading

An autonomous options trading agent for the **Alpaca AI Trading Agents Hackathon**.

## Structure
- `data/`: Contains downloaded historical market data and backtest results.
- `src/app/`: Streamlit dashboard.
- `src/backtest/`: Backtesting engine and metrics calculator.
- `src/data/`: Data pipeline for pulling historical SPY and VIX data.
- `src/risk/`: Deterministic risk gate.
- `src/strategy/`: Regime filtering and pricing logic.
- `src/orchestration/`: LangGraph multi-agent orchestration and MCP integration.
- `research/`: Pre-registration thesis and risk limits.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install yfinance pandas numpy matplotlib streamlit langgraph alpaca-py mcp pydantic langchain-openai
   ```
2. Set up your Alpaca paper trading API keys:
   ```bash
   set ALPACA_API_KEY=your_key
   set ALPACA_SECRET_KEY=your_secret
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
