from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.core.user_functions import UserFunctionError, lower_user_functions
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
        "_meta": {"source": "user-function-test", "timeframe": "5m", "instrument": "TEST"},
    }


class Axis1UserFunctionTests(unittest.TestCase):
    def test_pure_function_with_local_scope_matches_direct_expression(self):
        code = '''strategy "UserFunction" {
    timeframe = "5m"
    function centered(source, period) {
        basis = ta.sma(source, period)
        return source - basis
    }
    centered_value = centered(close, 3)
    gate = centered_value > 0
    on(gate) { order.buy(type = "MARKET") }
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        expected = market["close"] - CoreTALib.sma(market["close"], 3)
        np.testing.assert_allclose(compiled.values["centered_value"], expected, equal_nan=True)
        self.assertEqual(compiled.user_function_definitions[0]["name"], "centered")
        self.assertEqual(compiled.user_function_definitions[0]["locals"], ("basis",))

    def test_user_functions_compose_without_runtime_registration(self):
        code = '''strategy "ComposedFunctions" {
    timeframe = "5m"
    function centered(source, period) {
        basis = ta.sma(source, period)
        return source - basis
    }
    function magnitude(source, period) {
        centered_value = centered(source, period)
        return math.abs(centered_value)
    }
    strength = magnitude(close, 3)
    gate = strength > 0
    on(gate) { order.buy(type = "MARKET") }
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        centered = market["close"] - CoreTALib.sma(market["close"], 3)
        np.testing.assert_allclose(compiled.values["strength"], np.abs(centered), equal_nan=True)
        self.assertEqual(tuple(item["name"] for item in compiled.user_function_definitions), ("centered", "magnitude"))

    def test_user_function_can_feed_existing_multi_output_lowering(self):
        code = '''strategy "FunctionIntoTuple" {
    timeframe = "5m"
    function scaled(source, factor) {
        return source * factor
    }
    upper, middle, lower = ta.bbands(scaled(close, 1), 4, 2)
    gate = close > middle
    on(gate) { order.buy(type = "MARKET") }
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        expected = CoreTALib.bbands(market["close"], 4, 2)
        for name, values in zip(("upper", "middle", "lower"), expected):
            np.testing.assert_allclose(compiled.values[name], values, equal_nan=True)
        self.assertEqual(compiled.multi_output_bindings[0]["function"], "ta.bbands")

    def test_backtest_facade_preserves_function_definition_diagnostics(self):
        code = '''strategy "FunctionBacktest" {
    timeframe = "5m"
    function above_average(source, period) {
        average = ta.sma(source, period)
        return source > average
    }
    enter = above_average(close, 3)
    exit = not enter
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''
        result = Axis1BacktestEngine.run(
            code,
            market=backtest_market(),
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
        )
        diagnostics = result["diagnostics"]["user_functions"]
        self.assertTrue(diagnostics["supplied"])
        self.assertEqual(diagnostics["definitions"][0]["name"], "above_average")
        self.assertTrue(result["strategy"]["name"], "FunctionBacktest")

    def test_fail_closed_for_invalid_function_contracts(self):
        cases = (
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x, x) {\n        return x\n    }\n}''', "DUPLICATE_USER_FUNCTION_PARAMETER"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x) {\n        local = x + 1\n    }\n}''', "MISSING_USER_FUNCTION_RETURN"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x) {\n        return f(x)\n    }\n}''', "RECURSIVE_USER_FUNCTION"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x) {\n        return x + close\n    }\n    value = f(1)\n}''', "USER_FUNCTION_FREE_VARIABLE"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x, y) {\n        return x + y\n    }\n    value = f(1)\n}''', "BAD_USER_FUNCTION_ARITY"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x) {\n        return x\n    }\n    value = f(x=1)\n}''', "USER_FUNCTION_KEYWORD_UNSUPPORTED"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    function f(x) {\n        if (x > 0) {\n            return x\n        }\n    }\n}''', "USER_FUNCTION_BLOCK_UNSUPPORTED"),
        )
        for source, error_code in cases:
            with self.subTest(error_code=error_code):
                with self.assertRaises(UserFunctionError) as ctx:
                    lower_user_functions(source)
                self.assertEqual(ctx.exception.code, error_code)

    def test_downstream_runtime_error_keeps_original_line_number(self):
        code = '''strategy "LineMap" {
    timeframe = "5m"
    function doubled(source) {
        return source * 2
    }
    bad = doubled("text")
}'''
        with self.assertRaises(DSLRuntimeError) as ctx:
            Axis1DSLRuntime.compile(code, runtime_market())
        self.assertIn("line 6", str(ctx.exception))

    def test_user_function_feature_layer_does_not_import_frozen_core(self):
        import axes.axis1_dsl.core.user_functions as functions
        import axes.axis1_dsl.runtime.axis1_runtime as runtime
        import axes.axis1_dsl.execution.axis1_backtest as backtest

        for module in (functions, runtime, backtest):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
