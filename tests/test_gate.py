from src.risk.gate import ProposedTrade, AccountState, evaluate, Verdict


def base_account(**overrides):
    defaults = dict(
        equity=100_000,
        current_short_vol_exposure_dollars=0,
        vix_level=18,
        daily_pnl_dollars=0,
        daily_loss_limit_pct=0.03,
        kill_switch_engaged=False,
        hours_to_next_macro_print=None,
    )
    defaults.update(overrides)
    return AccountState(**defaults)


def test_normal_trade_approved():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=1000, notional_exposure_dollars=5000)
    result = evaluate(trade, base_account())
    assert result.verdict == Verdict.APPROVE


def test_kill_switch_halts_everything():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=100, notional_exposure_dollars=100)
    result = evaluate(trade, base_account(kill_switch_engaged=True))
    assert result.verdict == Verdict.HALT_ALL


def test_daily_drawdown_trips_circuit_breaker():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=100, notional_exposure_dollars=100)
    result = evaluate(trade, base_account(daily_pnl_dollars=-4000))  # -4% > 3% limit
    assert result.verdict == Verdict.HALT_ALL


def test_oversized_trade_rejected():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=3000, notional_exposure_dollars=100)
    result = evaluate(trade, base_account())
    assert result.verdict == Verdict.REJECT
    assert any("per-trade max loss" in r for r in result.reasons)


def test_exposure_cap_scales_down_with_vix():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=100, notional_exposure_dollars=20_000)
    result = evaluate(trade, base_account(vix_level=25, current_short_vol_exposure_dollars=0))
    # 20% projected > 15% cap at VIX 25
    assert result.verdict == Verdict.REJECT


def test_high_vix_vetoes_unconditional_entry():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=100, notional_exposure_dollars=100)
    result = evaluate(trade, base_account(vix_level=32))
    assert result.verdict == Verdict.REJECT


def test_earnings_sleeve_exempt_from_vix_veto():
    trade = ProposedTrade(
        "earnings_crush", "NVDA", max_loss_dollars=100,
        notional_exposure_dollars=100, is_earnings_sleeve=True,
    )
    result = evaluate(trade, base_account(vix_level=32))
    assert result.verdict == Verdict.APPROVE


def test_macro_print_window_blocks_non_earnings_entry():
    trade = ProposedTrade("vrp_premium", "SPY", max_loss_dollars=100, notional_exposure_dollars=100)
    result = evaluate(trade, base_account(hours_to_next_macro_print=6))
    assert result.verdict == Verdict.REJECT
