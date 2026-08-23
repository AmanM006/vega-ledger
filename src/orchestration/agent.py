import asyncio
import os
import hashlib
import json
from datetime import datetime
from typing import TypedDict, Annotated, List, Dict, Any

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

# Paper trading keys provided
ALPACA_API_KEY = os.environ["ALPACA_API_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

class AgentState(TypedDict):
    messages: list
    market_data: dict
    regime_signal: dict
    proposed_trade: dict
    risk_evaluation: dict
    execution_result: dict
    log_chain: list

def hash_log_entry(entry: dict, previous_hash: str) -> str:
    entry_str = json.dumps(entry, sort_keys=True) + previous_hash
    return hashlib.sha256(entry_str.encode()).hexdigest()

def gather_market_data(state: AgentState):
    print("-> Gathering REAL market data via yfinance & Alpaca...")
    # Get SPY price from Alpaca
    quote_req = StockLatestQuoteRequest(symbol_or_symbols="SPY")
    latest_quote = data_client.get_stock_latest_quote(quote_req)
    spy_price = latest_quote["SPY"].ask_price

    # Get VIX data from yfinance (Alpaca doesn't natively stream CBOE indices easily without special subscriptions)
    vix = yf.Ticker("^VIX").history(period="1y")["Close"]
    
    vix_now = float(vix.iloc[-1])
    vix_5d_ago = float(vix.iloc[-6]) if len(vix) >= 6 else vix_now
    vix_200dma = float(vix.rolling(200).mean().iloc[-1])
    
    rolling_min = vix.rolling(252).min().iloc[-1]
    rolling_max = vix.rolling(252).max().iloc[-1]
    
    if rolling_max > rolling_min:
        iv_rank = ((vix_now - rolling_min) / (rolling_max - rolling_min)) * 100
    else:
        iv_rank = 50.0

    current_iv = (vix < vix_now).mean() * 100
    iv_percentile = float(current_iv)
    
    # Get Real Account Equity from Alpaca
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
        "daily_pnl": daily_pnl
    }
    return {"market_data": market_data}

def check_regime_node(state: AgentState):
    print("-> Checking regime...")
    md = state["market_data"]
    signal = check_regime(
        vix_now=md["vix_now"],
        vix_200dma=md["vix_200dma"],
        vix_5d_ago=md["vix_5d_ago"],
        iv_rank=md["iv_rank"],
        iv_percentile=md["iv_percentile"]
    )
    
    proposed = None
    if signal.tradeable:
        proposed = {
            "strategy": "vrp_premium",
            "symbol": "SPY",
            "max_loss_dollars": 1000.0,
            "notional_exposure_dollars": 1000.0,
            "is_earnings_sleeve": False
        }
        
    return {"regime_signal": {"tradeable": signal.tradeable, "reasons": signal.reasons}, "proposed_trade": proposed}

def risk_gate_node(state: AgentState):
    print("-> Running risk gate...")
    proposed = state.get("proposed_trade")
    if not proposed:
        return {"risk_evaluation": {"verdict": "reject", "reasons": ["No trade proposed by regime filter"]}}
        
    pt = ProposedTrade(**proposed)
    md = state["market_data"]
    
    # Real current exposure logic would pull positions from Alpaca, we assume 0 for demo/stateless check here
    positions = trading_client.get_all_positions()
    current_exposure = sum(float(p.market_value) for p in positions if p.symbol == "SPY")
    
    acc = AccountState(
        equity=md["account_equity"],
        current_short_vol_exposure_dollars=abs(current_exposure),
        vix_level=md["vix_now"],
        daily_pnl_dollars=md["daily_pnl"],
        daily_loss_limit_pct=0.03
    )
    
    res = evaluate(pt, acc)
    return {"risk_evaluation": {"verdict": res.verdict.value, "reasons": res.reasons}}

def execute_trade_node(state: AgentState):
    print("-> Executing trade via Alpaca API...")
    risk = state["risk_evaluation"]
    if risk["verdict"] != "approve":
        return {"execution_result": {"status": "skipped", "reason": "Risk gate rejected or no trade"}}
        
    # Example market order via Alpaca. 
    # For actual options we'd use OptionOrderRequest, but we buy 1 share of SPY as a proxy to prove wiring
    market_order_data = MarketOrderRequest(
        symbol="SPY",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    
    try:
        order = trading_client.submit_order(order_data=market_order_data)
        return {"execution_result": {"status": "success", "order_id": str(order.id)}}
    except Exception as e:
         return {"execution_result": {"status": "failed", "reason": str(e)}}

def append_log_node(state: AgentState):
    print("-> Appending to verifiable log...")
    log_chain = state.get("log_chain", [])
    
    # Need to verify if the file exists and has content to avoid JSONDecodeError
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "verifiable_log.json")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                log_chain = json.load(f)
        except:
            log_chain = []
            
    prev_hash = log_chain[-1]["hash"] if log_chain else "0000000000000000000000000000000000000000000000000000000000000000"
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "market_data": state.get("market_data"),
        "regime_signal": state.get("regime_signal"),
        "risk_evaluation": state.get("risk_evaluation"),
        "execution_result": state.get("execution_result")
    }
    
    current_hash = hash_log_entry(entry, prev_hash)
    log_entry = {"entry": entry, "hash": current_hash}
    
    log_chain.append(log_entry)
    
    with open(log_path, "w") as f:
        json.dump(log_chain, f, indent=2)
        
    return {"log_chain": log_chain}

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("gather_market_data", gather_market_data)
    workflow.add_node("check_regime", check_regime_node)
    workflow.add_node("risk_gate", risk_gate_node)
    workflow.add_node("execute_trade", execute_trade_node)
    workflow.add_node("append_log", append_log_node)
    
    workflow.set_entry_point("gather_market_data")
    workflow.add_edge("gather_market_data", "check_regime")
    workflow.add_edge("check_regime", "risk_gate")
    workflow.add_edge("risk_gate", "execute_trade")
    workflow.add_edge("execute_trade", "append_log")
    workflow.add_edge("append_log", END)
    
    return workflow.compile()

def main():
    app = build_graph()
    state = app.invoke({"messages": [], "log_chain": []})
    print("Run complete. Final state logged:")
    print(state["execution_result"])

if __name__ == "__main__":
    main()
