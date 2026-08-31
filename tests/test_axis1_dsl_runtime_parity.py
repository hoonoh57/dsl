from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from core import dsl_runtime as legacy
from core.dsl_context import DSLContextSeriesBinding as LegacyContextBinding
from axes.axis1_dsl.runtime import dsl_runtime as axis1
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding as Axis1ContextBinding


def market_fixture():
    close = np.asarray([100, 101, 102, 103, 102, 104, 105, 106, 104, 107, 108, 109], dtype=float)
    return {
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": np.asarray([10, 12, 11, 13, 12, 14, 15, 13, 16, 15, 17, 18], dtype=float),
        "date": np.asarray([20260831] * len(close), dtype=float),
        "time": np.asarray([90000, 90500, 91000, 91500, 92000, 92500, 93000, 93500, 94000, 94500, 95000, 95500], dtype=float),
    }


def assert_value_equal(testcase, actual, expected, label):
    if isinstance(expected, np.ndarray):
        testcase.assertIsInstance(actual, np.ndarray, label)
        if expected.dtype == bool:
            np.testing.assert_array_equal(actual, expected, err_msg=label)
        else:
            np.testing.assert_allclose(actual, expected, equal_nan=True, err_msg=label)
    else:
        testcase.assertEqual(actual, expected, label)


class Axis1DSLRuntimeParityTests(unittest.TestCase):
    def test_compile_values_state_mtf_and_orders_match_legacy(self):
        code = '''strategy "RuntimeParity" {
            timeframe = "5m"
            input fast = 3
            sma = ta.sma(close, fast)
            dayret = session.day_return_pct()
            higher = mtf.close("15m")
            cross = ta.crossover(close, sma)
            state armed = false
            on_bar {
                if (cross) {
                    set armed = true
                }
                else {
                    if (close < sma) {
                        set armed = false
                    }
                }
            }
            enter = armed and close > sma
            on(enter) { order.buy(type = "MARKET", id = "entry") }
        }'''
        market = market_fixture()
        expected = legacy.DSLRuntime.compile(code, {k: v.copy() for k, v in market.items()})
        actual = axis1.DSLRuntime.compile(code, {k: v.copy() for k, v in market.items()})

        self.assertEqual(actual.name, expected.name)
        self.assertEqual(actual.timeframe, expected.timeframe)
        self.assertEqual(set(actual.values), set(expected.values))
        for name in expected.values:
            assert_value_equal(self, actual.values[name], expected.values[name], name)

        self.assertEqual(len(actual.events), len(expected.events))
        for got, want in zip(actual.events, expected.events):
            np.testing.assert_array_equal(got.condition, want.condition)
            self.assertEqual(got.commands, want.commands)
            self.assertEqual(got.line, want.line)
            self.assertEqual(len(got.orders), len(want.orders))
            for got_order, want_order in zip(got.orders, want.orders):
                self.assertEqual(got_order.command, want_order.command)
                self.assertEqual(set(got_order.arguments), set(want_order.arguments))
                for key in want_order.arguments:
                    assert_value_equal(self, got_order.arguments[key], want_order.arguments[key], key)

    def test_indicator_and_state_function_results_match_legacy(self):
        code = '''strategy "FunctionParity" {
            timeframe = "5m"
            j = ta.jma(close, 5, 0, 2)
            hist = user.macd_normalized(close, "hist_abs_pct", 3, 6, 3, "exponential")
            up = close > open
            held = state.hold(up, 2)
            ready = state.ready_after(not up, 1)
            signal = held and ready and j > j[1]
            on(signal) { order.buy(type = "MARKET") }
        }'''
        market = market_fixture()
        expected = legacy.DSLRuntime.compile(code, {k: v.copy() for k, v in market.items()})
        actual = axis1.DSLRuntime.compile(code, {k: v.copy() for k, v in market.items()})
        for name in ("j", "hist", "held", "ready", "signal"):
            assert_value_equal(self, actual.values[name], expected.values[name], name)
        np.testing.assert_array_equal(actual.events[0].condition, expected.events[0].condition)

    def test_prepared_context_compile_matches_legacy(self):
        market = market_fixture()
        target_times = tuple(f"20260831{int(clock):06d}" for clock in market["time"])
        fields = dict(
            target_symbol="TEST",
            target_times=target_times,
            frame_hash="frame-hash",
            registry_hash="registry-hash",
            feature_types={"market.regime": "NUMBER", "market.permission": "BOOLEAN"},
            feature_values={
                "market.regime": tuple(float(i % 3 - 1) for i in range(len(target_times))),
                "market.permission": tuple(i % 2 == 0 for i in range(len(target_times))),
            },
        )
        legacy_binding = LegacyContextBinding(**fields)
        axis1_binding = Axis1ContextBinding.from_prepared(**fields)
        code = '''strategy "ContextParity" {
            timeframe = "5m"
            gate = ctx.market.permission and ctx.market.regime >= 0
            on(gate) { order.buy(type = "MARKET") }
        }'''
        expected = legacy.DSLRuntime.compile(
            code,
            {k: v.copy() for k, v in market.items()},
            context_binding=legacy_binding,
            target_times=target_times,
        )
        actual = axis1.DSLRuntime.compile(
            code,
            {k: v.copy() for k, v in market.items()},
            context_binding=axis1_binding,
            target_times=target_times,
        )
        np.testing.assert_array_equal(actual.values["gate"], expected.values["gate"])
        np.testing.assert_array_equal(actual.events[0].condition, expected.events[0].condition)
        self.assertEqual(actual.context_binding_hash, expected.context_binding_hash)

    def test_runtime_fail_closed_error_matches_legacy(self):
        code = '''strategy "BadRuntime" {
            timeframe = "5m"
            input p = 0
            bad = ta.sma(close, p)
            enter = close > bad
            on(enter) { order.buy(type = "MARKET") }
        }'''
        market = market_fixture()
        with self.assertRaises(legacy.DSLRuntimeError) as legacy_ctx:
            legacy.DSLRuntime.compile(code, {k: v.copy() for k, v in market.items()})
        with self.assertRaises(axis1.DSLRuntimeError) as axis1_ctx:
            axis1.DSLRuntime.compile(code, {k: v.copy() for k, v in market.items()})
        self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_axis1_runtime_has_no_frozen_core_runtime_import(self):
        source = Path(axis1.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
