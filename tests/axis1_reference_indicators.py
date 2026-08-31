"""Independent NumPy reference formulas for AXIS 1 indicator differential tests.

This file intentionally does not import AXIS 1 implementation modules.  It is a
stable test-side reference surface used by Step 5-9 to detect accidental changes
in indicator semantics, warmup windows and event-history behavior.
"""
from __future__ import annotations

import numpy as np


def arr(values):
    return np.asarray(values, dtype=np.float64)


def shift(values, bars=1):
    source = arr(values)
    out = np.full_like(source, np.nan)
    bars = int(bars)
    if bars > 0:
        out[bars:] = source[:-bars]
    elif bars < 0:
        out[:bars] = source[-bars:]
    else:
        out[:] = source
    return out


def rolling(values, period, operation):
    source = arr(values)
    out = np.full_like(source, np.nan)
    period = int(period)
    if period <= 0:
        return out
    for index in range(period - 1, len(source)):
        out[index] = operation(source[index - period + 1:index + 1])
    return out


def highest(values, period):
    return rolling(values, period, np.nanmax)


def lowest(values, period):
    return rolling(values, period, np.nanmin)


def rolling_sum(values, period):
    return rolling(values, period, np.nansum)


def stdev(values, period):
    return rolling(values, period, np.nanstd)


def sma(values, period):
    source = arr(values)
    out = np.full_like(source, np.nan)
    period = int(period)
    if period <= 0 or len(source) < period:
        return out
    cumulative = np.cumsum(np.nan_to_num(source))
    cumulative[period:] -= cumulative[:-period]
    out[period - 1:] = cumulative[period - 1:] / period
    return out


def ema(values, period):
    source = arr(values)
    out = np.full_like(source, np.nan)
    period = int(period)
    if period <= 0 or len(source) < period:
        return out
    alpha = 2.0 / (period + 1.0)
    start = None
    for index in range(period - 1, len(source)):
        window = source[index - period + 1:index + 1]
        if np.all(np.isfinite(window)):
            start = index
            out[index] = np.mean(window)
            break
    if start is None:
        return out
    for index in range(start + 1, len(source)):
        out[index] = source[index] * alpha + out[index - 1] * (1.0 - alpha)
    return out


def rma(values, period):
    source = arr(values)
    out = np.full_like(source, np.nan)
    period = int(period)
    if period <= 0:
        return out
    start = None
    for index in range(period - 1, len(source)):
        window = source[index - period + 1:index + 1]
        if np.all(np.isfinite(window)):
            start = index
            out[index] = np.mean(window)
            break
    if start is None:
        return out
    for index in range(start + 1, len(source)):
        out[index] = (out[index - 1] * (period - 1) + source[index]) / period
    return out


def wma(values, period):
    period = int(period)
    weights = np.arange(1, period + 1, dtype=float)
    return rolling(values, period, lambda window: np.dot(window, weights) / weights.sum())


def ma(values, period, method="simple"):
    name = str(method).lower()
    if name in {"exponential", "지수"}:
        return ema(values, period)
    if name in {"weighted", "가중"}:
        return wma(values, period)
    return sma(values, period)


def roc(values, period):
    source = arr(values)
    previous = shift(source, int(period))
    return ((source / previous) - 1.0) * 100.0


def true_range(high, low, close):
    high = arr(high)
    low = arr(low)
    close = arr(close)
    previous = shift(close, 1)
    result = np.maximum(high - low, np.maximum(np.abs(high - previous), np.abs(low - previous)))
    if len(result):
        result[0] = high[0] - low[0]
    return result


def atr(high, low, close, period=14):
    return rma(true_range(high, low, close), period)


def rsi(values, period=14):
    source = arr(values)
    delta = np.diff(source, prepend=source[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = rma(gain[1:], period)
    avg_loss = rma(loss[1:], period)
    avg_gain = np.concatenate(([np.nan], avg_gain))
    avg_loss = np.concatenate(([np.nan], avg_loss))
    rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
    return 100.0 - (100.0 / (1.0 + rs))


def macd(values, short=12, long=26, method="exponential"):
    return ma(values, short, method) - ma(values, long, method)


def trix(values, period=12):
    triple = ema(ema(ema(values, period), period), period)
    previous = shift(triple, 1)
    return np.divide(
        triple - previous,
        previous,
        out=np.full_like(triple, np.nan),
        where=previous != 0,
    ) * 100.0


def cci(high, low, close, period=20):
    typical = (arr(high) + arr(low) + arr(close)) / 3.0
    average = sma(typical, period)
    deviation = rolling(typical, period, lambda window: np.mean(np.abs(window - np.mean(window))))
    return np.divide(
        typical - average,
        0.015 * deviation,
        out=np.full_like(typical, np.nan),
        where=deviation != 0,
    )


def adx(high, low, close, period=14):
    high = arr(high)
    low = arr(low)
    up = high - shift(high, 1)
    down = shift(low, 1) - low
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    atr_values = atr(high, low, close, period)
    plus_di = np.divide(rma(plus_dm, period), atr_values, out=np.zeros_like(atr_values), where=atr_values != 0) * 100.0
    minus_di = np.divide(rma(minus_dm, period), atr_values, out=np.zeros_like(atr_values), where=atr_values != 0) * 100.0
    total = plus_di + minus_di
    dx = np.divide(np.abs(plus_di - minus_di), total, out=np.zeros_like(total), where=total != 0) * 100.0
    return rma(dx, period)


def nrange(high, low, period):
    return highest(high, period) - lowest(low, period)


def williams_r(high, low, close, period):
    hh = highest(high, period)
    ll = lowest(low, period)
    return np.divide(hh - arr(close), hh - ll, out=np.full_like(hh, np.nan), where=hh != ll) * -100.0


def abs_range(values, period):
    return np.abs(highest(values, period) - lowest(values, period))


def sum_abs_r(values, period):
    source = arr(values)
    return rolling_sum(np.abs(source - shift(source, 1)), period)


def vhf(values, period):
    top = abs_range(values, period)
    bottom = sum_abs_r(values, period)
    return np.divide(top, bottom, out=np.full_like(top, np.nan), where=bottom != 0)


def bars_since(condition):
    source = np.asarray(condition, dtype=bool)
    out = np.full(len(source), np.nan)
    count = 0
    seen = False
    for index, hit in enumerate(source):
        if hit:
            count = 0
            seen = True
        elif seen:
            count += 1
        if seen:
            out[index] = count
    return out


def count_since(condition, data):
    resets = np.asarray(condition, dtype=bool)
    values = np.asarray(data, dtype=bool)
    out = np.zeros(len(resets))
    count = 0
    for index in range(len(resets)):
        if resets[index]:
            count = 0
        if values[index]:
            count += 1
        out[index] = count
    return out


def _since(condition, data, operation):
    trigger = np.asarray(condition, dtype=bool)
    values = arr(data)
    out = np.full_like(values, np.nan)
    current = np.nan
    for index in range(len(values)):
        if trigger[index] or np.isnan(current):
            current = values[index]
        else:
            current = operation(current, values[index])
        out[index] = current
    return out


def highest_since(condition, data):
    return _since(condition, data, max)


def lowest_since(condition, data):
    return _since(condition, data, min)


def value_when(nth, condition, data):
    nth = int(nth)
    trigger = np.asarray(condition, dtype=bool)
    values = arr(data)
    out = np.full_like(values, np.nan)
    hits = []
    for index in range(len(values)):
        if trigger[index]:
            hits.append(values[index])
        if len(hits) > nth:
            out[index] = hits[-(nth + 1)]
    return out


def crossover(a, b):
    left = arr(a)
    right = arr(b) if isinstance(b, np.ndarray) else np.full_like(left, b)
    return (shift(left, 1) <= shift(right, 1)) & (left > right)


def crossunder(a, b):
    left = arr(a)
    right = arr(b) if isinstance(b, np.ndarray) else np.full_like(left, b)
    return (shift(left, 1) >= shift(right, 1)) & (left < right)


def bbands(values, period=20, mult=2.0):
    source = arr(values)
    middle = sma(source, period)
    deviation = np.full_like(source, np.nan)
    for index in range(int(period) - 1, len(source)):
        deviation[index] = np.std(source[index - int(period) + 1:index + 1])
    return middle + mult * deviation, middle, middle - mult * deviation


def jma(values, length=20, phase=0, power=2):
    source = arr(values)
    length = max(int(length), 1)
    safe_phase = float(np.clip(float(phase), -100.0, 100.0))
    safe_power = max(int(power), 1)
    phase_ratio = safe_phase / 100.0 + 1.5
    beta = 0.45 * (length - 1) / ((0.45 * (length - 1)) + 2.0)
    alpha = beta ** safe_power
    one_minus_alpha = 1.0 - alpha
    alpha_squared = alpha * alpha
    smoothing_squared = one_minus_alpha * one_minus_alpha
    out = np.full_like(source, np.nan)
    colors = np.zeros(len(source), dtype=np.int8)
    if not len(source):
        return out, colors
    e0 = float(source[0])
    e1 = 0.0
    e2 = 0.0
    price_sum = float(source[0])
    out[0] = e0
    for index in range(1, len(source)):
        close_value = float(source[index])
        e0 = one_minus_alpha * close_value + alpha * e0
        e1 = (close_value - e0) * (1.0 - beta) + beta * e1
        phase_adjusted = e0 + phase_ratio * e1
        e2 = (phase_adjusted - out[index - 1]) * smoothing_squared + alpha_squared * e2
        if index < length:
            out[index] = (price_sum + close_value) / (index + 1)
        else:
            out[index] = round((out[index - 1] + e2) * 10.0) / 10.0
        colors[index] = 1 if out[index] > out[index - 1] else (-1 if out[index] < out[index - 1] else colors[index - 1])
        price_sum += close_value
    return out, colors


def supertrend(high, low, close, period=10, multiplier=3.0):
    high = arr(high)
    low = arr(low)
    close = arr(close)
    atr_values = atr(high, low, close, period)
    middle = (high + low) / 2.0
    basic_upper = middle + multiplier * atr_values
    basic_lower = middle - multiplier * atr_values
    upper = np.full_like(close, np.nan)
    lower = np.full_like(close, np.nan)
    line = np.full_like(close, np.nan)
    direction = np.zeros(len(close), dtype=np.int8)
    finite = np.flatnonzero(np.isfinite(atr_values))
    if not len(finite):
        return line, direction
    start = int(finite[0])
    upper[start] = basic_upper[start]
    lower[start] = basic_lower[start]
    direction[start] = 1
    line[start] = lower[start]
    for index in range(start + 1, len(close)):
        if not np.isfinite(basic_upper[index]):
            continue
        upper[index] = (
            basic_upper[index]
            if basic_upper[index] < upper[index - 1] or close[index - 1] > upper[index - 1]
            else upper[index - 1]
        )
        lower[index] = (
            basic_lower[index]
            if basic_lower[index] > lower[index - 1] or close[index - 1] < lower[index - 1]
            else lower[index - 1]
        )
        if close[index] > upper[index]:
            direction[index] = 1
        elif close[index] < lower[index]:
            direction[index] = -1
        else:
            direction[index] = direction[index - 1]
        line[index] = lower[index] if direction[index] == 1 else upper[index]
    return line, direction


def normalized_macd(values, component, short=12, long=26, signal=9, method="exponential"):
    source = arr(values)
    macd_line = macd(source, short, long, method)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    component = str(component).lower()
    if component == "macd":
        return macd_line
    if component == "signal":
        return signal_line
    if component == "hist":
        return histogram
    if component == "hist_abs_pct":
        denominator = np.abs(source)
        return np.divide(
            np.abs(histogram) * 100.0,
            denominator,
            out=np.full_like(histogram, np.nan),
            where=denominator != 0,
        )
    raise ValueError(component)
