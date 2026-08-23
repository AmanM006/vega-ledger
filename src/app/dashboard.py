"""
VRP-Agent Live Dashboard — Streamlit

Shows:
  - Current regime status (VIX, IV Rank, tradeable yes/no + reasons)
  - VRP equity curve (unconditional vs regime-filtered vs SPY)
  - LULU earnings trade status
  - Recent verifiable log decisions
  - Open Alpaca paper positions
  - Bootstrapped stats & Crisis stress tests
"""
import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timezone

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="VRP-Agent Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Path helpers ────────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_ROOT, "data")
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

# ── Sidebar ─────────────────────────────────────────────────────
st.sidebar.title("VRP-Agent")
st.sidebar.caption("Alpaca AI Hackathon 2026")
st.sidebar.markdown("---")
st.sidebar.markdown("**Account**: Paper (`$100k`)")
st.sidebar.markdown("**Live window**: Aug 31 – Sep 4, 2026")
st.sidebar.markdown("**Earnings trade**: LULU Sep 3 AMC")

# ── Header ──────────────────────────────────────────────────────
st.title("📊 VRP-Agent: Live Trading Dashboard")
st.caption(f"Last refreshed: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

# ── Row 1: Regime status ─────────────────────────────────────────
st.markdown("## 1 · Current Regime")

col1, col2, col3, col4 = st.columns(4)

try:
    import yfinance as yf
    vix = yf.Ticker("^VIX").history(period="10d")["Close"]
    vix_now = float(vix.iloc[-1])
    vix_5d_ago = float(vix.iloc[-6]) if len(vix) >= 6 else vix_now
    vix_200 = float(yf.Ticker("^VIX").history(period="2y")["Close"].rolling(200).mean().iloc[-1])

    vix_1y = yf.Ticker("^VIX").history(period="1y")["Close"]
    rolling_min = vix_1y.rolling(252).min().iloc[-1]
    rolling_max = vix_1y.rolling(252).max().iloc[-1]
    iv_rank = ((vix_now - rolling_min) / (rolling_max - rolling_min) * 100
               if rolling_max > rolling_min else 50.0)

    sys.path.insert(0, SRC_DIR)
    from strategy.regime import check_regime
    signal = check_regime(vix_now, vix_200, vix_5d_ago, iv_rank, iv_rank)

    col1.metric("VIX", f"{vix_now:.2f}", f"{vix_now - vix_5d_ago:+.2f} vs 5d ago")
    col2.metric("IV Rank (1yr)", f"{iv_rank:.0f}")
    col3.metric("VIX 200-DMA", f"{vix_200:.2f}")
    tradeable_label = "✅ TRADEABLE" if signal.tradeable else "🚫 SIT OUT"
    col4.metric("VRP Regime", tradeable_label)

    if signal.tradeable:
        st.success("**Regime: TRADEABLE** — VRP sleeve active")
    else:
        st.warning("**Regime: SIT OUT** — " + " | ".join(signal.reasons))

except Exception as e:
    st.error(f"Could not fetch live regime data: {e}")

# ── Row 2: VRP Equity Curve ──────────────────────────────────────
st.markdown("## 2 · VRP Backtest (Net of Transaction Costs)")
st.caption("Friction costs applied: $0.48 round-trip per Condor contract (SPY standard pricing).")

backtest_path = os.path.join(DATA_DIR, "backtest_results.csv")
if os.path.exists(backtest_path):
    bt = pd.read_csv(backtest_path, index_col="Date", parse_dates=True)
    
    # Plot Unconditional (Net), Regime (Net) and SPY
    cols_to_plot = ['Unconditional (Net)', 'Regime-Filtered (Net)', 'SPY']
    bt_norm = bt[cols_to_plot].copy()
    for col in bt_norm.columns:
        if bt_norm[col].iloc[0] != 0:
            bt_norm[col] = bt_norm[col] / bt_norm[col].iloc[0] * 100_000

    st.line_chart(bt_norm, use_container_width=True)
    
    # Advanced stats
    st.markdown("### Advanced Rigor Stats")
    st.markdown("""
    - **Deflated Sharpe Ratio (DSR)**: Adjusts for non-normality and selection bias (Bailey & Lopez de Prado, 2014).
    - **Bootstrap CIs**: 2,000 resamples of discrete trade P&L (not path-dependent daily returns).
    """)
    stats_data = [
        {"Model": "Unconditional (Gross)", "CAGR": "1.67%", "Sharpe": "1.62", "DSR": "-", "Bootstrap 95% CI (Sharpe)": "-"},
        {"Model": "Unconditional (Net)", "CAGR": "-0.65%", "Sharpe": "-0.25", "DSR": "0.00%", "Bootstrap 95% CI (Sharpe)": "[-2.12, 0.11]"},
        {"Model": "Regime-Filtered (Net)", "CAGR": "-0.73%", "Sharpe": "-0.36", "DSR": "0.00%", "Bootstrap 95% CI (Sharpe)": "[-3.39, -0.67]"}
    ]
    st.dataframe(pd.DataFrame(stats_data).set_index("Model"), use_container_width=True)
    
    st.markdown("### Crisis Period Performance (Max Drawdown)")
    crisis_data = [
        {"Crisis": "2008 Financial Crisis", "Uncond MaxDD": "-1.73%", "Regime MaxDD": "-1.09%", "SPY MaxDD": "-47.17%"},
        {"Crisis": "2018 Volmageddon/Q4", "Uncond MaxDD": "-3.45%", "Regime MaxDD": "-2.13%", "SPY MaxDD": "-19.20%"},
        {"Crisis": "2020 COVID Crash", "Uncond MaxDD": "-3.90%", "Regime MaxDD": "-2.14%", "SPY MaxDD": "-33.72%"}
    ]
    st.table(pd.DataFrame(crisis_data).set_index("Crisis"))
else:
    st.warning("Backtest results not found.")

# ── Row 3: LULU Earnings Trade ───────────────────────────────────
st.markdown("## 3 · Earnings Sleeve: LULU Sep 3 AMC")
try:
    from strategy.earnings import get_earnings_setup
    setup = get_earnings_setup("LULU", "2026-09-03", "post")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("LULU Price", f"${setup.stock_price:.2f}")
    col_b.metric("ATM Straddle", f"${setup.straddle_price:.2f}")
    col_c.metric("Implied Move", f"${setup.expected_move:.2f} ({setup.expected_move_pct:.1%})")
except Exception as e:
    st.error(f"Could not compute LULU setup: {e}")

# ── Row 4: Open Positions ────────────────────────────────────────
st.markdown("## 4 · Open Positions (Alpaca Paper)")
try:
    api_key = os.environ.get("ALPACA_API_KEY")
    api_secret = os.environ.get("ALPACA_SECRET_KEY")
    if api_key and api_secret:
        from alpaca.trading.client import TradingClient
        tc = TradingClient(api_key, api_secret, paper=True)
        account = tc.get_account()
        positions = tc.get_all_positions()

        col_e, col_f, col_g = st.columns(3)
        col_e.metric("Equity", f"${float(account.equity):,.2f}")
        col_f.metric("Buying Power", f"${float(account.buying_power):,.2f}")
        daily_pnl = float(account.equity) - float(account.last_equity)
        col_g.metric("Daily P&L", f"${daily_pnl:+,.2f}")

        if positions:
            pos_data = [{"Symbol": p.symbol, "Qty": p.qty, "Market Value": f"${float(p.market_value):,.2f}", "Unrealized P&L": f"${float(p.unrealized_pl):+,.2f}"} for p in positions]
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
        else:
            st.info("No open positions.")
except Exception as e:
    st.error(f"Could not fetch positions: {e}")

# ── Row 5: Recent Decisions from Verifiable Log ──────────────────
st.markdown("## 5 · Recent Agent Decisions (Verifiable Log)")
log_path = os.path.join(DATA_DIR, "verifiable_log.json")
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            chain = json.load(f)
        if chain:
            records = []
            for rec in chain[-10:]:
                entry = rec.get("entry", {})
                records.append({
                    "Timestamp": entry.get("timestamp", "–")[:19].replace("T", " "),
                    "VIX": f"{entry.get('market_data', {}).get('vix_now', 0):.1f}",
                    "VRP Verdict": entry.get("vrp", {}).get("risk_evaluation", {}).get("verdict", "–"),
                    "VRP Reason": " | ".join(entry.get("vrp", {}).get("risk_evaluation", {}).get("reasons", []))[:60],
                    "Hash": rec.get("hash", "")[:12] + "…",
                })
            st.dataframe(pd.DataFrame(records), use_container_width=True)
    except Exception as e:
        st.error(f"Could not read log: {e}")

st.markdown("---")
st.caption("VRP-Agent · Alpaca AI Trading Agents Hackathon 2026")
