"""Executable DSL feature catalog for Live Studio.

Every registered function gets a concrete DSL example.  The catalog is intentionally
engine-facing: a feature is considered verified only after Parser, Semantic and the
real BacktestEngine all accept the example under its declared fixture.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Iterable

import numpy as np

from core.function_registry import FUNCTION_SPECS


@dataclass(frozen=True)
class FeatureCase:
    feature_id: str
    category: str
    title: str
    description: str
    dsl_code: str
    fixture: str = "daily"
    settings: dict | None = None
    signature: str | None = None

    def public_dict(self) -> dict:
        value = asdict(self)
        value["settings"] = dict(self.settings or {})
        return value


def _call_expression(name: str) -> str:
    cond = "close > ta.sma(close, 5)"
    reset = "close < ta.sma(close, 5)"
    table = {
        "ta.sma": "ta.sma(close, 10)",
        "ta.ema": "ta.ema(close, 10)",
        "ta.wma": "ta.wma(close, 10)",
        "ta.rma": "ta.rma(close, 10)",
        "ta.ma": "ta.ma(close, 10, \"simple\")",
        "ta.rsi": "ta.rsi(close, 14)",
        "ta.crossover": "ta.crossover(ta.sma(close, 5), ta.sma(close, 20))",
        "ta.crossunder": "ta.crossunder(ta.sma(close, 5), ta.sma(close, 20))",
        "ta.highest": "ta.highest(high, 14)",
        "ta.lowest": "ta.lowest(low, 14)",
        "ta.sum": "ta.sum(volume, 10)",
        "ta.stdev": "ta.stdev(close, 14)",
        "ta.roc": "ta.roc(close, 10)",
        "ta.jma": "ta.jma(close, 14, 0, 2)",
        "ta.supertrend": "ta.supertrend(10, 3)",
        "ta.supertrend_direction": "ta.supertrend_direction(10, 3)",
        "ta.macd": "ta.macd(close, 12, 26, \"exponential\")",
        "user.macd_normalized": "user.macd_normalized(close, \"hist_abs_pct\", 12, 26, 9, \"exponential\")",
        "ta.atr": "ta.atr(14)",
        "ta.adx": "ta.adx(14)",
        "ta.trix": "ta.trix(12)",
        "ta.cci": "ta.cci(20)",
        "ta.nrange": "ta.nrange(14)",
        "ta.williams_r": "ta.williams_r(14)",
        "ta.abs_range": "ta.abs_range(14)",
        "ta.sum_abs_r": "ta.sum_abs_r(14)",
        "ta.vhf": "ta.vhf(14)",
        "ta.shift": "ta.shift(close, 1)",
        "ta.count_since": f"ta.count_since({cond}, {reset})",
        "ta.bars_since": f"ta.bars_since({cond})",
        "ta.highest_since": f"ta.highest_since({cond}, high)",
        "ta.lowest_since": f"ta.lowest_since({cond}, low)",
        "ta.value_when": f"ta.value_when(1, {cond}, close)",
        "logic.ifelse": f"logic.ifelse({cond}, close, open)",
        "math.log": "math.log(close)",
        "math.log10": "math.log10(close)",
        "math.abs": "math.abs(close - open)",
        "math.sqrt": "math.sqrt(close)",
        "math.sin": "math.sin(close / 1000)",
        "math.cos": "math.cos(close / 1000)",
        "math.tan": "math.tan(close / 1000)",
        "math.asin": "math.asin((close / close) * 0.5)",
        "math.acos": "math.acos((close / close) * 0.5)",
        "math.atan": "math.atan(close / 1000)",
        "math.pow": "math.pow(close, 2)",
        "math.max": "math.max(close, open)",
        "math.min": "math.min(close, open)",
        "session.day_open": "session.day_open()",
        "session.day_high": "session.day_high()",
        "session.day_low": "session.day_low()",
        "session.prev_open": "session.prev_open()",
        "session.prev_high": "session.prev_high()",
        "session.prev_low": "session.prev_low()",
        "session.prev_close": "session.prev_close()",
        "state.edge": f"state.edge({cond})",
        "state.falling_edge": f"state.falling_edge({cond})",
        "state.ready_after": f"state.ready_after({cond}, 3)",
        "state.hold": f"state.hold({cond}, 3)",
        "state.persist": f"state.persist({cond}, 3)",
        "state.latch": f"state.latch({cond}, {reset}, false)",
        "state.count": f"state.count({cond}, {reset})",
        "state.regime": f"state.regime({cond}, {reset}, 0)",
        "mtf.open": "mtf.open(\"5m\")",
        "mtf.high": "mtf.high(\"5m\")",
        "mtf.low": "mtf.low(\"5m\")",
        "mtf.close": "mtf.close(\"5m\")",
        "mtf.volume": "mtf.volume(\"5m\")",
        "mtf.sma": "mtf.sma(\"5m\", 3)",
    }
    if name not in table:
        raise KeyError(f"feature example is missing: {name}")
    return table[name]


def _function_dsl(name: str, category: str) -> str:
    timeframe = "1m" if category in {"mtf", "session"} else "1d"
    expr = _call_expression(name)
    safe_name = name.replace(".", "_")
    return f'''strategy "Feature_{safe_name}" {{
    timeframe = "{timeframe}"
    feature_value = {expr}
    ma_fast = ta.sma(close, 5)
    ma_slow = ta.sma(close, 20)
    entry_cond = ta.crossover(ma_fast, ma_slow)
    exit_cond = ta.crossunder(ma_fast, ma_slow)
    on(entry_cond) {{ order.buy(type = "MARKET") }}
    on(exit_cond) {{ order.close_position() }}
}}'''


def _grammar_cases() -> list[FeatureCase]:
    return [
        FeatureCase(
            "grammar.input", "grammar", "input scalar", "input scalar가 지표 period에 전달되는지 검증",
            '''strategy "Feature_Input" {
    timeframe = "1d"
    input period = 7
    line = ta.sma(close, period)
    entry_cond = ta.crossover(close, line)
    exit_cond = ta.crossunder(close, line)
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}''',
        ),
        FeatureCase(
            "grammar.history", "grammar", "과거 참조", "close[1] 시계열 과거 참조 검증",
            '''strategy "Feature_History" {
    timeframe = "1d"
    entry_cond = close > close[1]
    exit_cond = close < close[1]
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}''',
        ),
        FeatureCase(
            "grammar.on_bar_state", "grammar", "on_bar state", "state + on_bar + if/else 상태 전이 검증",
            '''strategy "Feature_OnBar" {
    timeframe = "1d"
    state armed = false
    on_bar {
        if (close > open) {
            set armed = true
        }
        else {
            set armed = false
        }
    }
    entry_cond = armed
    exit_cond = not armed
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}''',
        ),
        FeatureCase(
            "order.long_market", "orders", "Long MARKET", "order.buy / order.close_position 시장가 경로",
            '''strategy "Feature_LongMarket" {
    timeframe = "1d"
    entry_cond = ta.crossover(ta.sma(close, 5), ta.sma(close, 20))
    exit_cond = ta.crossunder(ta.sma(close, 5), ta.sma(close, 20))
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}''',
        ),
        FeatureCase(
            "order.short_market", "orders", "Short MARKET", "order.sell_short / order.close_short 시장가 경로",
            '''strategy "Feature_ShortMarket" {
    timeframe = "1d"
    entry_cond = ta.crossunder(ta.sma(close, 5), ta.sma(close, 20))
    exit_cond = ta.crossover(ta.sma(close, 5), ta.sma(close, 20))
    on(entry_cond) { order.sell_short(type = "MARKET") }
    on(exit_cond) { order.close_short() }
}''',
        ),
        FeatureCase(
            "order.limit_cancel", "orders", "LIMIT + cancel", "stable client id pending 주문과 generic cancel 경로",
            '''strategy "Feature_LimitCancel" {
    timeframe = "1d"
    arm = ta.crossover(ta.sma(close, 5), ta.sma(close, 20))
    cancel_it = ta.crossunder(ta.sma(close, 5), ta.sma(close, 20))
    on(arm) { order.buy(type = "LIMIT", id = "catalog-limit", limit = close * 0.98, tif = "GTC") }
    on(cancel_it) { order.cancel(id = "catalog-limit") }
}''',
        ),
        FeatureCase(
            "execution.next_open", "execution", "next_open", "prior completed bar signal이 next open에 체결되는 경로",
            '''strategy "Feature_NextOpen" {
    timeframe = "1d"
    entry_cond = ta.crossover(ta.sma(close, 5), ta.sma(close, 20))
    exit_cond = ta.crossunder(ta.sma(close, 5), ta.sma(close, 20))
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}''', settings={"signal_mode": "next_open"},
        ),
        FeatureCase(
            "risk.stop_take_trailing", "execution", "Risk exits", "stop loss / take profit / trailing 설정 경로",
            '''strategy "Feature_Risk" {
    timeframe = "1d"
    entry_cond = ta.crossover(ta.sma(close, 5), ta.sma(close, 20))
    exit_cond = ta.crossunder(ta.sma(close, 5), ta.sma(close, 20))
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}''', settings={"stop_loss_pct": 3.0, "take_profit_pct": 5.0, "trailing_enabled": True, "trailing_activation_pct": 2.0, "trailing_distance_pct": 1.0},
        ),
    ]


def all_feature_cases() -> tuple[FeatureCase, ...]:
    functions = []
    for name, spec in FUNCTION_SPECS.items():
        fixture = "intraday" if spec.category in {"mtf", "session"} else "daily"
        functions.append(FeatureCase(
            feature_id=name,
            category=spec.category,
            title=name,
            description=spec.signature,
            dsl_code=_function_dsl(name, spec.category),
            fixture=fixture,
            signature=spec.signature,
        ))
    return tuple(functions + _grammar_cases())


FEATURE_CASES: Dict[str, FeatureCase] = {case.feature_id: case for case in all_feature_cases()}


def cases_by_category() -> dict[str, list[FeatureCase]]:
    result: dict[str, list[FeatureCase]] = {}
    for case in FEATURE_CASES.values():
        result.setdefault(case.category, []).append(case)
    for values in result.values():
        values.sort(key=lambda x: x.feature_id)
    return dict(sorted(result.items()))


def intraday_market(bars_count: int = 360) -> dict:
    """Deterministic 1m multi-session fixture for session/MTF engine verification."""
    rng = np.random.default_rng(42)
    times = []
    cursor = datetime(2020, 1, 2, 9, 0)
    while len(times) < bars_count:
        if cursor.hour < 15 or (cursor.hour == 15 and cursor.minute <= 30):
            times.append(cursor.strftime("%Y%m%d%H%M%S"))
        cursor += timedelta(minutes=1)
        if cursor.hour > 15 or (cursor.hour == 15 and cursor.minute > 30):
            next_day = cursor.date() + timedelta(days=1)
            cursor = datetime.combine(next_day, datetime.min.time()).replace(hour=9)
    close = 1000.0 + np.cumsum(rng.normal(0, 1.5, len(times)))
    spread = rng.uniform(0.2, 2.0, len(times))
    open_ = close + rng.normal(0, 0.5, len(times))
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.integers(100, 5000, len(times)).astype(float)
    return {
        "time": times,
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": volume.tolist(),
        "_meta": {"source": "dsl_feature_catalog_intraday_fixture", "timeframe": "1m"},
    }