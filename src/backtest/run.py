import pandas as pd
import numpy as np
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from risk.gate import evaluate, ProposedTrade, AccountState, Verdict
from strategy.regime import check_regime
from backtest.pricer import bs_price, get_strike_for_delta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def run_backtest(df, use_regime_filter=True):
    account_equity = 100000.0
    open_trades = []
    history = []
    
    # Pre-compute risk-free rate roughly
    r = 0.04  # 4% risk-free rate
    
    for i, (date, row) in enumerate(df.iterrows()):
        spy_price = row['SPY']
        vix = row['VIX']
        iv_rank = row['IV_Rank']
        iv_pct = row['IV_Percentile']
        vix_200dma = row['VIX_200DMA']
        vix_5d_ago = row['VIX_5d_ago']
        
        # 1. Update existing trades
        daily_pnl = 0
        new_open_trades = []
        for trade in open_trades:
            days_held = (date - trade['entry_date']).days
            dte = trade['dte_initial'] - days_held
            
            # Current value of the Iron Condor (price to close)
            # Short call - Long call + Short put - Long put
            # VIX is annual IV in %.
            current_iv = vix / 100.0
            T = dte / 365.0
            
            if dte <= 0:
                T = 0.0001
            
            sc_price = bs_price(spy_price, trade['short_call_strike'], T, r, current_iv, 'c')
            lc_price = bs_price(spy_price, trade['long_call_strike'], T, r, current_iv, 'c')
            sp_price = bs_price(spy_price, trade['short_put_strike'], T, r, current_iv, 'p')
            lp_price = bs_price(spy_price, trade['long_put_strike'], T, r, current_iv, 'p')
            
            current_cost_to_close = sc_price - lc_price + sp_price - lp_price
            
            # Pnl for this trade since inception
            trade_pnl = (trade['credit_received'] - current_cost_to_close) * 100 * trade['qty']
            
            # Exit conditions
            # 50% profit target
            if current_cost_to_close <= trade['credit_received'] * 0.5:
                account_equity += trade_pnl
                daily_pnl += trade_pnl
                continue
                
            # 2x credit stop loss -> cost to close >= 3x credit (loss is 2x)
            if current_cost_to_close >= trade['credit_received'] * 3.0:
                account_equity += trade_pnl
                daily_pnl += trade_pnl
                continue
                
            # 21 DTE exit (entered at 45 DTE, so 24 days held)
            if dte <= 21:
                account_equity += trade_pnl
                daily_pnl += trade_pnl
                continue
                
            new_open_trades.append(trade)
            
        open_trades = new_open_trades
        
        # 2. Check for new entries
        # Can we trade today? (Skip if we already have too much exposure)
        current_exposure = sum((t['long_call_strike'] - t['short_call_strike']) * 100 * t['qty'] for t in open_trades)
        
        account_state = AccountState(
            equity=account_equity,
            current_short_vol_exposure_dollars=current_exposure,
            vix_level=vix,
            daily_pnl_dollars=daily_pnl,
            daily_loss_limit_pct=0.03
        )
        
        # Check regime
        regime = check_regime(vix, vix_200dma, vix_5d_ago, iv_rank, iv_pct)
        tradeable = regime.tradeable if use_regime_filter else True
        
        if tradeable and len(open_trades) < 2:  # Stagger up to 2 trades max
            # Price a 45 DTE 16-delta Iron Condor
            T_initial = 45 / 365.0
            initial_iv = vix / 100.0
            
            sc_strike = get_strike_for_delta(spy_price, T_initial, r, initial_iv, 0.16, 'c')
            sp_strike = get_strike_for_delta(spy_price, T_initial, r, initial_iv, -0.16, 'p')
            
            # 10 wide wings
            lc_strike = sc_strike + 10
            lp_strike = sp_strike - 10
            
            sc_price = bs_price(spy_price, sc_strike, T_initial, r, initial_iv, 'c')
            lc_price = bs_price(spy_price, lc_strike, T_initial, r, initial_iv, 'c')
            sp_price = bs_price(spy_price, sp_strike, T_initial, r, initial_iv, 'p')
            lp_price = bs_price(spy_price, lp_strike, T_initial, r, initial_iv, 'p')
            
            credit = sc_price - lc_price + sp_price - lp_price
            
            # If credit is negative or too small, skip (arbitrage/bad pricing)
            if credit > 0.5:
                # Sizing
                width = 10
                max_loss_per_contract = (width - credit) * 100
                qty = 2  # Max $2000 loss is 2% of $100k, 2 contracts is < $2000
                
                proposed = ProposedTrade(
                    strategy="vrp_premium",
                    symbol="SPY",
                    max_loss_dollars=max_loss_per_contract * qty,
                    notional_exposure_dollars=width * 100 * qty
                )
                
                gate_result = evaluate(proposed, account_state)
                
                if gate_result.verdict == Verdict.APPROVE:
                    open_trades.append({
                        'entry_date': date,
                        'dte_initial': 45,
                        'short_call_strike': sc_strike,
                        'long_call_strike': lc_strike,
                        'short_put_strike': sp_strike,
                        'long_put_strike': lp_strike,
                        'credit_received': credit,
                        'qty': qty
                    })

        history.append({
            'Date': date,
            'Equity': account_equity
        })
        
    return pd.DataFrame(history)

if __name__ == "__main__":
    df = pd.read_csv(os.path.join(DATA_DIR, "market_data.csv"), index_col="Date", parse_dates=True)
    
    print("Running Unconditional Backtest...")
    unconditional_equity = run_backtest(df, use_regime_filter=False)
    
    print("Running Regime-Filtered Backtest...")
    filtered_equity = run_backtest(df, use_regime_filter=True)
    
    merged = pd.DataFrame({
        'Unconditional': unconditional_equity.set_index('Date')['Equity'],
        'Regime-Filtered': filtered_equity.set_index('Date')['Equity']
    })
    
    merged.to_csv(os.path.join(DATA_DIR, "backtest_results.csv"))
    print("Saved backtest_results.csv")
