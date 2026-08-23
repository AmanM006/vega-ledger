"""
Earnings IV-crush sleeve.

Per PREREGISTRATION.md §3:
- Place iron condor 1-3 days BEFORE the earnings print
- Strikes beyond the ATM straddle-implied expected move
- Exit immediately after the print — no overnight directional hold
- Routes through the same risk gate as VRP sleeve with is_earnings_sleeve=True

Straddle-implied expected move = (ATM call mid + ATM put mid)
Short strikes placed just OUTSIDE that move (1.0x buffer by default).
Long wings 20% of the stock price further out for defined risk.
"""
from dataclasses import dataclass
from typing import Optional
import yfinance as yf


@dataclass
class EarningsSetup:
    ticker: str
    report_date: str          # YYYY-MM-DD
    report_time: str          # "pre" | "post"
    stock_price: float
    straddle_price: float
    expected_move: float      # $ absolute move implied by straddle
    expected_move_pct: float  # as fraction (e.g. 0.115 = 11.5%)
    short_call_strike: float
    long_call_strike: float
    short_put_strike: float
    long_put_strike: float
    expiry: str               # option expiry used (closest post-earnings)
    max_loss_dollars: float   # per-contract max loss (wing width - credit) * 100
    is_tradeable: bool
    reject_reason: Optional[str] = None


# Confirmed earnings for the hackathon window (Sep 3-4, 2026)
# Sourced from official IR pages: lululemon.com, ciena.com
# Cross-checked: web search Aug 23 2026
EARNINGS_CALENDAR = [
    {"ticker": "LULU", "report_date": "2026-09-03", "report_time": "post"},
    {"ticker": "CIEN", "report_date": "2026-09-03", "report_time": "pre"},
]

MIN_OI_THRESHOLD = 500      # minimum total OI on the closest expiry
MIN_LIQUID_STRIKES = 3      # minimum OTM strikes with bid > 0.05


def get_earnings_setup(ticker: str, report_date: str, report_time: str) -> EarningsSetup:
    """
    Compute iron condor parameters for an earnings play.
    Strikes are placed 1x the straddle-implied move OTM from current price.
    Wings are 15% of stock price further out for defined risk.
    """
    tk = yf.Ticker(ticker)
    info = tk.info
    price = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or info.get("previousClose", 0)
    )

    if price <= 0:
        return EarningsSetup(
            ticker=ticker, report_date=report_date, report_time=report_time,
            stock_price=0, straddle_price=0, expected_move=0, expected_move_pct=0,
            short_call_strike=0, long_call_strike=0, short_put_strike=0, long_put_strike=0,
            expiry="", max_loss_dollars=0, is_tradeable=False,
            reject_reason="Could not fetch stock price"
        )

    # Find closest expiry ON or just after the report date
    opts = tk.options
    expiry = None
    for o in opts:
        if o >= report_date:
            expiry = o
            break

    if not expiry:
        return EarningsSetup(
            ticker=ticker, report_date=report_date, report_time=report_time,
            stock_price=price, straddle_price=0, expected_move=0, expected_move_pct=0,
            short_call_strike=0, long_call_strike=0, short_put_strike=0, long_put_strike=0,
            expiry="", max_loss_dollars=0, is_tradeable=False,
            reject_reason=f"No options expiry found on or after {report_date}"
        )

    chain = tk.option_chain(expiry)
    calls = chain.calls
    puts = chain.puts

    total_oi = calls["openInterest"].sum() + puts["openInterest"].sum()
    otm_calls = calls[calls["strike"] > price]
    otm_puts = puts[puts["strike"] < price]
    liquid_calls = len(otm_calls[otm_calls["bid"] > 0.05])
    liquid_puts = len(otm_puts[otm_puts["bid"] > 0.05])

    if total_oi < MIN_OI_THRESHOLD or liquid_calls < MIN_LIQUID_STRIKES or liquid_puts < MIN_LIQUID_STRIKES:
        return EarningsSetup(
            ticker=ticker, report_date=report_date, report_time=report_time,
            stock_price=price, straddle_price=0, expected_move=0, expected_move_pct=0,
            short_call_strike=0, long_call_strike=0, short_put_strike=0, long_put_strike=0,
            expiry=expiry, max_loss_dollars=0, is_tradeable=False,
            reject_reason=f"Insufficient liquidity: OI={total_oi}, liquid_calls={liquid_calls}, liquid_puts={liquid_puts}"
        )

    # ATM straddle price
    atm_call = calls.iloc[(calls["strike"] - price).abs().argsort()[:1]]
    atm_put = puts.iloc[(puts["strike"] - price).abs().argsort()[:1]]
    atm_call_mid = (atm_call["bid"].values[0] + atm_call["ask"].values[0]) / 2
    atm_put_mid = (atm_put["bid"].values[0] + atm_put["ask"].values[0]) / 2
    straddle = atm_call_mid + atm_put_mid
    expected_move = straddle

    # Short strikes: 1.0x expected move beyond current price
    # Round to nearest $2.50 for standard option strikes
    def round_strike(s, step=2.5):
        return round(s / step) * step

    short_call = round_strike(price + expected_move)
    short_put = round_strike(price - expected_move)

    # Wing width: 15% of stock price for defined risk
    wing_width = max(round_strike(price * 0.15), 5.0)
    long_call = short_call + wing_width
    long_put = short_put - wing_width

    # Max loss = (wing_width - net_credit) * 100 per contract
    # We can't know net credit precisely without live bid/ask on those specific strikes,
    # so conservatively assume worst case: net credit = 0 (zero credit scenario)
    max_loss_per_contract = wing_width * 100

    return EarningsSetup(
        ticker=ticker,
        report_date=report_date,
        report_time=report_time,
        stock_price=price,
        straddle_price=straddle,
        expected_move=expected_move,
        expected_move_pct=expected_move / price,
        short_call_strike=short_call,
        long_call_strike=long_call,
        short_put_strike=short_put,
        long_put_strike=long_put,
        expiry=expiry,
        max_loss_dollars=max_loss_per_contract,
        is_tradeable=True,
    )


def get_all_earnings_setups() -> list[EarningsSetup]:
    setups = []
    for entry in EARNINGS_CALENDAR:
        setup = get_earnings_setup(entry["ticker"], entry["report_date"], entry["report_time"])
        setups.append(setup)
    return setups


if __name__ == "__main__":
    for setup in get_all_earnings_setups():
        print(f"\n{'='*50}")
        print(f"  {setup.ticker} | Earnings: {setup.report_date} ({setup.report_time}-market)")
        print(f"  Price: ${setup.stock_price:.2f}")
        print(f"  Straddle: ${setup.straddle_price:.2f} => Move: ${setup.expected_move:.2f} ({setup.expected_move_pct:.1%})")
        print(f"  Short call: {setup.short_call_strike} / Long call: {setup.long_call_strike}")
        print(f"  Short put:  {setup.short_put_strike} / Long put:  {setup.long_put_strike}")
        print(f"  Expiry: {setup.expiry} | Max loss/contract: ${setup.max_loss_dollars:.0f}")
        print(f"  Tradeable: {setup.is_tradeable}" + (f" | Reject: {setup.reject_reason}" if setup.reject_reason else ""))
