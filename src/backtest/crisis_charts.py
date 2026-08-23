import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def plot_crisis(df, start, end, title, filename):
    mask = (df.index >= start) & (df.index <= end)
    sub = df.loc[mask].copy()
    if len(sub) == 0:
        return
        
    # Normalize to 100 for the start of the crisis
    for col in sub.columns:
        sub[col] = sub[col] / sub[col].iloc[0] * 100
        
    plt.figure(figsize=(10, 6))
    plt.plot(sub.index, sub['Unconditional (Net)'], label='Unconditional (Net)', color='red')
    plt.plot(sub.index, sub['Regime-Filtered (Net)'], label='Regime-Filtered (Net)', color='blue')
    plt.plot(sub.index, sub['SPY'], label='SPY Buy & Hold', color='black', linestyle='--')
    
    plt.title(title)
    plt.ylabel('Normalized Equity (100 = Start)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    out_path = os.path.join(DATA_DIR, filename)
    plt.savefig(out_path)
    plt.close()
    
    # Print stats
    print(f"\n=== {title} ({start} to {end}) ===")
    for col in ['Unconditional (Net)', 'Regime-Filtered (Net)', 'SPY']:
        ret = sub[col].iloc[-1] / sub[col].iloc[0] - 1
        mdd = ((sub[col] - sub[col].cummax()) / sub[col].cummax()).min()
        print(f"  {col:25s}: Return = {ret:7.2%}, MaxDD = {mdd:7.2%}")

if __name__ == "__main__":
    df = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"), index_col="Date", parse_dates=True)
    
    crises = [
        ('2008 Financial Crisis', '2008-07-01', '2009-03-31', 'crisis_2008.png'),
        ('2018 Volmageddon/Q4', '2018-10-01', '2019-01-31', 'crisis_2018.png'),
        ('2020 COVID Crash', '2020-02-01', '2020-05-31', 'crisis_2020.png')
    ]
    
    for title, start, end, fname in crises:
        plot_crisis(df, start, end, title, fname)
