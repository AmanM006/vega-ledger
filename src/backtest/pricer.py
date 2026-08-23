import math

def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def bs_price(S, K, T, r, sigma, option_type="c"):
    if T <= 0:
        return max(S - K, 0) if option_type == "c" else max(K - S, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == "c":
        return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)

def get_strike_for_delta(S, T, r, sigma, target_delta, option_type="c"):
    # Rough approximation of strike for a given delta
    # delta_c = norm_cdf(d1) -> d1 = norm_ppf(delta_c)
    # let's just do a binary search
    low, high = (S * 0.1, S * 2.0)
    for _ in range(30):
        mid = (low + high) / 2
        d1 = (math.log(S / mid) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        delta = norm_cdf(d1) if option_type == "c" else norm_cdf(d1) - 1
        if option_type == "c":
            if delta > target_delta:
                low = mid
            else:
                high = mid
        else:
            # put delta is negative. e.g. -0.16
            if delta < target_delta:
                high = mid
            else:
                low = mid
    return (low + high) / 2
