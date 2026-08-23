import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from risk.gate import evaluate, ProposedTrade, AccountState, Verdict
from strategy.regime import check_regime
from backtest.pricer import bs_price, get_strike_for_delta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def run_backtest(df, use_regime_filter=True, apply_costs=False):
    account_equity = 100000.0
    open_trades = []
    history = []
    closed_trades = []
    
    r = 0.04
    # Cost model: $0.05 half-spread + $0.01 slippage = $0.06 per option.
    # 4 legs = $0.24 to open, $0.24 to close -> $0.48 total cost per condor share
    # We do 2 contracts (qty=2), so that's 200 shares. Total cost per trade = $96.
    # For simplicity, we just deduct $0.48 from the per-share P&L.
    rt_cost_per_share = 0.48 if apply_costs else 0.0
    
    for i, (date, row) in enumerate(df.iterrows()):
        spy_price = row['SPY']
        vix = row['VIX']
        iv_rank = row['IV_Rank']
        iv_pct = row['IV_Percentile']
        vix_200dma = row['VIX_200DMA']
        vix_5d_ago = row['VIX_5d_ago']
        
        daily_pnl = 0
        new_open_trades = []
        for trade in open_trades:
            days_held = (date - trade['entry_date']).days
            dte = trade['dte_initial'] - days_held
            current_iv = vix / 100.0
            T = dte / 365.0
            if dte <= 0:
                T = 0.0001
            
            sc_price = bs_price(spy_price, trade['short_call_strike'], T, r, current_iv, 'c')
            lc_price = bs_price(spy_price, trade['long_call_strike'], T, r, current_iv, 'c')
            sp_price = bs_price(spy_price, trade['short_put_strike'], T, r, current_iv, 'p')
            lp_price = bs_price(spy_price, trade['long_put_strike'], T, r, current_iv, 'p')
            
            current_cost_to_close = sc_price - lc_price + sp_price - lp_price
            
            # Pnl for this trade since inception (after RT costs if exiting)
            per_share_pnl = trade['credit_received'] - current_cost_to_close - rt_cost_per_share
            trade_pnl = per_share_pnl * 100 * trade['qty']
            
            exit_reason = None
            if current_cost_to_close <= trade['credit_received'] * 0.5:
                exit_reason = "Take Profit"
            elif current_cost_to_close >= trade['credit_received'] * 3.0:
                exit_reason = "Stop Loss"
            elif dte <= 21:
                exit_reason = "Time Exit"
                
            if exit_reason:
                account_equity += trade_pnl
                daily_pnl += trade_pnl
                closed_trades.append({
                    'entry_date': trade['entry_date'],
                    'exit_date': date,
                    'pnl': trade_pnl,
                    'per_share_pnl': per_share_pnl,
                    'reason': exit_reason,
                    'credit_received': trade['credit_received'],
                    'qty': trade['qty']
                })
                continue
                
            new_open_trades.append(trade)
            
        open_trades = new_open_trades
        
        current_exposure = sum((t['long_call_strike'] - t['short_call_strike']) * 100 * t['qty'] for t in open_trades)
        account_state = AccountState(
            equity=account_equity,
            current_short_vol_exposure_dollars=current_exposure,
            vix_level=vix,
            daily_pnl_dollars=daily_pnl,
            daily_loss_limit_pct=0.03
        )
        
        regime = check_regime(vix, vix_200dma, vix_5d_ago, iv_rank, iv_pct)
        tradeable = regime.tradeable if use_regime_filter else True
        
        if tradeable and len(open_trades) < 2:
            T_initial = 45 / 365.0
            initial_iv = vix / 100.0
            sc_strike = get_strike_for_delta(spy_price, T_initial, r, initial_iv, 0.16, 'c')
            sp_strike = get_strike_for_delta(spy_price, T_initial, r, initial_iv, -0.16, 'p')
            lc_strike = sc_strike + 20
            lp_strike = sp_strike - 20
            
            sc_price = bs_price(spy_price, sc_strike, T_initial, r, initial_iv, 'c')
            lc_price = bs_price(spy_price, lc_strike, T_initial, r, initial_iv, 'c')
            sp_price = bs_price(spy_price, sp_strike, T_initial, r, initial_iv, 'p')
            lp_price = bs_price(spy_price, lp_strike, T_initial, r, initial_iv, 'p')
            
            credit = sc_price - lc_price + sp_price - lp_price
            
            if credit > 0.5:
                width = 20
                max_loss_per_contract = (width - credit) * 100
                qty = 1
                
                proposed = ProposedTrade(
                    strategy="vrp_premium",
                    symbol="SPY",
                    max_loss_dollars=max_loss_per_contract * qty,
                    notional_exposure_dollars=width * 100 * qty,
                    is_earnings_sleeve=False
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
            'Equity': account_equity,
            'SPY': spy_price
        })
        
    return pd.DataFrame(history), closed_trades

if __name__ == "__main__":
    df = pd.read_csv(os.path.join(DATA_DIR, "market_data.csv"), index_col="Date", parse_dates=True)
    
    print("Running Unconditional (Gross)...")
    uncond_eq_gross, uncond_trades_gross = run_backtest(df, use_regime_filter=False, apply_costs=False)
    
    print("Running Unconditional (Net)...")
    uncond_eq_net, uncond_trades_net = run_backtest(df, use_regime_filter=False, apply_costs=True)
    
    print("Running Regime-Filtered (Gross)...")
    reg_eq_gross, reg_trades_gross = run_backtest(df, use_regime_filter=True, apply_costs=False)
    
    print("Running Regime-Filtered (Net)...")
    reg_eq_net, reg_trades_net = run_backtest(df, use_regime_filter=True, apply_costs=True)
    
    # SPY Buy & Hold (normalized to 100,000)
    spy_initial = uncond_eq_gross['SPY'].iloc[0]
    spy_equity = (uncond_eq_gross['SPY'] / spy_initial) * 100000.0
    
    merged = pd.DataFrame({
        'Unconditional (Gross)': uncond_eq_gross.set_index('Date')['Equity'],
        'Unconditional (Net)': uncond_eq_net.set_index('Date')['Equity'],
        'Regime-Filtered (Gross)': reg_eq_gross.set_index('Date')['Equity'],
        'Regime-Filtered (Net)': reg_eq_net.set_index('Date')['Equity'],
        'SPY': spy_equity.values
    })
    merged.index = uncond_eq_gross['Date']
    
    merged.to_csv(os.path.join(DATA_DIR, "backtest_results.csv"))
    print("Saved backtest_results.csv with Gross, Net, and SPY.")
    
    import json
    trades_data = {
        'unconditional_net': uncond_trades_net,
        'regime_net': reg_trades_net
    }
    with open(os.path.join(DATA_DIR, "trades.json"), 'w') as f:
        json.dump(trades_data, f, default=str)
    print("Saved trades.json")
