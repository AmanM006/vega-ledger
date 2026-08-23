"""
Regime-conditional entry filter.

Backed by: regime-filtered short iron condors (VIX below its 200-day MA and
not rising) showed Sharpe 0.52 -> 0.81 and max drawdown 28.3% -> 16.1% vs.
unconditional entry (see research/PREREGISTRATION.md and the VRP literature
cited in your write-up). This is the single highest-leverage rule in the
whole system — do not weaken it under demo pressure to force a trade.
"""
from dataclasses import dataclass


@dataclass
class RegimeSignal:
    tradeable: bool
    reasons: list[str]


def check_regime(
    vix_now: float,
    vix_200dma: float,
    vix_5d_ago: float,
    iv_rank: float,
    iv_percentile: float,
) -> RegimeSignal:
    reasons = []

    vix_rising = vix_now > vix_5d_ago * 1.05
    vix_above_200dma = vix_now > vix_200dma

    if vix_above_200dma and vix_rising:
        reasons.append("VIX above 200DMA and rising >5% over 5 sessions — regime veto")

    if iv_rank <= 50 or iv_percentile <= 50:
        reasons.append(
            f"IV rank/percentile too low (rank={iv_rank:.0f}, pct={iv_percentile:.0f}) "
            "— VRP edge minimal, not worth selling"
        )

    if vix_now > 30:
        reasons.append("VIX > 30 — outside tested regime, sit out")

    return RegimeSignal(tradeable=len(reasons) == 0, reasons=reasons)
