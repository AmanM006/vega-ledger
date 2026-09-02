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
4. Launch the visual dashboard:
   ```bash
   python cli.py dashboard
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
