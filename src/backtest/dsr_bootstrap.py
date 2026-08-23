import json
import os
import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def calc_dsr(returns, num_trials=3):
    """
    Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)
    Corrects for selection bias (multiple trials) and non-normality (skew, kurtosis).
    """
    if len(returns) < 3 or np.std(returns) == 0:
        return 0.0
        
    sr_obs = np.mean(returns) / np.std(returns)
    T = len(returns)
    sk = skew(returns)
    ku = kurtosis(returns, fisher=False)  # Pearson's kurtosis
    
    # Expected Max Sharpe (approx) for independent trials
    # Euler-Mascheroni constant approx = 0.5772
    emc = 0.5772156649
    if num_trials > 1:
        sr_exp = np.sqrt(2 * np.log(num_trials)) + (emc / np.sqrt(2 * np.log(num_trials)))
    else:
        sr_exp = 0.0
        
    # Standard deviation of the Sharpe Ratio estimator
    # Accounting for non-normality
    sr_std = np.sqrt((1 - sk * sr_obs + ((ku - 1) / 4) * (sr_obs**2)) / (T - 1))
    
    # DSR is the CDF of the adjusted statistic
    z = (sr_obs - sr_exp) / sr_std
    dsr = norm.cdf(z)
    
    return sr_obs, dsr

def bootstrap_ci(trades, metric_func, n_bootstraps=2000, ci=95):
    """
    Bootstrap a generic metric (e.g., Sharpe or CAGR) on the discrete sequence of trades.
    """
    if len(trades) < 2:
        return 0.0, 0.0, 0.0
        
    metrics = []
    n_trades = len(trades)
    for _ in range(n_bootstraps):
        sample = np.random.choice(trades, size=n_trades, replace=True)
        metrics.append(metric_func(sample))
        
    lower = np.percentile(metrics, (100 - ci) / 2)
    upper = np.percentile(metrics, 100 - (100 - ci) / 2)
    return np.mean(metrics), lower, upper

def compute_trade_sharpe(trades_sample):
    pnl = [t['pnl'] for t in trades_sample]
    if np.std(pnl) == 0: return 0.0
    return np.mean(pnl) / np.std(pnl) * np.sqrt(252) # rough annualized trade sharpe, but typically we just do standard SR. Let's return raw trade SR.

def compute_trade_cagr(trades_sample):
    # This is a bit tricky on discrete trades without time series,
    # but we can sum PnL and assume the total timeframe is 2007-2024 (~17.5 years).
    total_pnl = sum(t['pnl'] for t in trades_sample)
    end_eq = 100000.0 + total_pnl
    if end_eq <= 0: return -1.0
    return (end_eq / 100000.0)**(1/17.5) - 1.0


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "trades.json")) as f:
        trades_data = json.load(f)
        
    # We will compute DSR on the daily equity curve returns to be precise.
    df = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"), index_col="Date", parse_dates=True)
    
    for strategy in ['Unconditional (Net)', 'Regime-Filtered (Net)']:
        eq = df[strategy].dropna()
        daily_ret = eq.pct_change().dropna()
        
        # 3 trials: Unconditional, Regime (original buggy), Regime (fixed)
        sr, dsr = calc_dsr(daily_ret, num_trials=3)
        # Annualized standard Sharpe for display
        ann_sr = sr * np.sqrt(252)
        
        print(f"\n--- {strategy} ---")
        print(f"Raw Annualized Sharpe: {ann_sr:.2f}")
        print(f"Deflated Sharpe Ratio (DSR): {dsr:.2%} (Prob that True SR > 0 after accounting for 3 trials)")
        
        # Bootstrap discrete trades
        key = 'unconditional_net' if 'Unconditional' in strategy else 'regime_net'
        trades = trades_data[key]
        
        mean_sr, low_sr, high_sr = bootstrap_ci(trades, compute_trade_sharpe, n_bootstraps=2000)
        mean_cagr, low_cagr, high_cagr = bootstrap_ci(trades, compute_trade_cagr, n_bootstraps=2000)
        
        print(f"Bootstrap 95% CI Trade Sharpe: {mean_sr:.2f} [{low_sr:.2f}, {high_sr:.2f}]")
        print(f"Bootstrap 95% CI CAGR: {mean_cagr:.2%} [{low_cagr:.2%}, {high_cagr:.2%}]")

