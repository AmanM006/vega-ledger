import asyncio
import os
import hashlib
import json
from datetime import datetime
from typing import TypedDict, Annotated, List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from risk.gate import evaluate, ProposedTrade, AccountState, Verdict
from strategy.regime import check_regime

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

async def gather_market_data(state: AgentState):
    print("-> Gathering market data via MCP...")
    market_data = {
        "spy_price": 450.0,
        "vix_now": 18.5,
        "vix_200dma": 20.0,
        "vix_5d_ago": 17.0,
        "iv_rank": 55.0,
        "iv_percentile": 60.0
    }
    return {"market_data": market_data}

async def check_regime_node(state: AgentState):
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

async def risk_gate_node(state: AgentState):
    print("-> Running risk gate...")
    proposed = state.get("proposed_trade")
    if not proposed:
        return {"risk_evaluation": {"verdict": "reject", "reasons": ["No trade proposed by regime filter"]}}
        
    pt = ProposedTrade(**proposed)
    acc = AccountState(
        equity=100000.0,
        current_short_vol_exposure_dollars=0.0,
        vix_level=state["market_data"]["vix_now"],
        daily_pnl_dollars=0.0,
        daily_loss_limit_pct=0.03
    )
    
    res = evaluate(pt, acc)
    return {"risk_evaluation": {"verdict": res.verdict.value, "reasons": res.reasons}}

async def execute_trade_node(state: AgentState):
    print("-> Executing trade via MCP...")
    risk = state["risk_evaluation"]
    if risk["verdict"] != "approve":
        return {"execution_result": {"status": "skipped", "reason": "Risk gate rejected or no trade"}}
        
    return {"execution_result": {"status": "success", "order_id": "mock-order-123"}}

async def append_log_node(state: AgentState):
    print("-> Appending to verifiable log...")
    log_chain = state.get("log_chain", [])
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
    
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "verifiable_log.json")
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

async def main():
    app = build_graph()
    state = await app.ainvoke({"messages": [], "log_chain": []})
    print("Run complete. Final state logged.")

if __name__ == "__main__":
    asyncio.run(main())
