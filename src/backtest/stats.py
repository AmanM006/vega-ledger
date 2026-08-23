import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def calculate_metrics(equity_series):
    # Daily returns
    returns = equity_series.pct_change().dropna()
    
    # CAGR
    years = (equity_series.index[-1] - equity_series.index[0]).days / 365.25
    cagr = (equity_series.iloc[-1] / equity_series.iloc[0]) ** (1 / years) - 1
    
    # Sharpe (assuming 0% risk free rate for simplicity of metric)
    sharpe = np.sqrt(252) * returns.mean() / returns.std()
    
    # Max Drawdown
    roll_max = equity_series.cummax()
    drawdown = equity_series / roll_max - 1.0
    max_drawdown = drawdown.min()
    
    return {
        "CAGR": cagr,
        "Sharpe": sharpe,
        "Max Drawdown": max_drawdown
    }

def main():
    df = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"), index_col="Date", parse_dates=True)
    
    uncond_metrics = calculate_metrics(df['Unconditional'])
    regime_metrics = calculate_metrics(df['Regime-Filtered'])
    
    print("Unconditional Metrics:", uncond_metrics)
    print("Regime-Filtered Metrics:", regime_metrics)
    
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Unconditional'], label='Unconditional')
    plt.plot(df.index, df['Regime-Filtered'], label='Regime-Filtered')
    plt.title('Backtest Equity Curve: VRP Premium Selling')
    plt.xlabel('Date')
    plt.ylabel('Account Equity ($)')
    plt.legend()
    plt.grid(True)
    
    chart_path = os.path.join(DATA_DIR, "equity_curve.png")
    plt.savefig(chart_path)
    print(f"Chart saved to {chart_path}")
    
if __name__ == "__main__":
    main()
