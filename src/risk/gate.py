"""
Deterministic risk gate.

Every proposed trade — regardless of what any LLM, regime filter, or memory
lookup suggests — passes through here before it can reach the execution layer.
Nothing in this file calls an LLM. That's the point: the model can propose,
this decides. Mirrors the pre-trade / real-time / post-trade risk-control
framework used in the agentic-trading safety literature.

Rules are sourced from research/PREREGISTRATION.md — do not hardcode a number
here that contradicts that file. If you need to change a limit, change the
doc first, then this file, and note why.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Verdict(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    HALT_ALL = "halt_all"  # kill switch tripped — reject this AND stop taking new entries


@dataclass
class ProposedTrade:
    strategy: str  # "vrp_premium" | "earnings_crush"
    symbol: str
    max_loss_dollars: float
    notional_exposure_dollars: float
    is_earnings_sleeve: bool = False


@dataclass
class AccountState:
    equity: float
    current_short_vol_exposure_dollars: float
    vix_level: float
    daily_pnl_dollars: float
    daily_loss_limit_pct: float  # set once calibrated in backtest, e.g. 0.03
    kill_switch_engaged: bool = False
    hours_to_next_macro_print: float | None = None


@dataclass
class GateResult:
    verdict: Verdict
    reasons: list[str]


PER_TRADE_MAX_LOSS_PCT = 0.02  # 2% of equity, per PREREGISTRATION.md §4


def _exposure_cap_pct(vix: float) -> float:
    """VIX-scaled portfolio short-vol exposure cap, per PREREGISTRATION.md §2."""
    if vix > 30:
        return 0.05
    if vix >= 22:
        return 0.15
    return 0.25


def evaluate(trade: ProposedTrade, account: AccountState) -> GateResult:
    reasons: list[str] = []

    if account.kill_switch_engaged:
        return GateResult(Verdict.HALT_ALL, ["kill switch is engaged — no new entries"])

    if account.daily_pnl_dollars < 0:
        daily_loss_pct = abs(account.daily_pnl_dollars) / account.equity
        if daily_loss_pct > account.daily_loss_limit_pct:
            return GateResult(
                Verdict.HALT_ALL,
                [f"daily drawdown {daily_loss_pct:.2%} exceeds limit "
                 f"{account.daily_loss_limit_pct:.2%} — circuit breaker tripped"],
            )

    per_trade_pct = trade.max_loss_dollars / account.equity
    if per_trade_pct > PER_TRADE_MAX_LOSS_PCT:
        reasons.append(
            f"per-trade max loss {per_trade_pct:.2%} exceeds cap {PER_TRADE_MAX_LOSS_PCT:.2%}"
        )

    if not trade.is_earnings_sleeve:
        projected_exposure = (
            account.current_short_vol_exposure_dollars + trade.notional_exposure_dollars
        ) / account.equity
        cap = _exposure_cap_pct(account.vix_level)
        if projected_exposure > cap:
            reasons.append(
                f"projected short-vol exposure {projected_exposure:.2%} exceeds "
                f"VIX-scaled cap {cap:.2%} at VIX={account.vix_level:.1f}"
            )

    if account.vix_level > 30 and not trade.is_earnings_sleeve:
        reasons.append("VIX > 30 — no new unconditional short-vol entries, regime veto")

    if (
        account.hours_to_next_macro_print is not None
        and account.hours_to_next_macro_print < 24
        and not trade.is_earnings_sleeve
    ):
        reasons.append("inside 24h of scheduled macro print — entries blocked per §4")

    if reasons:
        return GateResult(Verdict.REJECT, reasons)
    return GateResult(Verdict.APPROVE, ["all checks passed"])
