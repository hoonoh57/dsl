"""Correctness-first AXIS 1 batch/streaming parity certification helpers.

This Step 5-10 layer is additive. A full batch result is compared with repeated
causal prefixes (the information available when each bar arrived). Intrabar and
execution events are also exposed through one ordered tape that can be consumed
as a batch or one event at a time. No frozen-core dependency is introduced.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine
from axes.axis1_dsl.execution.pyramiding_execution import PyramidingExecutionSession
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime


class FullEngineParityError(AssertionError):
    def __init__(self, message: str, code: str = "FULL_ENGINE_PARITY_ERROR"):
        self.code = str(code)
        super().__init__(message)


@dataclass(frozen=True)
class RuntimeParityReport:
    bars: int
    prefixes_checked: int
    series_checked: tuple[str, ...]
    event_count: int


@dataclass(frozen=True)
class BacktestParityReport:
    bars: int
    prefixes_checked: int
    trade_count: int
    closed_trade_count: int
    broker_history_count: int


def _slice_value(value, size: int):
    if isinstance(value, np.ndarray):
        return np.asarray(value)[:size].copy()
    if isinstance(value, list):
        return list(value[:size])
    if isinstance(value, tuple):
        return tuple(value[:size])
    if isinstance(value, dict):
        return dict(value)
    return value


def slice_market(market: Mapping[str, object], size: int) -> dict:
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    if "close" not in market:
        raise ValueError("market.close is required")
    total = len(market["close"])
    if size > total:
        raise ValueError(f"prefix size exceeds market length: {size} > {total}")
    return {key: _slice_value(value, size) for key, value in market.items()}


def _arrays_equal(actual, expected) -> bool:
    left, right = np.asarray(actual), np.asarray(expected)
    if left.shape != right.shape:
        return False
    if left.dtype == bool or right.dtype == bool:
        return bool(np.array_equal(left, right))
    try:
        return bool(np.allclose(left.astype(float), right.astype(float), rtol=0.0, atol=0.0, equal_nan=True))
    except (TypeError, ValueError):
        return bool(np.array_equal(left, right))


def _assert_array_equal(actual, expected, label: str, *, expected_colors=None) -> None:
    if not _arrays_equal(actual, expected):
        raise FullEngineParityError(f"array parity mismatch: {label}", "ARRAY_PARITY_MISMATCH")

    actual_colors = getattr(actual, "trend_colors", None)
    if expected_colors is None:
        expected_colors = getattr(expected, "trend_colors", None)
    if actual_colors is None and expected_colors is None:
        return
    if actual_colors is None or expected_colors is None:
        raise FullEngineParityError(f"trend metadata missing: {label}", "TREND_METADATA_PARITY_MISMATCH")
    count = len(np.asarray(actual))
    if not np.array_equal(np.asarray(actual_colors)[:count], np.asarray(expected_colors)[:count]):
        raise FullEngineParityError(f"trend metadata parity mismatch: {label}", "TREND_METADATA_PARITY_MISMATCH")


def _assert_value_equal(actual, expected, label: str) -> None:
    if isinstance(actual, np.ndarray) or isinstance(expected, np.ndarray):
        _assert_array_equal(actual, expected, label)
        return
    if isinstance(actual, np.generic):
        actual = actual.item()
    if isinstance(expected, np.generic):
        expected = expected.item()
    try:
        if np.isnan(actual) and np.isnan(expected):
            return
    except TypeError:
        pass
    if actual != expected:
        raise FullEngineParityError(
            f"value parity mismatch: {label}: {actual!r} != {expected!r}",
            "VALUE_PARITY_MISMATCH",
        )


def verify_runtime_prefix_parity(code: str, market: Mapping[str, object]) -> RuntimeParityReport:
    """Compare every streamed prefix with the corresponding full-batch prefix."""
    total = len(market["close"])
    if total <= 0:
        raise ValueError("runtime parity requires at least one bar")
    full = Axis1DSLRuntime.compile(code, slice_market(market, total))
    series_names = tuple(sorted(
        name for name, value in full.values.items()
        if isinstance(value, np.ndarray) and len(value) == total
    ))

    for size in range(1, total + 1):
        prefix = Axis1DSLRuntime.compile(code, slice_market(market, size))
        for name in series_names:
            if name not in prefix.values:
                raise FullEngineParityError(f"stream prefix missing series: {name}", "STREAM_SERIES_MISSING")
            full_value = full.values[name]
            expected = np.asarray(full_value)[:size]
            expected_colors = getattr(full_value, "trend_colors", None)
            if expected_colors is not None:
                expected_colors = np.asarray(expected_colors)[:size]
            _assert_array_equal(
                prefix.values[name], expected,
                f"runtime:{name}:prefix={size}",
                expected_colors=expected_colors,
            )

        for name, expected in full.values.items():
            if isinstance(expected, np.ndarray):
                continue
            if name in prefix.values:
                _assert_value_equal(prefix.values[name], expected, f"runtime-scalar:{name}:prefix={size}")

        if len(prefix.events) != len(full.events):
            raise FullEngineParityError(f"event count drift at prefix {size}", "EVENT_COUNT_PARITY_MISMATCH")
        for event_index, (actual_event, expected_event) in enumerate(zip(prefix.events, full.events)):
            _assert_array_equal(
                actual_event.condition,
                np.asarray(expected_event.condition)[:size],
                f"event[{event_index}].condition:prefix={size}",
            )
            if actual_event.commands != expected_event.commands:
                raise FullEngineParityError(
                    f"event command drift at prefix {size}, event {event_index}",
                    "EVENT_COMMAND_PARITY_MISMATCH",
                )
            for order_index, (actual_order, expected_order) in enumerate(zip(actual_event.orders, expected_event.orders)):
                if set(actual_order.arguments) != set(expected_order.arguments):
                    raise FullEngineParityError("order argument key drift", "ORDER_ARGUMENT_PARITY_MISMATCH")
                for key, expected_value in expected_order.arguments.items():
                    if isinstance(expected_value, np.ndarray):
                        expected_value = np.asarray(expected_value)[:size]
                    _assert_value_equal(
                        actual_order.arguments[key], expected_value,
                        f"event[{event_index}].order[{order_index}].{key}:prefix={size}",
                    )

    return RuntimeParityReport(total, total, series_names, len(full.events))


def _filter_rows(rows: Sequence[Mapping[str, object]], key: str, allowed: set[str]) -> list[dict]:
    return [dict(row) for row in rows if row.get(key) is not None and str(row.get(key)) in allowed]


def _position_from_trades(trades: Sequence[Mapping[str, object]]) -> int:
    position = 0
    for row in trades:
        if row.get("kind") == "ENTRY":
            position = 1 if str(row.get("side", "")).upper() == "BUY" else -1
        elif row.get("kind") == "EXIT":
            position = 0
    return position


def verify_backtest_prefix_parity(
    code: str,
    market: Mapping[str, object],
    *,
    data_timeframe: str,
    settings: Mapping[str, object] | None = None,
) -> BacktestParityReport:
    """Compare equity, executions, closed trades and broker lifecycle per prefix.

    GTC/market fixtures are used for prefix certification because an artificial
    prefix end is not an authoritative DAY-session boundary.
    """
    total = len(market["close"])
    if total < 2:
        raise ValueError("backtest parity requires at least two bars")
    config = dict(settings or {})
    full = Axis1BacktestEngine.run(
        code, market=slice_market(market, total), data_timeframe=data_timeframe, settings=config,
    )
    full_equity = [float(item["value"]) for item in full["equity_curve"]]
    times = [str(item) for item in market["time"]]

    for size in range(2, total + 1):
        prefix = Axis1BacktestEngine.run(
            code, market=slice_market(market, size), data_timeframe=data_timeframe, settings=config,
        )
        actual_equity = [float(item["value"]) for item in prefix["equity_curve"]]
        if not np.allclose(actual_equity, full_equity[:size], rtol=0.0, atol=0.0, equal_nan=True):
            raise FullEngineParityError(f"equity parity mismatch at prefix {size}", "EQUITY_PARITY_MISMATCH")

        allowed = set(times[:size])
        expected_trades = _filter_rows(full["trades"], "time", allowed)
        expected_closed = _filter_rows(full["closed_trades"], "exit_time", allowed)
        expected_history = _filter_rows(full["diagnostics"]["broker_history"], "event", allowed)
        if prefix["trades"] != expected_trades:
            raise FullEngineParityError(f"trade parity mismatch at prefix {size}", "TRADE_PARITY_MISMATCH")
        if prefix["closed_trades"] != expected_closed:
            raise FullEngineParityError(f"closed-trade parity mismatch at prefix {size}", "CLOSED_TRADE_PARITY_MISMATCH")
        if prefix["diagnostics"]["broker_history"] != expected_history:
            raise FullEngineParityError(f"broker lifecycle parity mismatch at prefix {size}", "BROKER_HISTORY_PARITY_MISMATCH")
        if int(prefix["metrics_numeric"]["open_position"]) != _position_from_trades(expected_trades):
            raise FullEngineParityError(f"position parity mismatch at prefix {size}", "POSITION_PARITY_MISMATCH")
        if int(prefix["metrics_numeric"]["closed_trade_count"]) != len(expected_closed):
            raise FullEngineParityError(
                f"closed trade count parity mismatch at prefix {size}",
                "CLOSED_TRADE_COUNT_PARITY_MISMATCH",
            )

    return BacktestParityReport(
        total, total - 1, len(full["trades"]), len(full["closed_trades"]),
        len(full["diagnostics"]["broker_history"]),
    )


class Axis1EventTapeSession:
    """Ordered intrabar + partial/pyramiding execution tape authority."""
    def __init__(
        self,
        compiled,
        *,
        initial_state: Mapping[str, object] | None = None,
        initial_cash: float = 0.0,
        commission_pct: float = 0.0,
        sell_tax_pct: float = 0.0,
        max_lots: int = 4,
    ):
        self.intrabar = Axis1DSLRuntime.open_intrabar_session(compiled, initial_state=initial_state)
        self.execution = PyramidingExecutionSession(
            initial_cash=initial_cash,
            commission_pct=commission_pct,
            sell_tax_pct=sell_tax_pct,
            max_lots=max_lots,
        )
        self.results: list[dict] = []

    @staticmethod
    def _order_kwargs(event: Mapping[str, object]) -> dict:
        names = ("type", "limit_price", "stop_price", "tif", "oco", "origin", "signal_time", "client_order_id", "event")
        return {name: event[name] for name in names if name in event}

    def apply(self, event: Mapping[str, object]) -> dict:
        if not isinstance(event, Mapping):
            raise TypeError("event tape item must be a mapping")
        op = str(event.get("op", "")).strip().upper()
        if not op:
            raise ValueError("event tape item requires op")

        if op == "BEGIN_BAR":
            result = {"op": op, "state": self.intrabar.begin_bar(event["bar_id"])}
        elif op == "TICK":
            result = {"op": op, "state": self.intrabar.on_tick(
                price=event["price"], volume=event.get("volume", 0.0), time=event.get("time"),
            )}
        elif op == "SUBMIT_ENTRY":
            order = self.execution.submit_entry(
                event["order_id"], event["side"], event["quantity"], **self._order_kwargs(event),
            )
            result = {"op": op, "order": order.public_dict()}
        elif op == "SUBMIT_EXIT":
            kwargs = self._order_kwargs(event)
            if "lot_id" in event:
                kwargs["lot_id"] = event["lot_id"]
            order = self.execution.submit_exit(event["order_id"], event.get("quantity"), **kwargs)
            result = {"op": op, "order": order.public_dict()}
        elif op == "FILL":
            execution_result = self.execution.fill(
                event["order_id"], event["price"], event["quantity"],
                event=event.get("event", event.get("time")),
            )
            # Exchange/accounting fact is authoritative. If the handler rejects,
            # its provisional strategy state rolls back but the fill is retained.
            state = self.intrabar.on_fill(**self.execution.intrabar_fill_event(execution_result))
            result = {"op": op, "execution": execution_result, "state": state}
        elif op == "CANCEL":
            order = self.execution.cancel(
                event["order_id"], reason=str(event.get("reason", "user canceled")),
                event=event.get("event", event.get("time")),
            )
            result = {"op": op, "order": order.public_dict()}
        elif op == "COMMIT_BAR":
            result = {"op": op, "state": self.intrabar.commit_bar()}
        elif op == "ROLLBACK_BAR":
            result = {"op": op, "state": self.intrabar.rollback_bar()}
        else:
            raise ValueError(f"unsupported event tape operation: {op}")

        self.results.append(result)
        return result

    def run(self, tape: Sequence[Mapping[str, object]]) -> dict:
        for event in tape:
            self.apply(event)
        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "intrabar": {
                "revision": self.intrabar.revision,
                "bar_open": self.intrabar.bar_open,
                "committed": self.intrabar.committed_state(),
                "provisional": self.intrabar.provisional_state() if self.intrabar.bar_open else None,
                "audit": tuple(dict(item) for item in self.intrabar.audit),
            },
            "execution": self.execution.snapshot(),
            "result_count": len(self.results),
        }


def verify_event_tape_batch_stream_parity(
    compiled,
    tape: Sequence[Mapping[str, object]],
    *,
    initial_state: Mapping[str, object] | None = None,
    initial_cash: float = 0.0,
    commission_pct: float = 0.0,
    sell_tax_pct: float = 0.0,
    max_lots: int = 4,
) -> dict:
    """Compare grouped replay with one-event-at-a-time replay exactly."""
    def make_session():
        return Axis1EventTapeSession(
            compiled,
            initial_state=initial_state,
            initial_cash=initial_cash,
            commission_pct=commission_pct,
            sell_tax_pct=sell_tax_pct,
            max_lots=max_lots,
        )

    batch = make_session()
    batch_snapshot = batch.run(tape)
    stream = make_session()
    stream_results = [stream.apply(event) for event in tape]
    stream_snapshot = stream.snapshot()

    if batch.results != stream_results:
        raise FullEngineParityError("event result parity mismatch", "EVENT_RESULT_PARITY_MISMATCH")
    if batch_snapshot != stream_snapshot:
        raise FullEngineParityError("event tape final snapshot parity mismatch", "EVENT_TAPE_PARITY_MISMATCH")
    return {"events": len(tape), "final": batch_snapshot}
