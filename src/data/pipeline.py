import yfinance as yf
import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def fetch_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print("Downloading SPY and VIX data...")
    spy = yf.Ticker("SPY").history(period="max")["Close"]
    vix = yf.Ticker("^VIX").history(period="max")["Close"]

    spy.index = spy.index.tz_convert(None).floor('D')
    vix.index = vix.index.tz_convert(None).floor('D')

    spy.name = "SPY"
    vix.name = "VIX"
    
    # Need to group by index in case of duplicates from floor
    spy = spy.groupby(spy.index).first()
    vix = vix.groupby(vix.index).first()

    df = pd.concat([spy, vix], axis=1).dropna()

    print("Computing metrics...")
    rolling_min = df["VIX"].rolling(window=252).min()
    rolling_max = df["VIX"].rolling(window=252).max()
    
    df["IV_Rank"] = ((df["VIX"] - rolling_min) / (rolling_max - rolling_min)) * 100
    
    # We can vectorize IVP for speed
    def calc_ivp(series):
        current_val = series.iloc[-1]
        return (series < current_val).mean() * 100

    df["IV_Percentile"] = df["VIX"].rolling(window=252).apply(calc_ivp, raw=False)
    
    df["VIX_200DMA"] = df["VIX"].rolling(window=200).mean()
    df["VIX_5d_ago"] = df["VIX"].shift(5)
    df["VIX_5d_ROC"] = (df["VIX"] / df["VIX_5d_ago"] - 1) * 100

    df.dropna(inplace=True)

    out_path = os.path.join(DATA_DIR, "market_data.csv")
    df.to_csv(out_path)
    print(f"Data saved to {out_path} with {len(df)} rows.")
    return df

if __name__ == "__main__":
    fetch_data()
