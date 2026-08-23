import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="VRP Trading Agent Dashboard", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def load_data():
    bt = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"), index_col="Date", parse_dates=True)
    md = pd.read_csv(os.path.join(DATA_DIR, "market_data.csv"), index_col="Date", parse_dates=True)
    return bt, md

st.title("Autonomous VRP Options Trading Agent")

bt, md = load_data()

st.subheader("Current Regime Read (Latest Data)")
latest = md.iloc[-1]
vix = latest['VIX']
vix_200 = latest['VIX_200DMA']
vix_5d = latest['VIX_5d_ago']
iv_rank = latest['IV_Rank']
iv_pct = latest['IV_Percentile']

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("VIX", f"{vix:.2f}")
col2.metric("VIX 200DMA", f"{vix_200:.2f}")
col3.metric("VIX 5d Ago", f"{vix_5d:.2f}")
col4.metric("IV Rank", f"{iv_rank:.1f}")
col5.metric("IV Percentile", f"{iv_pct:.1f}")

# Check Regime
vix_rising = vix > vix_5d * 1.05
vix_above_200dma = vix > vix_200

reasons = []
if vix_above_200dma and vix_rising:
    reasons.append("VIX above 200DMA and rising >5%")
if iv_rank <= 50 or iv_pct <= 50:
    reasons.append("IV rank/percentile <= 50")
if vix > 30:
    reasons.append("VIX > 30 (extreme tail)")

tradeable = len(reasons) == 0

st.write(f"**Regime Filter Status:** {'? Tradeable' if tradeable else '? Sit out'}")
if reasons:
    st.write("Reasons: ", ", ".join(reasons))

st.subheader("Backtest: Regime-Filtered vs Unconditional")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(bt.index, bt['Unconditional'], label='Unconditional')
ax.plot(bt.index, bt['Regime-Filtered'], label='Regime-Filtered')
ax.set_ylabel('Account Equity ($)')
ax.legend()
ax.grid(True)
st.pyplot(fig)

st.subheader("Live Execution Log")
st.write("*(Demo: agent actions will be logged here via LangGraph state during the live window)*")
