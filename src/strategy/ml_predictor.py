import os
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta

def get_ml_signal(ticker="SPY"):
    """
    Trains a lightweight Random Forest model on the last 5 years of SPY and VIX data.
    Predicts if tomorrow's return will be positive.
    Returns: {"signal": "BUY" | "SELL" | "HOLD", "confidence": float}
    """
    print(f"-> [ML Predictor] Training Random Forest on {ticker} + VIX data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    spy = yf.download("SPY", start=start_date, end=end_date, progress=False)
    vix = yf.download("^VIX", start=start_date, end=end_date, progress=False)
    
    if spy.empty or vix.empty:
        return {"signal": "HOLD", "confidence": 0.0, "reason": "Data fetch failed"}

    # Handle multi-level columns from yfinance if present
    if isinstance(spy.columns, pd.MultiIndex):
        spy = spy.droplevel(1, axis=1)
    if isinstance(vix.columns, pd.MultiIndex):
        vix = vix.droplevel(1, axis=1)

    df = pd.DataFrame(index=spy.index)
    df['spy_close'] = spy['Close']
    df['vix_close'] = vix['Close']
    
    # Feature engineering
    df['spy_ret'] = df['spy_close'].pct_change()
    df['vix_ret'] = df['vix_close'].pct_change()
    df['spy_ma5'] = df['spy_close'].rolling(5).mean()
    df['spy_ma20'] = df['spy_close'].rolling(20).mean()
    df['vix_ma5'] = df['vix_close'].rolling(5).mean()
    
    # Target: 1 if tomorrow's return > 0 else 0
    df['target'] = (df['spy_ret'].shift(-1) > 0).astype(int)
    
    df.dropna(inplace=True)
    
    features = ['spy_ret', 'vix_ret', 'spy_ma5', 'spy_ma20', 'vix_ma5']
    X = df[features][:-1]
    y = df['target'][:-1]
    
    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    rf.fit(X, y)
    
    # Predict today
    today_features = df[features].iloc[-1:]
    prob = rf.predict_proba(today_features)[0][1]
    
    if prob >= 0.45:
        return {"signal": "BUY", "confidence": round(prob, 3), "reason": f"RF bullish (p={prob:.2f})"}
    elif prob < 0.45:
        return {"signal": "SELL", "confidence": round(1-prob, 3), "reason": f"RF bearish (p={1-prob:.2f})"}
    else:
        return {"signal": "HOLD", "confidence": round(prob, 3), "reason": f"RF neutral (p={prob:.2f})"}

if __name__ == "__main__":
    print(get_ml_signal())
