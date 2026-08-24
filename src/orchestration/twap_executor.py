import time
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, ReplaceOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

API_KEY = os.environ.get("ALPACA_API_KEY", "YOUR_API_KEY")
SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "YOUR_SECRET_KEY")

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def get_live_mid_price(symbol: str) -> float:
    """Get the current live mid-price (bid + ask) / 2 from Alpaca."""
    try:
        # Note: In a real options environment, we'd pull the OPRA options chain quote.
        # Here we demonstrate the TWAP mid-price logic on the underlying proxy.
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quote_response = data_client.get_stock_latest_quote(req)
        quote = quote_response[symbol]
        
        bid = quote.bid_price
        ask = quote.ask_price
        
        # Fallback if quotes are 0 (e.g. extended hours glitch)
        if bid == 0 or ask == 0:
            return 0.0
            
        return round((bid + ask) / 2.0, 2)
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        return 0.0

def execute_twap_limit_order(symbol: str, qty: int, side: OrderSide, execution_window_minutes: int = 15):
    """
    Places a limit order at the mid-price.
    Adjusts the price incrementally closer to the ask (for buys) or bid (for sells) 
    over the execution window if unfilled.
    """
    print(f"\n[TWAP Executor] Initiating mid-price execution for {qty} {symbol} ({side.value})")
    
    mid_price = get_live_mid_price(symbol)
    if mid_price == 0.0:
        print(f"[TWAP] No valid quote for {symbol}, aborting TWAP.")
        return {"status": "failed", "reason": "No valid quote"}
        
    print(f"[TWAP] Initial Mid-Price: ${mid_price:.2f}")

    # 1. Place initial mid-price limit order
    limit_req = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY,
        limit_price=mid_price
    )
    
    try:
        order = trading_client.submit_order(order_data=limit_req)
        order_id = str(order.id)
        print(f"[TWAP] Submitted initial limit order {order_id} at ${mid_price}")
    except Exception as e:
        print(f"[TWAP] Submit failed: {e}")
        return {"status": "failed", "reason": str(e)}

    # 2. Monitor and adjust (TWAP loop)
    # We will adjust 3 times over the window (e.g., every 5 minutes if window=15)
    adjustments = 3
    sleep_interval = (execution_window_minutes * 60) / adjustments
    
    for i in range(adjustments):
        time.sleep(sleep_interval)
        
        # Check order status
        try:
            live_order = trading_client.get_order_by_id(order_id)
        except Exception as e:
            print(f"[TWAP] Error fetching order {order_id}: {e}")
            break
            
        if live_order.status in ["filled", "canceled", "expired"]:
            print(f"[TWAP] Order {order_id} is already {live_order.status}.")
            return {"status": live_order.status, "order_id": order_id}
            
        # Unfilled, adjust closer to the aggressive side
        new_quote = get_live_mid_price(symbol)
        if new_quote == 0.0:
            continue
            
        # Shift limit price closer to market
        # Buy: shift up slightly. Sell: shift down slightly.
        # This simulates giving up a fraction of the edge (e.g. 1 cent) to secure a fill
        adjustment_penny = 0.01 * (i + 1)
        new_limit = new_quote + adjustment_penny if side == OrderSide.BUY else new_quote - adjustment_penny
        new_limit = round(new_limit, 2)
        
        print(f"[TWAP] Minute {int((i+1)*(sleep_interval/60))}: Order unfilled. Adjusting limit to ${new_limit:.2f}")
        
        replace_req = ReplaceOrderRequest(limit_price=new_limit)
        try:
            live_order = trading_client.replace_order_by_id(order_id, order_data=replace_req)
        except Exception as e:
            print(f"[TWAP] Failed to replace order: {e}")
            
    # Final check
    try:
        live_order = trading_client.get_order_by_id(order_id)
        if live_order.status == "filled":
             return {"status": "success", "order_id": order_id}
        else:
             print("[TWAP] Window expired. Order still open (partial or unfilled).")
             return {"status": "open", "order_id": order_id}
    except Exception as e:
        return {"status": "unknown", "order_id": order_id, "reason": str(e)}

