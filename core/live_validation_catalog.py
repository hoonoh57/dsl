"""Machine-readable examples for manual Core DSL verification in Live Studio.

This catalog is intentionally separate from Parser/Runtime semantics.  It only
provides user-facing example DSL programs that exercise already-registered Core
capabilities.  Each tranche adds a small, reviewable family and the examples
must execute through the real BacktestEngine before they are treated as trusted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class LiveValidationExample:
    id: str
    category: str
    title: str
    capability: str
    description: str
    expected_indicator: str
    dsl: str


_MOVING_AVERAGE_EXAMPLES: Tuple[LiveValidationExample, ...] = (
    LiveValidationExample(
        id="ta.sma.basic",
        category="TA / 이동평균",
        title="SMA 단순이동평균",
        capability="ta.sma",
        description="종가 5봉 단순이동평균을 계산하고 종가와의 상향/하향 교차로 주문 이벤트를 검증합니다.",
        expected_indicator="basis",
        dsl='''strategy "Verify_SMA" {
    timeframe = "1d"
    basis = ta.sma(close, 5)
    long_entry = ta.crossover(close, basis)
    long_exit = ta.crossunder(close, basis)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}''',
    ),
    LiveValidationExample(
        id="ta.ema.basic",
        category="TA / 이동평균",
        title="EMA 지수이동평균",
        capability="ta.ema",
        description="종가 8봉 지수이동평균을 계산하고 종가와의 교차가 실제 Core 실행 경로를 통과하는지 검증합니다.",
        expected_indicator="basis",
        dsl='''strategy "Verify_EMA" {
    timeframe = "1d"
    basis = ta.ema(close, 8)
    long_entry = ta.crossover(close, basis)
    long_exit = ta.crossunder(close, basis)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}''',
    ),
    LiveValidationExample(
        id="ta.wma.basic",
        category="TA / 이동평균",
        title="WMA 가중이동평균",
        capability="ta.wma",
        description="종가 10봉 가중이동평균의 계산·조건·주문 연결을 한 예제로 검증합니다.",
        expected_indicator="basis",
        dsl='''strategy "Verify_WMA" {
    timeframe = "1d"
    basis = ta.wma(close, 10)
    long_entry = ta.crossover(close, basis)
    long_exit = ta.crossunder(close, basis)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}''',
    ),
    LiveValidationExample(
        id="ta.rma.basic",
        category="TA / 이동평균",
        title="RMA Wilder 이동평균",
        capability="ta.rma",
        description="Wilder RMA가 DSL에서 계산되고 교차 조건 및 Core 주문 실행과 연결되는지 검증합니다.",
        expected_indicator="basis",
        dsl='''strategy "Verify_RMA" {
    timeframe = "1d"
    basis = ta.rma(close, 14)
    long_entry = ta.crossover(close, basis)
    long_exit = ta.crossunder(close, basis)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}''',
    ),
)


def live_validation_examples() -> Tuple[LiveValidationExample, ...]:
    """Return the currently registered manual-verification examples."""
    return _MOVING_AVERAGE_EXAMPLES


def live_validation_categories() -> Tuple[str, ...]:
    """Return categories in deterministic first-registration order."""
    return tuple(dict.fromkeys(item.category for item in live_validation_examples()))


def get_live_validation_example(example_id: str) -> LiveValidationExample:
    for item in live_validation_examples():
        if item.id == example_id:
            return item
    raise KeyError(example_id)
