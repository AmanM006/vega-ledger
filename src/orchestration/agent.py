import os
import hashlib
import json
from datetime import datetime, date
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
import yfinance as yf

# Alpaca imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from risk.gate import evaluate, ProposedTrade, AccountState, Verdict
from strategy.regime import check_regime
from strategy.earnings import get_all_earnings_setups, EARNINGS_CALENDAR
from strategy.ml_predictor import get_ml_signal

ALPACA_API_KEY = os.environ["ALPACA_API_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


class AgentState(TypedDict):
    messages: list
    market_data: dict
    # VRP sleeve
    regime_signal: dict
    proposed_vrp_trade: Optional[dict]
    vrp_risk_evaluation: dict
    vrp_execution_result: dict
    # Earnings sleeve
    earnings_setups: list
    proposed_earnings_trades: list
    earnings_risk_evaluations: list
    earnings_execution_results: list
    # ML Sleeve
    ml_signal: dict
    ml_execution_result: dict
    # Shared
    log_chain: list


def hash_log_entry(entry: dict, previous_hash: str) -> str:
    entry_str = json.dumps(entry, sort_keys=True, default=str) + previous_hash
    return hashlib.sha256(entry_str.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────
# SHARED: Market data node
# ─────────────────────────────────────────────────────────────
def gather_market_data(state: AgentState):
    print("-> Gathering REAL market data via yfinance & Alpaca...")
    quote_req = StockLatestQuoteRequest(symbol_or_symbols="SPY")
    latest_quote = data_client.get_stock_latest_quote(quote_req)
    spy_price = latest_quote["SPY"].ask_price

    vix = yf.Ticker("^VIX").history(period="1y")["Close"]
    vix_now = float(vix.iloc[-1])
    vix_5d_ago = float(vix.iloc[-6]) if len(vix) >= 6 else vix_now
    vix_200dma = float(vix.rolling(200).mean().iloc[-1])

    rolling_min = vix.rolling(252).min().iloc[-1]
    rolling_max = vix.rolling(252).max().iloc[-1]
    iv_rank = ((vix_now - rolling_min) / (rolling_max - rolling_min) * 100
               if rolling_max > rolling_min else 50.0)
    iv_percentile = float((vix < vix_now).mean() * 100)

    account = trading_client.get_account()
    equity = float(account.equity)
    daily_pnl = float(account.equity) - float(account.last_equity)

    market_data = {
        "spy_price": float(spy_price),
        "vix_now": vix_now,
        "vix_200dma": vix_200dma,
        "vix_5d_ago": vix_5d_ago,
        "iv_rank": iv_rank,
        "iv_percentile": iv_percentile,
        "account_equity": equity,
        "daily_pnl": daily_pnl,
        "today": date.today().isoformat(),
    }
    return {"market_data": market_data}


# ─────────────────────────────────────────────────────────────
# VRP SLEEVE: Regime check → proposes a VRP trade or None
# ─────────────────────────────────────────────────────────────
def check_regime_node(state: AgentState):
    print("-> [VRP] Checking regime...")
    md = state["market_data"]
    signal = check_regime(
        vix_now=md["vix_now"],
        vix_200dma=md["vix_200dma"],
        vix_5d_ago=md["vix_5d_ago"],
        iv_rank=md["iv_rank"],
        iv_percentile=md["iv_percentile"],
    )

    proposed = None
    if signal.tradeable:
        proposed = {
            "strategy": "vrp_premium",
            "symbol": "SPY",
            "max_loss_dollars": 1000.0,
            "notional_exposure_dollars": 1000.0,
            "is_earnings_sleeve": False,
        }

    return {
        "regime_signal": {"tradeable": signal.tradeable, "reasons": signal.reasons},
        "proposed_vrp_trade": proposed,
    }


# ─────────────────────────────────────────────────────────────
# EARNINGS SLEEVE: Check calendar, compute setups for today window
# ─────────────────────────────────────────────────────────────
def check_earnings_node(state: AgentState):
    print("-> [Earnings] Checking earnings calendar...")
    today = state["market_data"]["today"]
    proposed_trades = []
    setups_summary = []

    # We enter 1-3 days before the report date
    from datetime import timedelta, date as date_type
    today_dt = date_type.fromisoformat(today)

    eligible = []
    for entry in EARNINGS_CALENDAR:
        report_dt = date_type.fromisoformat(entry["report_date"])
        days_until = (report_dt - today_dt).days
        if 1 <= days_until <= 3:
            eligible.append(entry)

    if not eligible:
        print(f"   No earnings within 1-3 day window from {today}. Sleeve idle.")
        return {"earnings_setups": [], "proposed_earnings_trades": []}

    setups = get_all_earnings_setups()
    for setup in setups:
        report_dt = date_type.fromisoformat(setup.report_date)
        days_until = (report_dt - today_dt).days
        if not (1 <= days_until <= 3):
            continue

        setups_summary.append({
            "ticker": setup.ticker,
            "report_date": setup.report_date,
            "report_time": setup.report_time,
            "straddle": setup.straddle_price,
            "expected_move_pct": setup.expected_move_pct,
            "tradeable": setup.is_tradeable,
            "reject_reason": setup.reject_reason,
        })

        if setup.is_tradeable:
            proposed_trades.append({
                "strategy": "earnings_crush",
                "symbol": setup.ticker,
                "max_loss_dollars": setup.max_loss_dollars,
                "notional_exposure_dollars": setup.max_loss_dollars,
                "is_earnings_sleeve": True,
                # Carry setup metadata for execution node
                "_setup": {
                    "short_call": setup.short_call_strike,
                    "long_call": setup.long_call_strike,
                    "short_put": setup.short_put_strike,
                    "long_put": setup.long_put_strike,
                    "expiry": setup.expiry,
                    "stock_price": setup.stock_price,
                    "straddle": setup.straddle_price,
                },
            })

    return {
        "earnings_setups": setups_summary,
        "proposed_earnings_trades": proposed_trades,
    }


# ─────────────────────────────────────────────────────────────
# SHARED RISK GATE: runs both VRP and earnings proposals
# Single evaluate() entry point — one gate, one source of truth
# ─────────────────────────────────────────────────────────────
def risk_gate_node(state: AgentState):
    print("-> [Risk Gate] Evaluating all proposed trades...")
    md = state["market_data"]

    positions = trading_client.get_all_positions()
    current_exposure = sum(float(p.market_value) for p in positions)

    acc = AccountState(
        equity=md["account_equity"],
        current_short_vol_exposure_dollars=abs(current_exposure),
        vix_level=md["vix_now"],
        daily_pnl_dollars=md["daily_pnl"],
        daily_loss_limit_pct=0.03,
    )

    # Evaluate VRP trade
    vrp_eval = {"verdict": "reject", "reasons": ["No VRP trade proposed"]}
    if state.get("proposed_vrp_trade"):
        t = state["proposed_vrp_trade"]
        pt = ProposedTrade(
            strategy=t["strategy"],
            symbol=t["symbol"],
            max_loss_dollars=t["max_loss_dollars"],
            notional_exposure_dollars=t["notional_exposure_dollars"],
            is_earnings_sleeve=False,
        )
        res = evaluate(pt, acc)
        vrp_eval = {"verdict": res.verdict.value, "reasons": res.reasons}

    # Evaluate each earnings trade — is_earnings_sleeve=True bypasses VIX regime veto
    earnings_evals = []
    for t in state.get("proposed_earnings_trades", []):
        pt = ProposedTrade(
            strategy=t["strategy"],
            symbol=t["symbol"],
            max_loss_dollars=t["max_loss_dollars"],
            notional_exposure_dollars=t["notional_exposure_dollars"],
            is_earnings_sleeve=True,          # ← key: bypasses VIX/regime cap
        )
        res = evaluate(pt, acc)
        earnings_evals.append({
            "symbol": t["symbol"],
            "verdict": res.verdict.value,
            "reasons": res.reasons,
            "_setup": t.get("_setup"),
        })

    return {
        "vrp_risk_evaluation": vrp_eval,
        "earnings_risk_evaluations": earnings_evals,
    }


# ─────────────────────────────────────────────────────────────
# EXECUTION: VRP trade
# ─────────────────────────────────────────────────────────────
def execute_vrp_node(state: AgentState):
    print("-> [VRP] Executing via Alpaca...")
    risk = state["vrp_risk_evaluation"]
    if risk["verdict"] != "approve":
        return {"vrp_execution_result": {"status": "skipped", "reason": risk["reasons"]}}

    market_order_data = MarketOrderRequest(
        symbol="SPY",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    try:
        order = trading_client.submit_order(order_data=market_order_data)
        return {"vrp_execution_result": {"status": "success", "order_id": str(order.id)}}
    except Exception as e:
        return {"vrp_execution_result": {"status": "failed", "reason": str(e)}}


# ─────────────────────────────────────────────────────────────
# EXECUTION: Earnings trades
# ─────────────────────────────────────────────────────────────
def execute_earnings_node(state: AgentState):
    print("-> [Earnings] Executing approved earnings trades via Alpaca...")
    return {"earnings_execution_results": [{"status": "skipped", "reason": "Earnings execution disabled for snapshot protection"}]}



# ─────────────────────────────────────────────────────────────
# LOG: Hash-chained, unified log for both sleeves
# ─────────────────────────────────────────────────────────────

def check_ml_node(state: AgentState):
    print("-> [ML] Running Random Forest Predictor...")
    try:
        from strategy.ml_predictor import get_ml_signal
        sig = get_ml_signal("SPY")
        return {"ml_signal": sig}
    except Exception as e:
        print(f"ML error: {e}")
        return {"ml_signal": {"signal": "HOLD", "confidence": 0, "reason": "Error running ML"}}

def execute_ml_node(state: AgentState):
    print("-> [ML] Evaluating ML proposal against quantitative risk gate...")
    sig = state.get("ml_signal", {})
    signal_type = sig.get("signal", "HOLD")
    confidence = sig.get("confidence", 0.0)
    
    # Institutional Risk Gate:
    # The directional ML sleeve lacks walk-forward DSR validation (>95% threshold).
    # Refuse unhedged directional live orders to maintain zero-alpha-hallucination discipline.
    if signal_type in ["BUY", "SELL"]:
        return {
            "ml_execution_result": {
                "status": "benched",
                "signal": signal_type,
                "confidence": confidence,
                "reason": [
                    "Directional ML model lacks Deflated Sharpe Ratio (DSR > 0.95) walk-forward proof",
                    "Unhedged directional trade refused by quantitative risk governor"
                ]
            }
        }
    return {
        "ml_execution_result": {
            "status": "skipped",
            "signal": "HOLD",
            "confidence": confidence,
            "reason": [sig.get("reason", "Model output in noise/neutral regime")]
        }
    }

def append_log_node(state: AgentState):
    print("-> Appending to verifiable log...")
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "verifiable_log.json"
    )

    log_chain = []
    if os.path.exists(log_path):
        try:
            with open(log_path) as f:
                log_chain = json.load(f)
        except Exception:
            log_chain = []

    prev_hash = log_chain[-1]["hash"] if log_chain else "0" * 64

    entry = {
        "timestamp": datetime.now(tz=__import__("datetime").timezone.utc).isoformat(),
        "market_data": state.get("market_data"),
        "vrp": {
            "regime_signal": state.get("regime_signal"),
            "risk_evaluation": state.get("vrp_risk_evaluation"),
            "execution_result": state.get("vrp_execution_result"),
        },
        "ml_momentum": {
            "signal": state.get("ml_signal"),
            "execution": state.get("ml_execution_result")
        },
        "earnings": {
            "setups": state.get("earnings_setups"),
            "risk_evaluations": state.get("earnings_risk_evaluations"),
            "execution_results": state.get("earnings_execution_results"),
        },
    }

    current_hash = hash_log_entry(entry, prev_hash)
    log_chain.append({"entry": entry, "hash": current_hash})

    with open(log_path, "w") as f:
        json.dump(log_chain, f, indent=2, default=str)

    return {"log_chain": log_chain}


# ─────────────────────────────────────────────────────────────
# GRAPH: VRP and earnings nodes run sequentially (single-thread);
# both feed into shared risk gate → execution → log
# ─────────────────────────────────────────────────────────────
def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("gather_market_data", gather_market_data)
    workflow.add_node("check_regime", check_regime_node)
    workflow.add_node("check_earnings", check_earnings_node)
    workflow.add_node("check_ml", check_ml_node)
    workflow.add_node("risk_gate", risk_gate_node)
    workflow.add_node("execute_vrp", execute_vrp_node)
    workflow.add_node("execute_earnings", execute_earnings_node)
    workflow.add_node("execute_ml", execute_ml_node)
    workflow.add_node("append_log", append_log_node)

    workflow.set_entry_point("gather_market_data")
    workflow.add_edge("gather_market_data", "check_regime")
    workflow.add_edge("gather_market_data", "check_earnings")
    workflow.add_edge("gather_market_data", "check_ml")
    
    workflow.add_edge("check_regime", "risk_gate")
    workflow.add_edge("check_earnings", "risk_gate")
    workflow.add_edge("check_ml", "risk_gate")
    
    workflow.add_edge("risk_gate", "execute_vrp")
    workflow.add_edge("risk_gate", "execute_earnings")
    workflow.add_edge("risk_gate", "execute_ml")
    
    workflow.add_edge("execute_vrp", "append_log")
    workflow.add_edge("execute_earnings", "append_log")
    workflow.add_edge("execute_ml", "append_log")
    workflow.add_edge("append_log", END)

    return workflow.compile()


def main():
    app = build_graph()
    state = app.invoke({
        "messages": [],
        "log_chain": [],
        "proposed_vrp_trade": None,
        "proposed_earnings_trades": [],
        "earnings_setups": [],
        "earnings_risk_evaluations": [],
        "earnings_execution_results": [],
        "vrp_risk_evaluation": {},
        "vrp_execution_result": {},
    })
    print("\nRun complete.")
    print("VRP:", state.get("vrp_execution_result"))
    print("Earnings:", state.get("earnings_execution_results"))
    print("ML Momentum:", state.get("ml_execution_result"))


if __name__ == "__main__":
    main()
