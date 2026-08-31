from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.core.multi_output import (
    MULTI_OUTPUT_SPECS,
    MultiOutputError,
    lower_multi_output,
    multi_output_manifest,
)
from axes.axis1_dsl.indicators.indicators import CoreTALib
from axes.axis1_dsl.indicators.user_indicators import normalized_macd_component
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime
from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine


def market_fixture(size=48):
    index = np.arange(size, dtype=float)
    close = 100.0 + np.sin(index / 3.0) * 4.0 + index * 0.15
    return {
        "open": close - 0.4,
        "high": close + 1.2,
        "low": close - 1.1,
        "close": close,
        "volume": 1000.0 + index * 10.0,
        "date": np.full(size, 20260831.0),
        "time": 90000.0 + index * 500.0,
    }


def backtest_market(size=48):
    values = market_fixture(size)
    base = datetime(2026, 8, 31, 9, 0, 0)
    times = [(base + timedelta(minutes=5 * i)).strftime("%Y%m%d%H%M%S") for i in range(size)]
    return {
        "time": times,
        "open": values["open"],
        "high": values["high"],
        "low": values["low"],
        "close": values["close"],
        "volume": values["volume"],
        "_meta": {"source": "multi-output-test", "timeframe": "5m", "instrument": "TEST"},
    }


class Axis1MultiOutputTests(unittest.TestCase):
    def test_registered_contract_is_typed_and_explicit(self):
        manifest = {item["name"]: item for item in multi_output_manifest()}
        self.assertEqual(set(manifest), {"ta.supertrend", "ta.bbands", "user.macd_normalized_all"})
        self.assertEqual(manifest["ta.supertrend"]["components"], ("line", "direction"))
        self.assertEqual(manifest["ta.bbands"]["component_types"], ("series<number>",) * 3)
        self.assertEqual(manifest["user.macd_normalized_all"]["component_types"], ("series<number>",) * 4)
        for spec in MULTI_OUTPUT_SPECS.values():
            spec.validate()

    def test_supertrend_destructuring_matches_kernel_components(self):
        code = '''strategy "SupertrendTuple" {
            timeframe = "5m"
            st, direction = ta.supertrend(5, 2.0)
            gate = direction > 0 and close > st
            on(gate) { order.buy(type = "MARKET") }
        }'''
        market = market_fixture()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        expected_line, expected_direction = CoreTALib.supertrend(
            market["high"], market["low"], market["close"], 5, 2.0
        )
        np.testing.assert_allclose(compiled.values["st"], expected_line, equal_nan=True)
        np.testing.assert_array_equal(compiled.values["direction"], expected_direction)
        self.assertEqual(compiled.multi_output_bindings[0]["targets"], ("st", "direction"))

    def test_bbands_destructuring_matches_kernel(self):
        code = '''strategy "BandsTuple" {
            timeframe = "5m"
            upper, middle, lower = ta.bbands(close, 8, 2.5)
            wide = upper - lower
            gate = close > middle
            on(gate) { order.buy(type = "MARKET") }
        }'''
        market = market_fixture()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        expected = CoreTALib.bbands(market["close"], 8, 2.5)
        for name, values in zip(("upper", "middle", "lower"), expected):
            np.testing.assert_allclose(compiled.values[name], values, equal_nan=True)
        np.testing.assert_allclose(
            compiled.values["wide"], expected[0] - expected[2], equal_nan=True
        )

    def test_normalized_macd_multi_output_matches_registered_components(self):
        code = '''strategy "MacdTuple" {
            timeframe = "5m"
            macd, signal, hist, strength = user.macd_normalized_all(close, 5, 12, 4, "exponential")
            gate = hist > 0 and strength > 0
            on(gate) { order.buy(type = "MARKET") }
        }'''
        market = market_fixture()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        for target, component in (
            ("macd", "macd"),
            ("signal", "signal"),
            ("hist", "hist"),
            ("strength", "hist_abs_pct"),
        ):
            expected = normalized_macd_component(
                market["close"], component, 5, 12, 4, "exponential"
            )
            np.testing.assert_allclose(compiled.values[target], expected, equal_nan=True)

    def test_fail_closed_for_bad_destructuring_contracts(self):
        bad_sources = (
            ('''strategy "Bad" {\n    timeframe = "5m"\n    a, b, c = ta.supertrend(5, 2)\n}''', "BAD_DESTRUCTURING_ARITY"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    a, a = ta.supertrend(5, 2)\n}''', "DUPLICATE_MULTI_OUTPUT_TARGET"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    a, b = ta.unknown(close)\n}''', "UNREGISTERED_MULTI_OUTPUT_FUNCTION"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    close, b = ta.supertrend(5, 2)\n}''', "RESERVED_MULTI_OUTPUT_TARGET"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    a, b = ta.supertrend(period=5, multiplier=2)\n}''', "MULTI_OUTPUT_KEYWORD_UNSUPPORTED"),
        )
        for source, code in bad_sources:
            with self.subTest(code=code):
                with self.assertRaises(MultiOutputError) as ctx:
                    lower_multi_output(source)
                self.assertEqual(ctx.exception.code, code)

    def test_backtest_facade_consumes_destructuring_and_preserves_metadata(self):
        code = '''strategy "TupleBacktest" {
            timeframe = "5m"
            upper, middle, lower = ta.bbands(close, 8, 2)
            enter = ta.crossover(close, middle)
            exit = ta.crossunder(close, middle)
            on(enter) { order.buy(type = "MARKET") }
            on(exit) { order.close_long() }
        }'''
        result = Axis1BacktestEngine.run(
            code,
            market=backtest_market(),
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
        )
        self.assertTrue(result["diagnostics"]["multi_output"]["supplied"])
        binding = result["diagnostics"]["multi_output"]["bindings"][0]
        self.assertEqual(binding["targets"], ("upper", "middle", "lower"))
        names = {item["name"] for item in result["indicators"]}
        self.assertTrue({"upper", "middle", "lower"}.issubset(names))

    def test_additive_feature_modules_do_not_import_frozen_core(self):
        import axes.axis1_dsl.core.multi_output as multi
        import axes.axis1_dsl.runtime.axis1_runtime as runtime
        import axes.axis1_dsl.execution.axis1_backtest as backtest

        for module in (multi, runtime, backtest):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
