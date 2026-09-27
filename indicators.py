"""Technical indicators: MA, MACD, RSI, KDJ, Bollinger Bands."""

def calc_ma(closes: list, period: int) -> list:
    """Simple Moving Average."""
    result = []
    for i in range(len(closes)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(round(sum(closes[i-period+1:i+1]) / period, 4))
    return result


def calc_ema(values: list, period: int) -> list:
    """Exponential Moving Average."""
    k = 2 / (period + 1)
    result = [None] * (period - 1)
    ema = sum(values[:period]) / period
    result.append(round(ema, 4))
    for i in range(period, len(values)):
        ema = values[i] * k + ema * (1 - k)
        result.append(round(ema, 4))
    return result


def calc_macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD indicator."""
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)
    dif = []
    for i in range(len(closes)):
        if i < slow - 1:
            dif.append(None)
        else:
            dif.append(round(ema_fast[i] - ema_slow[i], 4))
    valid_dif = [d for d in dif if d is not None]
    dea_raw = calc_ema(valid_dif, signal) if len(valid_dif) >= signal else []
    dea = [None] * (slow - 1 + signal - 1) + dea_raw
    hist = []
    for i in range(len(dif)):
        if dif[i] is not None and i < len(dea) and dea[i] is not None:
            hist.append(round(2 * (dif[i] - dea[i]), 4))
        else:
            hist.append(None)
    return {"dif": dif, "dea": dea, "hist": hist}


def calc_rsi(closes: list, period: int = 14) -> list:
    """Relative Strength Index."""
    result = [None] * period
    for i in range(period, len(closes)):
        gains = []
        losses = []
        for j in range(i - period, i):
            change = closes[j + 1] - closes[j]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(round(100 - 100 / (1 + rs), 2))
    return result


def calc_kdj(highs: list, lows: list, closes: list, period: int = 9) -> dict:
    """KDJ indicator."""
    k_vals = [None] * (period - 1)
    d_vals = [None] * (period - 1)
    j_vals = [None] * (period - 1)
    prev_k = 50.0
    prev_d = 50.0
    for i in range(period - 1, len(closes)):
        high_n = max(highs[i - period + 1:i + 1])
        low_n = min(lows[i - period + 1:i + 1])
        rsv = (closes[i] - low_n) / (high_n - low_n) * 100 if high_n != low_n else 50.0
        k = 2 / 3 * prev_k + 1 / 3 * rsv
        d = 2 / 3 * prev_d + 1 / 3 * k
        j = 3 * k - 2 * d
        k_vals.append(round(k, 2))
        d_vals.append(round(d, 2))
        j_vals.append(round(j, 2))
        prev_k = k
        prev_d = d
    return {"k": k_vals, "d": d_vals, "j": j_vals}


def calc_boll(closes: list, period: int = 20, std_dev: float = 2.0) -> dict:
    """Bollinger Bands."""
    result = {"upper": [], "middle": [], "lower": []}
    for i in range(len(closes)):
        if i < period - 1:
            result["upper"].append(None)
            result["middle"].append(None)
            result["lower"].append(None)
        else:
            window = closes[i - period + 1:i + 1]
            ma = sum(window) / period
            variance = sum((x - ma) ** 2 for x in window) / period
            sd = variance ** 0.5
            result["upper"].append(round(ma + std_dev * sd, 4))
            result["middle"].append(round(ma, 4))
            result["lower"].append(round(ma - std_dev * sd, 4))
    return result
