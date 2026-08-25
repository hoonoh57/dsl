"""Canonical function signatures for DSL prompt/semantic/runtime parity checks."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    minimum: int
    maximum: int
    returns: str
    signature: str
    category: str


def _spec(name, minimum, maximum, returns, signature, category):
    return FunctionSpec(name, minimum, maximum, returns, signature, category)


FUNCTION_SPECS = {
    item.name: item for item in [
        _spec("ta.sma",2,3,"series<number>","ta.sma(series, period[, bars]) -> series","ta"),
        _spec("ta.ema",2,3,"series<number>","ta.ema(series, period[, bars]) -> series","ta"),
        _spec("ta.wma",2,3,"series<number>","ta.wma(series, period[, bars]) -> series","ta"),
        _spec("ta.rma",2,3,"series<number>","ta.rma(series, period[, bars]) -> series (Wilder)","ta"),
        _spec("ta.ma",2,4,"series<number>","ta.ma(series, period[, method, bars]) -> series","ta"),
        _spec("ta.rsi",1,2,"series<number>","ta.rsi(series, period) 또는 ta.rsi(period) -> series","ta"),
        _spec("ta.crossover",2,2,"series<bool>","ta.crossover(series_a, series_b) -> condition","ta"),
        _spec("ta.crossunder",2,2,"series<bool>","ta.crossunder(series_a, series_b) -> condition","ta"),
        _spec("ta.highest",2,3,"series<number>","ta.highest(series, period[, bars]) -> series","ta"),
        _spec("ta.lowest",2,3,"series<number>","ta.lowest(series, period[, bars]) -> series","ta"),
        _spec("ta.sum",1,3,"series<number>","ta.sum(series[, period, bars]) -> series","ta"),
        _spec("ta.stdev",2,3,"series<number>","ta.stdev(series, period[, bars]) -> series","ta"),
        _spec("ta.roc",2,2,"series<number>","ta.roc(series, period) -> series","ta"),
        _spec("ta.jma",3,4,"series<number>","ta.jma(series, length, phase, power) 또는 ta.jma(length, phase, power) -> trend_series","ta"),
        _spec("ta.supertrend",0,2,"series<number>","ta.supertrend([period, multiplier]) -> trend_series","ta"),
        _spec("ta.supertrend_direction",0,2,"series<number>","ta.supertrend_direction([period, multiplier]) -> direction_series","ta"),
        _spec("ta.macd",1,5,"series<number>","ta.macd(series, short, long[, signal, method]) -> series","ta"),
        _spec("ta.atr",0,1,"series<number>","ta.atr([period]) -> series","ta"),
        _spec("ta.adx",0,1,"series<number>","ta.adx([period]) -> series","ta"),
        _spec("ta.trix",0,1,"series<number>","ta.trix([period]) -> series","ta"),
        _spec("ta.cci",0,1,"series<number>","ta.cci([period]) -> series","ta"),
        _spec("ta.nrange",1,1,"series<number>","ta.nrange(period) -> series","ta"),
        _spec("ta.williams_r",1,1,"series<number>","ta.williams_r(period) -> series","ta"),
        _spec("ta.abs_range",1,1,"series<number>","ta.abs_range(period) -> series","ta"),
        _spec("ta.sum_abs_r",1,1,"series<number>","ta.sum_abs_r(period) -> series","ta"),
        _spec("ta.vhf",1,1,"series<number>","ta.vhf(period) -> series","ta"),
        _spec("ta.shift",2,2,"series<number>","ta.shift(series, bars) -> series","ta"),
        _spec("ta.count_since",2,2,"series<number>","ta.count_since(condition, reset) -> series","ta"),
        _spec("ta.bars_since",1,1,"series<number>","ta.bars_since(condition) -> series","ta"),
        _spec("ta.highest_since",2,2,"series<number>","ta.highest_since(condition, series) -> series","ta"),
        _spec("ta.lowest_since",2,2,"series<number>","ta.lowest_since(condition, series) -> series","ta"),
        _spec("ta.value_when",3,3,"series<number>","ta.value_when(occurrence, condition, series) -> series","ta"),
        _spec("logic.ifelse",3,3,"series<number>","logic.ifelse(condition, yes, no) -> scalar/series","logic"),
        *[_spec(name,1,1,"series<number>",f"{name}(number|series) -> number|series","math") for name in
          ("math.log","math.log10","math.abs","math.sqrt","math.sin","math.cos","math.tan","math.asin","math.acos","math.atan")],
        *[_spec(name,2,2,"series<number>",f"{name}(a, b) -> number|series","math") for name in ("math.pow","math.max","math.min")],
        *[_spec(name,0,0,"series<number>",f"{name}() -> series","session") for name in
          ("session.day_open","session.day_high","session.day_low","session.prev_open","session.prev_high","session.prev_low","session.prev_close")],
        _spec("state.edge",1,1,"series<bool>","state.edge(condition) -> condition","state"),
        _spec("state.falling_edge",1,1,"series<bool>","state.falling_edge(condition) -> condition","state"),
        _spec("state.ready_after",2,2,"series<bool>","state.ready_after(trigger, bars) -> condition","state"),
        _spec("state.hold",2,2,"series<bool>","state.hold(condition, bars) -> condition","state"),
        _spec("state.persist",2,2,"series<bool>","state.persist(condition, bars) -> condition","state"),
        _spec("state.latch",2,3,"series<bool>","state.latch(set, reset[, initial]) -> condition","state"),
        _spec("state.count",2,2,"series<number>","state.count(condition, reset) -> series","state"),
        _spec("state.regime",2,3,"series<number>","state.regime(bullish, bearish[, initial]) -> series","state"),
        *[_spec(name,1,1,"series<number>",f"{name}(timeframe) -> confirmed series","mtf") for name in
          ("mtf.open","mtf.high","mtf.low","mtf.close","mtf.volume")],
        _spec("mtf.sma",2,2,"series<number>","mtf.sma(timeframe, period) -> confirmed series","mtf"),
    ]
}


def specs_by_category(category: str):
    return [spec for spec in FUNCTION_SPECS.values() if spec.category == category]


def manifest_lines(category: str):
    return [spec.signature for spec in specs_by_category(category)]
