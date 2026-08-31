from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.core.bounded_loops import (
    INTERNAL_PREFIX,
    MAX_BOUNDED_LOOP_ITERATIONS,
    BoundedLoopError,
    lower_bounded_loops,
)
from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine
from axes.axis1_dsl.indicators.indicators import CoreTALib
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime
from axes.axis1_dsl.runtime.dsl_runtime import DSLRuntimeError


def runtime_market():
    close = np.asarray([100, 101, 103, 102, 105, 107, 106, 108, 111, 109, 112, 114], dtype=float)
    size = len(close)
    return {
        "open": close - 0.4,
        "high": close + 1.2,
        "low": close - 1.1,
        "close": close,
        "volume": np.arange(size, dtype=float) * 10.0 + 1000.0,
        "date": np.full(size, 20260831.0),
        "time": np.asarray([90000, 90500, 91000, 91500, 92000, 92500, 93000, 93500, 94000, 94500, 95000, 95500], dtype=float),
    }


def backtest_market():
    market = runtime_market()
    return {
        "time": [
            "20260831090000", "20260831090500", "20260831091000", "20260831091500",
            "20260831092000", "20260831092500", "20260831093000", "20260831093500",
            "20260831094000", "20260831094500", "20260831095000", "20260831095500",
        ],
        "open": market["open"],
        "high": market["high"],
        "low": market["low"],
        "close": market["close"],
        "volume": market["volume"],
        "_meta": {"source": "bounded-loop-test", "timeframe": "5m", "instrument": "TEST"},
    }


class Axis1BoundedLoopTests(unittest.TestCase):
    def test_compile_time_loop_matches_manual_history_expression(self):
        code = '''strategy "BoundedMean" {
    timeframe = "5m"
    function mean3(source) {
        total = 0
        for i in range(0, 3) {
            total = total + source[i]
        }
        return total / 3
    }
    average = mean3(close)
    gate = close > average
    on(gate) { order.buy(type = "MARKET") }
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        expected = (
            market["close"]
            + CoreTALib.shift(market["close"], 1)
            + CoreTALib.shift(market["close"], 2)
        ) / 3.0
        np.testing.assert_allclose(compiled.values["average"], expected, equal_nan=True)
        self.assertEqual(len(compiled.bounded_loop_definitions), 1)
        loop = compiled.bounded_loop_definitions[0]
        self.assertEqual(loop["iterations"], 3)
        self.assertEqual(loop["targets"], ("total",))
        self.assertFalse(loop["runtime_loop"])

    def test_step_range_and_multiple_accumulators_are_deterministic(self):
        code = '''strategy "WeightedLoop" {
    timeframe = "5m"
    function weighted(source) {
        total = 0
        weights = 0
        for i in range(1, 6, 2) {
            total = total + source[i] * i
            weights = weights + i
        }
        return total / weights
    }
    value = weighted(close)
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        expected = (
            CoreTALib.shift(market["close"], 1) * 1
            + CoreTALib.shift(market["close"], 3) * 3
            + CoreTALib.shift(market["close"], 5) * 5
        ) / 9.0
        np.testing.assert_allclose(compiled.values["value"], expected, equal_nan=True)
        loop = compiled.bounded_loop_definitions[0]
        self.assertEqual((loop["start"], loop["stop"], loop["step"]), (1, 6, 2))
        self.assertEqual(loop["targets"], ("total", "weights"))

    def test_loop_function_can_feed_existing_multi_output_lowering(self):
        code = '''strategy "LoopIntoTuple" {
    timeframe = "5m"
    function mean3(source) {
        total = 0
        for i in range(0, 3) {
            total = total + source[i]
        }
        return total / 3
    }
    upper, middle, lower = ta.bbands(mean3(close), 4, 2)
    gate = close > middle
    on(gate) { order.buy(type = "MARKET") }
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        mean3 = (
            market["close"]
            + CoreTALib.shift(market["close"], 1)
            + CoreTALib.shift(market["close"], 2)
        ) / 3.0
        expected = CoreTALib.bbands(mean3, 4, 2)
        for name, values in zip(("upper", "middle", "lower"), expected):
            np.testing.assert_allclose(compiled.values[name], values, equal_nan=True)
        self.assertEqual(compiled.multi_output_bindings[0]["function"], "ta.bbands")

    def test_backtest_preserves_loop_diagnostics_without_internal_series(self):
        code = '''strategy "LoopBacktest" {
    timeframe = "5m"
    function mean3(source) {
        total = 0
        for i in range(0, 3) {
            total = total + source[i]
        }
        return total / 3
    }
    average = mean3(close)
    enter = ta.crossover(close, average)
    exit = ta.crossunder(close, average)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''
        result = Axis1BacktestEngine.run(
            code,
            market=backtest_market(),
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
        )
        diagnostics = result["diagnostics"]["bounded_loops"]
        self.assertTrue(diagnostics["supplied"])
        self.assertEqual(diagnostics["loops"][0]["iterations"], 3)
        self.assertFalse(any(INTERNAL_PREFIX in item["name"] for item in result["indicators"]))

    def test_fail_closed_for_unbounded_or_unsafe_loop_contracts(self):
        limit = MAX_BOUNDED_LOOP_ITERATIONS + 1
        cases = (
            (f'''strategy "Bad" {{\n    timeframe = "5m"\n    function f(source) {{\n        total = 0\n        for i in range(0, {limit}) {{\n            total = total + source[i]\n        }}\n        return total\n    }}\n}}''', "LOOP_ITERATION_LIMIT"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(source, period) {\n        total = 0\n        for i in range(0, period) {\n            total = total + source[i]\n        }\n        return total\n    }\n}''', "LOOP_BOUND_LITERAL_REQUIRED"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(source) {\n        total = 0\n        for i in range(0, 3, 0) {\n            total = total + source[i]\n        }\n        return total\n    }\n}''', "LOOP_ZERO_STEP"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    total = 0\n    for i in range(0, 3) {\n        total = total + close[i]\n    }\n}''', "LOOP_SCOPE_UNSUPPORTED"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(source) {\n        total = 0\n        for i in range(0, 3) {\n            source = source[i]\n        }\n        return total\n    }\n}''', "LOOP_TARGET_MUST_BE_LOCAL"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(source) {\n        total = 0\n        for i in range(0, 3) {\n            for j in range(0, 2) {\n                total = total + source[i + j]\n            }\n        }\n        return total\n    }\n}''', "NESTED_LOOP_UNSUPPORTED"),
        )
        for source, error_code in cases:
            with self.subTest(error_code=error_code):
                with self.assertRaises(BoundedLoopError) as ctx:
                    lower_bounded_loops(source)
                self.assertEqual(ctx.exception.code, error_code)

    def test_source_line_count_and_downstream_error_line_are_preserved(self):
        code = '''strategy "LoopLine" {
    timeframe = "5m"
    function mean2(source) {
        total = 0
        for i in range(0, 2) {
            total = total + source[i]
        }
        return total / 2
    }
    bad = mean2("text")
}'''
        lowered = lower_bounded_loops(code)
        self.assertEqual(len(lowered.source.splitlines()), len(code.splitlines()))
        with self.assertRaises(DSLRuntimeError) as ctx:
            Axis1DSLRuntime.compile(code, runtime_market())
        self.assertIn("line 10", str(ctx.exception))

    def test_bounded_loop_layer_does_not_import_frozen_core(self):
        import axes.axis1_dsl.core.bounded_loops as loops
        import axes.axis1_dsl.runtime.axis1_runtime as runtime
        import axes.axis1_dsl.execution.axis1_backtest as backtest

        for module in (loops, runtime, backtest):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
