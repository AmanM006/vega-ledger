"""
Earnings IV-crush backtest.
Uses historical LULU earnings dates from yfinance, computes post-earnings
1-day price move vs implied straddle width at entry.
We CANNOT get historical implied volatility surfaces for free, so we use
realized move vs a 30-day HV proxy for the "expected move."
This is NOT a true IV-crush backtest — it is an approximate proxy.
The limitation is explicitly documented.
"""
import yfinance as yf
import pandas as pd
import numpy as np

def backtest_earnings_crush(ticker: str) -> pd.DataFrame:
    tk = yf.Ticker(ticker)

    # Get earnings dates with reported EPS (i.e., past events)
    earnings = tk.earnings_dates
    if earnings is None:
        print(f"No earnings dates for {ticker}")
        return pd.DataFrame()

    # Only past events (non-NaN Reported EPS)
    past = earnings[earnings["Reported EPS"].notna()].copy()
    past.index = past.index.tz_convert(None).floor("D")
    past = past[~past.index.duplicated(keep="first")]
    print(f"{ticker}: {len(past)} historical earnings events")

    # Daily price history
    hist = tk.history(period="max")["Close"]
    hist.index = hist.index.tz_convert(None).floor("D")
    hist = hist.groupby(hist.index).first()

    results = []
    for event_date in past.index:
        # pre-earnings price (day before)
        try:
            pre_idx = hist.index.get_loc(event_date)
        except KeyError:
            # Try next available day
            candidates = hist.index[hist.index >= event_date]
            if len(candidates) == 0:
                continue
            pre_idx = hist.index.get_loc(candidates[0])

        if pre_idx < 20:
            continue  # need 20 days for HV

        price_before = hist.iloc[pre_idx - 1]  # close before earnings

        # 30-day realized vol as IV proxy (annualized)
        window_returns = hist.iloc[pre_idx - 21:pre_idx].pct_change().dropna()
        if len(window_returns) < 10:
            continue
        hv_annualized = window_returns.std() * np.sqrt(252)

        # 1-day expected move from HV (daily vol * price)
        daily_vol = hv_annualized / np.sqrt(252)
        implied_move_proxy = daily_vol * price_before

        # Actual post-earnings move
        if pre_idx >= len(hist) - 1:
            continue  # no day-after data
        price_after = hist.iloc[pre_idx]
        actual_move = abs(price_after - price_before)
        actual_move_pct = actual_move / price_before

        # Iron condor profit/loss:
        # Short strikes at 1x implied move, wings at 1.5x
        # Credit received ≈ 0 (conservative — true P&L requires live IV data)
        # Profit if actual move < implied move (stay inside shorts)
        # Max profit = credit received (modeled as 30% of wing width)
        wing_width = implied_move_proxy * 0.5  # wing is 0.5x extra
        credit_received = wing_width * 0.30  # rough estimate: 30% of width
        max_profit = credit_received * 100
        max_loss = (wing_width - credit_received) * 100

        stayed_inside = actual_move < implied_move_proxy
        pnl = max_profit if stayed_inside else -max_loss

        results.append({
            "date": event_date,
            "price_before": price_before,
            "price_after": price_after,
            "actual_move": actual_move,
            "actual_move_pct": actual_move_pct,
            "implied_move_proxy": implied_move_proxy,
            "implied_move_pct": implied_move_proxy / price_before,
            "stayed_inside": stayed_inside,
            "pnl": pnl,
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    for ticker in ["LULU", "CIEN"]:
        df = backtest_earnings_crush(ticker)
        if df.empty:
            print(f"{ticker}: No data\n")
            continue

        wins = df["stayed_inside"].sum()
        total = len(df)
        win_rate = wins / total
        total_pnl = df["pnl"].sum()
        avg_pnl = df["pnl"].mean()
        sharpe = df["pnl"].mean() / df["pnl"].std() * np.sqrt(4) if df["pnl"].std() > 0 else 0

        print(f"\n{'='*50}")
        print(f"{ticker} Earnings IV-Crush Backtest ({total} events)")
        print(f"  Win rate:  {win_rate:.1%}  ({wins}/{total} events inside short strikes)")
        print(f"  Total P&L: ${total_pnl:,.0f}")
        print(f"  Avg P&L:   ${avg_pnl:,.0f} per event")
        print(f"  Sharpe:    {sharpe:.2f}")
        print(f"  Avg actual move:   {df['actual_move_pct'].mean():.1%}")
        print(f"  Avg implied proxy: {df['implied_move_proxy'].mean() / df['price_before'].mean():.1%}")
        print()
        print("  NOTE: This is a HV-proxy backtest — not real IV surface data.")
        print("  Credit received estimated at 30% of wing width (conservative).")
        print("  Real results would require historical options data (not free).")
