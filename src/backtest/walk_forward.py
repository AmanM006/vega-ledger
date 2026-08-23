import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def compute_metrics(eq):
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (252 / len(eq)) - 1
    daily_ret = eq.pct_change().dropna()
    sharpe = daily_ret.mean() / daily_ret.std() * np.sqrt(252) if daily_ret.std() > 0 else 0
    mdd = ((eq - eq.cummax()) / eq.cummax()).min()
    return cagr, sharpe, mdd

if __name__ == "__main__":
    df = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"), index_col="Date", parse_dates=True)
    
    # Split: Dev (2007-2015), OOS (2016-2024)
    dev_df = df.loc['2007':'2015']
    oos_df = df.loc['2016':]
    
    print("=== Walk-Forward Split Analysis ===")
    for strategy in ['Unconditional (Net)', 'Regime-Filtered (Net)']:
        print(f"\n--- {strategy} ---")
        
        dev_eq = dev_df[strategy].dropna()
        oos_eq = oos_df[strategy].dropna()
        
        if len(dev_eq) > 0 and len(oos_eq) > 0:
            dcagr, dshr, dmdd = compute_metrics(dev_eq)
            ocagr, oshr, omdd = compute_metrics(oos_eq)
            
            print(f"Development (2007-2015): CAGR {dcagr:.2%}, Sharpe {dshr:.2f}, MaxDD {dmdd:.2%}")
            print(f"Held-Out    (2016-2024): CAGR {ocagr:.2%}, Sharpe {oshr:.2f}, MaxDD {omdd:.2%}")
        else:
            print("Not enough data for split.")
