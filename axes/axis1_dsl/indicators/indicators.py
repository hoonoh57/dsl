import numpy as np


class TrendArray(np.ndarray):
    """Numeric indicator values carrying a precomputed compact colour state.

    ``trend_colors`` is an int8 array: 1=up, -1=down, 0=not established.
    Keeping it beside the calculated values avoids scanning the whole indicator
    again whenever the chart is rendered.
    """
    def __new__(cls, values, trend_colors):
        obj = np.asarray(values, dtype=np.float64).view(cls)
        obj.trend_colors = np.asarray(trend_colors, dtype=np.int8)
        return obj

    def __array_finalize__(self, source):
        if source is not None:
            self.trend_colors = getattr(source, "trend_colors", None)

class CoreTALib:
    @staticmethod
    def _to_arr(s):
        return np.asarray(s, dtype=np.float64)

    @staticmethod
    def _shift(arr, shift=1):
        out = np.full_like(arr, np.nan)
        if shift > 0:
            out[shift:] = arr[:-shift]
        elif shift < 0:
            out[:shift] = arr[-shift:]
        else:
            out[:] = arr
        return out

    shift = _shift

    @classmethod
    def _rolling(cls, series, period, operation):
        s = cls._to_arr(series)
        out = np.full_like(s, np.nan)
        period = int(period)
        if period <= 0:
            return out
        for i in range(period - 1, len(s)):
            out[i] = operation(s[i - period + 1:i + 1])
        return out

    @classmethod
    def highest(cls, series, period): return cls._rolling(series, period, np.nanmax)

    @classmethod
    def lowest(cls, series, period): return cls._rolling(series, period, np.nanmin)

    @classmethod
    def rolling_sum(cls, series, period): return cls._rolling(series, period, np.nansum)

    @classmethod
    def stdev(cls, series, period): return cls._rolling(series, period, np.nanstd)

    @classmethod
    def wma(cls, series, period):
        weights = np.arange(1, int(period) + 1, dtype=float)
        return cls._rolling(series, period, lambda values: np.dot(values, weights) / weights.sum())

    @classmethod
    def ma(cls, series, period, method="simple"):
        method = str(method).lower()
        if method in ("exponential", "지수"): return cls.ema(series, period)
        if method in ("weighted", "가중"): return cls.wma(series, period)
        return cls.sma(series, period)

    @classmethod
    def roc(cls, series, period):
        s = cls._to_arr(series)
        previous = cls._shift(s, int(period))
        return ((s / previous) - 1.0) * 100.0

    @classmethod
    def jma(cls, series, length=20, phase=0, power=2):
        """JMA port matching chart_base_trading/JmaIncrementalState.vb.

        The first ``length`` values use a running mean. Later values use the
        recursive JMA state and are rounded to one decimal place, exactly as
        the referenced chart engine does.
        """
        s = cls._to_arr(series)
        length = max(int(length), 1)
        safe_phase = float(np.clip(float(phase), -100.0, 100.0))
        safe_power = max(int(power), 1)
        phase_ratio = (safe_phase / 100.0) + 1.5
        beta = 0.45 * (length - 1) / ((0.45 * (length - 1)) + 2.0)
        alpha = beta ** safe_power
        one_minus_alpha = 1.0 - alpha
        alpha_squared = alpha * alpha
        smoothing_squared = one_minus_alpha * one_minus_alpha
        out = np.full_like(s, np.nan)
        colors = np.zeros(len(s), dtype=np.int8)
        if not len(s):
            return TrendArray(out, colors)
        e0 = float(s[0])
        e1 = 0.0
        e2 = 0.0
        price_sum = float(s[0])
        out[0] = e0
        for i in range(1, len(s)):
            close_value = float(s[i])
            e0 = (one_minus_alpha * close_value) + (alpha * e0)
            e1 = ((close_value - e0) * (1.0 - beta)) + (beta * e1)
            phase_adjusted = e0 + (phase_ratio * e1)
            e2 = ((phase_adjusted - out[i - 1]) * smoothing_squared) + (alpha_squared * e2)
            if i < length:
                out[i] = (price_sum + close_value) / (i + 1)
            else:
                out[i] = round((out[i - 1] + e2) * 10.0) / 10.0
            colors[i] = 1 if out[i] > out[i - 1] else (-1 if out[i] < out[i - 1] else colors[i - 1])
            price_sum += close_value
        return TrendArray(out, colors)

    @classmethod
    def supertrend(cls, high, low, close, period=10, multiplier=3.0):
        """Return the classic ATR Supertrend line and its trend direction.

        Direction is 1 for an uptrend and -1 for a downtrend.  The recursive
        final-band rules are kept here so chart colouring and strategy values
        always use the exact same state.
        """
        high, low, close = cls._to_arr(high), cls._to_arr(low), cls._to_arr(close)
        period, multiplier = max(int(period), 1), float(multiplier)
        atr = cls.atr(high, low, close, period)
        middle = (high + low) / 2.0
        basic_upper, basic_lower = middle + multiplier * atr, middle - multiplier * atr
        upper, lower = np.full_like(close, np.nan), np.full_like(close, np.nan)
        line, direction = np.full_like(close, np.nan), np.zeros(len(close), dtype=np.int8)
        finite = np.flatnonzero(np.isfinite(atr))
        if not len(finite):
            return line, direction
        start = int(finite[0])
        upper[start], lower[start], direction[start] = basic_upper[start], basic_lower[start], 1
        line[start] = lower[start]
        for i in range(start + 1, len(close)):
            if not np.isfinite(basic_upper[i]):
                continue
            upper[i] = (basic_upper[i] if basic_upper[i] < upper[i - 1] or close[i - 1] > upper[i - 1]
                        else upper[i - 1])
            lower[i] = (basic_lower[i] if basic_lower[i] > lower[i - 1] or close[i - 1] < lower[i - 1]
                        else lower[i - 1])
            if close[i] > upper[i]:
                direction[i] = 1
            elif close[i] < lower[i]:
                direction[i] = -1
            else:
                direction[i] = direction[i - 1]
            line[i] = lower[i] if direction[i] == 1 else upper[i]
        return TrendArray(line, direction), direction

    @classmethod
    def macd(cls, series, short=12, long=26, method="exponential"):
        return cls.ma(series, short, method) - cls.ma(series, long, method)

    @classmethod
    def true_range(cls, high, low, close):
        previous = cls.shift(close, 1)
        result=np.maximum(high-low,np.maximum(np.abs(high-previous),np.abs(low-previous)))
        if len(result):result[0]=high[0]-low[0]
        return result

    @classmethod
    def rma(cls,series,period=14):
        """Wilder moving average (TradingView ta.rma / TA indicator smoothing)."""
        source=cls._to_arr(series);period=int(period);out=np.full_like(source,np.nan)
        if period<=0:return out
        start=None
        for i in range(period-1,len(source)):
            window=source[i-period+1:i+1]
            if np.all(np.isfinite(window)):start=i;out[i]=np.mean(window);break
        if start is None:return out
        for i in range(start+1,len(source)):out[i]=(out[i-1]*(period-1)+source[i])/period
        return out

    @classmethod
    def atr(cls, high, low, close, period=14): return cls.rma(cls.true_range(high, low, close), period)

    @classmethod
    def trix(cls, series, period=12):
        triple = cls.ema(cls.ema(cls.ema(series, period), period), period)
        previous = cls.shift(triple, 1)
        return np.divide(triple - previous, previous, out=np.full_like(triple, np.nan), where=previous != 0) * 100

    @classmethod
    def cci(cls, high, low, close, period=20):
        typical = (high + low + close) / 3.0
        average = cls.sma(typical, period)
        deviation = cls._rolling(typical, period, lambda x: np.mean(np.abs(x - np.mean(x))))
        return np.divide(typical - average, .015 * deviation, out=np.full_like(typical, np.nan), where=deviation != 0)

    @classmethod
    def adx(cls, high, low, close, period=14):
        up, down = high - cls.shift(high, 1), cls.shift(low, 1) - low
        plus_dm = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)
        atr = cls.atr(high, low, close, period)
        plus_di = np.divide(cls.rma(plus_dm, period), atr, out=np.zeros_like(atr), where=atr != 0) * 100
        minus_di = np.divide(cls.rma(minus_dm, period), atr, out=np.zeros_like(atr), where=atr != 0) * 100
        total = plus_di + minus_di
        dx = np.divide(np.abs(plus_di - minus_di), total, out=np.zeros_like(total), where=total != 0) * 100
        return cls.rma(dx, period)

    @classmethod
    def nrange(cls, high, low, period): return cls.highest(high, period) - cls.lowest(low, period)

    @classmethod
    def williams_r(cls, high, low, close, period):
        hh, ll = cls.highest(high, period), cls.lowest(low, period)
        return np.divide(hh - close, hh - ll, out=np.full_like(hh, np.nan), where=hh != ll) * -100

    @classmethod
    def abs_range(cls, series, period): return np.abs(cls.highest(series, period) - cls.lowest(series, period))

    @classmethod
    def sum_abs_r(cls, series, period): return cls.rolling_sum(np.abs(series - cls.shift(series, 1)), period)

    @classmethod
    def vhf(cls, series, period):
        top = np.abs(cls.highest(series, period) - cls.lowest(series, period))
        bottom = cls.sum_abs_r(series, period)
        return np.divide(top, bottom, out=np.full_like(top, np.nan), where=bottom != 0)

    @classmethod
    def bars_since(cls, condition):
        cond = np.asarray(condition, dtype=bool); out = np.full(len(cond), np.nan); count = 0
        seen = False
        for i, hit in enumerate(cond):
            if hit: count, seen = 0, True
            elif seen: count += 1
            if seen: out[i] = count
        return out

    @classmethod
    def count_since(cls, condition, data):
        cond, values = np.asarray(condition, bool), np.asarray(data, bool); out = np.zeros(len(cond)); count = 0
        for i in range(len(cond)):
            if cond[i]: count = 0
            if values[i]: count += 1
            out[i] = count
        return out

    @classmethod
    def highest_since(cls, condition, data): return cls._since(condition, data, max)

    @classmethod
    def lowest_since(cls, condition, data): return cls._since(condition, data, min)

    @classmethod
    def _since(cls, condition, data, operation):
        cond, values = np.asarray(condition, bool), cls._to_arr(data); out = np.full_like(values, np.nan); current = np.nan
        for i in range(len(values)):
            if cond[i] or np.isnan(current): current = values[i]
            else: current = operation(current, values[i])
            out[i] = current
        return out

    @classmethod
    def value_when(cls, nth, condition, data):
        """Value at the Nth most recent occurrence (0 = latest), Pine-compatible."""
        nth = int(nth)
        if nth < 0: raise ValueError("ta.value_when occurrence는 0 이상이어야 합니다.")
        cond, values = np.asarray(condition, bool), cls._to_arr(data); out = np.full_like(values, np.nan); hits = []
        for i in range(len(values)):
            if cond[i]: hits.append(values[i])
            if len(hits) > nth: out[i] = hits[-(nth + 1)]
        return out

    @classmethod
    def sma(cls, series: np.ndarray, period: int) -> np.ndarray:
        s = cls._to_arr(series)
        out = np.full_like(s, np.nan)
        if len(s) < period or period <= 0:
            return out
        cumsum = np.cumsum(np.nan_to_num(s))
        cumsum[period:] = cumsum[period:] - cumsum[:-period]
        out[period - 1:] = cumsum[period - 1:] / period
        return out

    @classmethod
    def ema(cls, series: np.ndarray, period: int) -> np.ndarray:
        s = cls._to_arr(series)
        out = np.full_like(s, np.nan)
        period = int(period)
        if len(s) < period or period <= 0:
            return out
        k = 2.0 / (period + 1.0)
        start = None
        for i in range(period - 1, len(s)):
            window = s[i - period + 1:i + 1]
            if np.all(np.isfinite(window)):
                start = i
                out[i] = np.mean(window)
                break
        if start is None:
            return out
        for i in range(start + 1, len(s)):
            out[i] = (s[i] * k) + (out[i - 1] * (1.0 - k))
        return out

    @classmethod
    def rsi(cls, series: np.ndarray, period: int = 14) -> np.ndarray:
        s = cls._to_arr(series)
        delta = np.diff(s, prepend=s[0])
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = cls.rma(gain[1:],period);avg_loss=cls.rma(loss[1:],period)
        avg_gain=np.concatenate(([np.nan],avg_gain));avg_loss=np.concatenate(([np.nan],avg_loss))
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        return 100.0 - (100.0 / (1.0 + rs))

    @classmethod
    def bbands(cls, series: np.ndarray, period: int = 20, mult: float = 2.0):
        mid = cls.sma(series, period)
        s = cls._to_arr(series)
        std = np.full_like(s, np.nan)
        for i in range(period - 1, len(s)):
            std[i] = np.std(s[i - period + 1 : i + 1])
        upper = mid + (mult * std)
        lower = mid - (mult * std)
        return upper, mid, lower

    @classmethod
    def crossover(cls, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        arr_a = cls._to_arr(a)
        arr_b = cls._to_arr(b) if isinstance(b, np.ndarray) else np.full_like(arr_a, b)
        prev_a = cls._shift(arr_a, 1)
        prev_b = cls._shift(arr_b, 1)
        return (prev_a <= prev_b) & (arr_a > arr_b)

    @classmethod
    def crossunder(cls, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        arr_a = cls._to_arr(a)
        arr_b = cls._to_arr(b) if isinstance(b, np.ndarray) else np.full_like(arr_a, b)
        prev_a = cls._shift(arr_a, 1)
        prev_b = cls._shift(arr_b, 1)
        return (prev_a >= prev_b) & (arr_a < arr_b)
