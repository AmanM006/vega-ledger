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

    if vix_rising:
        reasons.append("VIX rising >5% over 5 sessions — vol expansion veto")

    if iv_rank <= 25:
        reasons.append(
            f"IV rank too low (rank={iv_rank:.0f}) — premium too cheap, not worth selling"
        )

    if vix_now > 30:
        reasons.append("VIX > 30 — outside tested regime, sit out")

    return RegimeSignal(tradeable=len(reasons) == 0, reasons=reasons)
