"""Deterministic AXIS 1 batch/streaming parity certification helpers.

This Step 5-10 layer is additive.  It does not replace the migrated runtime or
backtest engine.  Instead it verifies causality by comparing one full batch run
with repeated prefix runs (the same data arriving one bar at a time), and it
provides one ordered event-tape session that can be consumed either all-at-once
or event-by-event.

The prefix method is intentionally correctness-first rather than performance-
first: every prefix is independently recompiled/replayed from authoritative
inputs.  That makes any future-data dependency, state drift, signal drift or
order/accounting drift observable without introducing a second calculation
kernel that could disagree for unrelated reasons.
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

    def public_dict(self) -> dict:
        return {
            "bars": self.bars,
            "prefixes_checked": self.prefixes_checked,
            "series_checked": self.series_checked,
            "event_count": self.event_count,
        }


@dataclass(frozen=True)
class BacktestParityReport:
    bars: int
    prefixes_checked: int
    trade_count: int
    closed_trade_count: int
    broker_history_count: int

    def public_dict(self) -> dict:
        return {
            "bars": self.bars,
            "prefixes_checked": self.prefixes_checked,
            "trade_count": self.trade_count,
            "closed_trade_count": self.closed_trade_count,
            "broker_history_count": self.broker_history_count,
        }


def _slice_value(value, size: int):
    if isinstance(value, np.ndarray):
        return value[:size].copy()
    if isinstance(value, list):
        return list(value[:size])
    if isinstance(value, tuple):
        return tuple(value[:size])
    if isinstance(value, dict):
        return dict(value)
    return value


def slice_market(market: Mapping[str, object], size: int) -> dict:
    """Return a prefix market without mutating the caller's fixture."""
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    if "close" not in market:
        raise ValueError("market.close is required")
    total = len(market["close"])
    if size > total:
        raise ValueError(f"prefix size exceeds market length: {size} > {total}")
    return {key: _slice_value(value, size) for key, value in market.items()}


def _numeric_array_equal(actual, expected) -> bool:
    left = np.asarray(actual)
    right = np.asarray(expected)
    if left.shape != right.shape:
        return False
    if left.dtype == bool or right.dtype == bool:
        return bool(np.array_equal(left, right))
    try:
        return bool(np.allclose(left.astype(float), right.astype(float), rtol=0.0, atol=0.0, equal_nan=True))
    except (TypeError, ValueError):
        return bool(np.array_equal(left, right))


def _assert_array_equal(actual, expected, label: str) -> None:
    if not _numeric_array_equal(actual, expected):
        raise FullEngineParityError(f"array parity mismatch: {label}", "ARRAY_PARITY_MISMATCH")

    actual_colors = getattr(actual, "trend_colors", None)
    expected_colors = getattr(expected, "trend_colors", None)
    if actual_colors is not None or expected_colors is not None:
        if actual_colors is None or expected_colors is None or not np.array_equal(actual_colors, expected_colors):
            raise FullEngineParityError(f"trend metadata parity mismatch: {label}", "TREND_METADATA_PARITY_MISMATCH")


def _assert_value_equal(actual, expected, label: str) -> None:
    if isinstance(expected, np.ndarray) or isinstance(actual, np.ndarray):
        _assert_array_equal(actual, expected, label)
        return
    if isinstance(expected, np.generic):
        expected = expected.item()
    if isinstance(actual, np.generic):
        actual = actual.item()
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            if np.isnan(expected) and np.isnan(actual):
                return
        except TypeError:
            pass
    if actual != expected:
        raise FullEngineParityError(
            f"value parity mismatch: {label}: {actual!r} != {expected!r}",
            "VALUE_PARITY_MISMATCH",
        )


def verify_runtime_prefix_parity(code: str, market: Mapping[str, object]) -> RuntimeParityReport:
    """Verify that full batch runtime output is identical at every causal prefix.

    A prefix compile represents the exact information that would have been
    available when that bar arrived.  Therefore comparing every prefix against
    the corresponding full-batch prefix detects future leakage as well as state,
    MTF, multi-output and event-condition drift.
    """
    total = len(market["close"])
    if total <= 0:
        raise ValueError("runtime parity requires at least one bar")

    full_market = {key: _slice_value(value, total) for key, value in market.items()}
    full = Axis1DSLRuntime.compile(code, full_market)
    series_names = tuple(
        sorted(
            name
            for name, value in full.values.items()
            if isinstance(value, np.ndarray) and len(value) == total
        )
    )

    for size in range(1, total + 1):
        prefix = Axis1DSLRuntime.compile(code, slice_market(market, size))
        for name in series_names:
            if name not in prefix.values:
                raise FullEngineParityError(f"stream prefix missing series: {name}", "STREAM_SERIES_MISSING")
            expected = full.values[name][:size]
            actual = prefix.values[name]
            _assert_array_equal(actual, expected, f"runtime:{name}:prefix={size}")

        for name, expected in full.values.items():
            if isinstance(expected, np.ndarray):
                continue
            if name in prefix.values:
                _assert_value_equal(prefix.values[name], expected, f"runtime-scalar:{name}:prefix={size}")

        if len(prefix.events) != len(full.events):
            raise FullEngineParityError(
                f"event count drift at prefix {size}: {len(prefix.events)} != {len(full.events)}",
                "EVENT_COUNT_PARITY_MISMATCH",
            )
        for event_index, (actual_event, expected_event) in enumerate(zip(prefix.events, full.events)):
            _assert_array_equal(
                actual_event.condition,
                expected_event.condition[:size],
                f"event[{event_index}].condition:prefix={size}",
            )
            if actual_event.commands != expected_event.commands:
                raise FullEngineParityError(
                    f"event command drift at prefix {size}, event {event_index}",
                    "EVENT_COMMAND_PARITY_MISMATCH",
                )
            for order_index, (actual_order, expected_order) in enumerate(zip(actual_event.orders, expected_event.orders)):
                if set(actual_order.arguments) != set(expected_order.arguments):
                    raise FullEngineParityError(
                        f"order argument keys drift at prefix {size}, event {event_index}, order {order_index}",
                        "ORDER_ARGUMENT_PARITY_MISMATCH",
                    )
                for key, expected_value in expected_order.arguments.items():
                    actual_value = actual_order.arguments[key]
                    if isinstance(expected_value, np.ndarray):
                        expected_value = expected_value[:size]
                    _assert_value_equal(
                        actual_value,
                        expected_value,
                        f"event[{event_index}].order[{order_index}].{key}:prefix={size}",
                    )

    return RuntimeParityReport(
        bars=total,
        prefixes_checked=total,
        series_checked=series_names,
        event_count=len(full.events),
    )


def _filter_rows_by_time(rows: Sequence[Mapping[str, object]], key: str, allowed_times: set[str]) -> list[dict]:
    result = []
    for row in rows:
        value = row.get(key)
        if value is not None and str(value) in allowed_times:
            result.append(dict(row))
    return result


def _open_position_from_trades(trades: Sequence[Mapping[str, object]]) -> int:
    position = 0
    for row in trades:
        if row.get("kind") == "ENTRY":
            side = str(row.get("side", "")).upper()
            position = 1 if side == "BUY" else -1
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
    """Compare batch backtest state with repeated one-more-bar prefix replay.

    The test intentionally compares equity, execution records, closed trades and
    broker lifecycle history.  Prefix fixtures should use GTC/market orders when
    lifecycle equality across artificial prefix ends is required; DAY expiration
    at an artificial prefix end is a different input condition by definition.
    """
    total = len(market["close"])
    if total < 2:
        raise ValueError("backtest parity requires at least two bars")

    kwargs = {
        "market": {key: _slice_value(value, total) for key, value in market.items()},
        "data_timeframe": data_timeframe,
        "settings": dict(settings or {}),
    }
    full = Axis1BacktestEngine.run(code, **kwargs)
    full_equity = [float(item["value"]) for item in full["equity_curve"]]
    all_times = [str(item) for item in market["time"]]

    for size in range(2, total + 1):
        prefix_market = slice_market(market, size)
        prefix = Axis1BacktestEngine.run(
            code,
            market=prefix_market,
            data_timeframe=data_timeframe,
            settings=dict(settings or {}),
        )
        prefix_equity = [float(item["value"]) for item in prefix["equity_curve"]]
        if not np.allclose(prefix_equity, full_equity[:size], rtol=0.0, atol=0.0, equal_nan=True):
            raise FullEngineParityError(f"equity parity mismatch at prefix {size}", "EQUITY_PARITY_MISMATCH")

        allowed = set(all_times[:size])
        expected_trades = _filter_rows_by_time(full["trades"], "time", allowed)
        if prefix["trades"] != expected_trades:
            raise FullEngineParityError(f"trade parity mismatch at prefix {size}", "TRADE_PARITY_MISMATCH")

        expected_closed = _filter_rows_by_time(full["closed_trades"], "exit_time", allowed)
        if prefix["closed_trades"] != expected_closed:
            raise FullEngineParityError(
                f"closed-trade parity mismatch at prefix {size}",
                "CLOSED_TRADE_PARITY_MISMATCH",
            )

        expected_history = _filter_rows_by_time(full["diagnostics"]["broker_history"], "event", allowed)
        if prefix["diagnostics"]["broker_history"] != expected_history:
            raise FullEngineParityError(
                f"broker lifecycle parity mismatch at prefix {size}",
                "BROKER_HISTORY_PARITY_MISMATCH",
            )

        expected_position = _open_position_from_trades(expected_trades)
        actual_position = int(prefix["metrics_numeric"]["open_position"])
        if actual_position != expected_position:
            raise FullEngineParityError(
                f"position parity mismatch at prefix {size}: {actual_position} != {expected_position}",
                "POSITION_PARITY_MISMATCH",
            )
        if int(prefix["metrics_numeric"]["closed_trade_count"]) != len(expected_closed):
            raise FullEngineParityError(
                f"closed trade count parity mismatch at prefix {size}",
                "CLOSED_TRADE_COUNT_PARITY_MISMATCH",
            )

    return BacktestParityReport(
        bars=total,
        prefixes_checked=total - 1,
        trade_count=len(full["trades"]),
        closed_trade_count=len(full["closed_trades"]),
        broker_history_count=len(full["diagnostics"]["broker_history"]),
    )


class Axis1EventTapeSession:
    """One ordered event authority consumable in batch or streaming form.

    Broker/accounting fills remain authoritative even when strategy intrabar
    state is later rolled back.  This preserves the Step 5-6/5-7 authority split.
    """

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
    def _optional_order_args(event: Mapping[str, object]) -> dict:
        allowed = (
            "type", "limit_price", "stop_price", "tif", "oco",
            "origin", "signal_time", "client_order_id", "event",
        )
        return {name: event[name] for name in allowed if name in event}

    def apply(self, event: Mapping[str, object]) -> dict:
        if not isinstance(event, Mapping):
            raise TypeError("event tape item must be a mapping")
        operation = str(event.get("op", "")).strip().upper()
        if not operation:
            raise ValueError("event tape item requires op")

        if operation == "BEGIN_BAR":
            value = self.intrabar.begin_bar(event["bar_id"])
            result = {"op": operation, "state": value}
        elif operation == "TICK":
            value = self.intrabar.on_tick(
                price=event["price"],
                volume=event.get("volume", 0.0),
                time=event.get("time"),
            )
            result = {"op": operation, "state": value}
        elif operation == "SUBMIT_ENTRY":
            order = self.execution.submit_entry(
                event["order_id"],
                event["side"],
                event["quantity"],
                **self._optional_order_args(event),
            )
            result = {"op": operation, "order": order.public_dict()}
        elif operation == "SUBMIT_EXIT":
            kwargs = self._optional_order_args(event)
            if "lot_id" in event:
                kwargs["lot_id"] = event["lot_id"]
            order = self.execution.submit_exit(
                event["order_id"],
                event.get("quantity"),
                **kwargs,
            )
            result = {"op": operation, "order": order.public_dict()}
        elif operation == "FILL":
            execution_result = self.execution.fill(
                event["order_id"],
                event["price"],
                event["quantity"],
                event=event.get("event", event.get("time")),
            )
            state = self.intrabar.on_fill(**self.execution.intrabar_fill_event(execution_result))
            result = {"op": operation, "execution": execution_result, "state": state}
        elif operation == "CANCEL":
            order = self.execution.cancel(
                event["order_id"],
                reason=str(event.get("reason", "user canceled")),
                event=event.get("event", event.get("time")),
            )
            result = {"op": operation, "order": order.public_dict()}
        elif operation == "COMMIT_BAR":
            result = {"op": operation, "state": self.intrabar.commit_bar()}
        elif operation == "ROLLBACK_BAR":
            result = {"op": operation, "state": self.intrabar.rollback_bar()}
        else:
            raise ValueError(f"unsupported event tape operation: {operation}")

        self.results.append(result)
        return result

    def run(self, tape: Sequence[Mapping[str, object]]) -> dict:
        for event in tape:
            self.apply(event)
        return self.snapshot()

    def snapshot(self) -> dict:
        provisional = self.intrabar.provisional_state() if self.intrabar.bar_open else None
        return {
            "intrabar": {
                "revision": self.intrabar.revision,
                "bar_open": self.intrabar.bar_open,
                "committed": self.intrabar.committed_state(),
                "provisional": provisional,
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
    """Verify grouped tape replay and one-event-at-a-time replay are identical."""

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
    stream_results = []
    for event in tape:
        stream_results.append(stream.apply(event))
    stream_snapshot = stream.snapshot()

    if batch.results != stream_results:
        raise FullEngineParityError("event result parity mismatch", "EVENT_RESULT_PARITY_MISMATCH")
    if batch_snapshot != stream_snapshot:
        raise FullEngineParityError("event tape final snapshot parity mismatch", "EVENT_TAPE_PARITY_MISMATCH")

    return {
        "events": len(tape),
        "final": batch_snapshot,
    }
