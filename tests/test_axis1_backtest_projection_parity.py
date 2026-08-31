from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from core.backtest import BacktestEngine as LegacyBacktestEngine
from axes.axis1_dsl.execution import backtest as axis1_backtest
from axes.axis1_dsl.execution.backtest import BacktestEngine as Axis1BacktestEngine
from axes.axis1_dsl.execution import backtest_parent_context as axis1_context_adapter
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding


def market_fixture():
    close = np.asarray([100, 102, 104, 101, 99, 103, 106, 102, 98, 101, 105, 100], dtype=float)
    return {
        "time": [
            "20260831090000", "20260831090500", "20260831091000", "20260831091500",
            "20260831092000", "20260831092500", "20260831093000", "20260831093500",
            "20260831094000", "20260831094500", "20260831095000", "20260831095500",
        ],
        "open": close - 0.5,
        "high": close + 1.5,
        "low": close - 1.5,
        "close": close,
        "volume": np.asarray([10, 12, 11, 13, 12, 14, 15, 13, 16, 15, 17, 18], dtype=float),
        "_meta": {"source": "parity", "timeframe": "5m", "instrument": "TEST"},
    }


CODE = '''strategy "BacktestParity" {
    timeframe = "5m"
    fast = ta.sma(close, 2)
    slow = ta.sma(close, 3)
    j = ta.jma(close, 3, 0, 2)
    enter = ta.crossover(fast, slow)
    exit = ta.crossunder(fast, slow)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''


def assert_nested_numeric_close(testcase, actual, expected):
    if isinstance(expected, float):
        if np.isinf(expected):
            testcase.assertEqual(actual, expected)
        else:
            testcase.assertAlmostEqual(float(actual), expected, places=10)
        return
    if isinstance(expected, dict):
        testcase.assertEqual(set(actual), set(expected))
        for key in expected:
            assert_nested_numeric_close(testcase, actual[key], expected[key])
        return
    if isinstance(expected, list):
        testcase.assertEqual(len(actual), len(expected))
        for got, want in zip(actual, expected):
            assert_nested_numeric_close(testcase, got, want)
        return
    testcase.assertEqual(actual, expected)


class Axis1BacktestProjectionParityTests(unittest.TestCase):
    def test_backtest_trades_metrics_markers_and_projection_match_legacy(self):
        market = market_fixture()
        settings = {
            "total_capital": 1_000_000.0,
            "allocation_pct": 70.0,
            "commission_pct": 0.015,
            "sell_tax_pct": 0.18,
            "slippage_pct": 0.05,
        }
        expected = LegacyBacktestEngine.run(CODE, market=market, settings=settings, data_timeframe="5m")
        actual = Axis1BacktestEngine.run(CODE, market=market, settings=settings, data_timeframe="5m")

        for key in (
            "candles", "markers", "trades", "closed_trades", "indicators", "metrics",
            "metrics_numeric", "equity_curve", "strategy", "settings", "ma5", "ma20",
            "bb_upper", "bb_lower",
        ):
            assert_nested_numeric_close(self, actual[key], expected[key])

        for key in (
            "bars", "signal_counts", "rejections", "broker_history",
            "strategy_market_order_history", "risk_exit_order_history", "pending_order_history",
            "closed_trade_count", "average_mfe_pct", "average_mae_pct",
            "average_realized_return_pct", "mfe_giveback_pct", "data_meta",
            "execution_authority", "entry_policy",
        ):
            assert_nested_numeric_close(self, actual["diagnostics"][key], expected["diagnostics"][key])

    def test_risk_exit_behavior_matches_legacy(self):
        market = market_fixture()
        settings = {
            "total_capital": 500_000.0,
            "allocation_pct": 60.0,
            "stop_loss_pct": 1.0,
            "take_profit_pct": 2.0,
            "commission_pct": 0.0,
            "sell_tax_pct": 0.0,
            "slippage_pct": 0.0,
        }
        expected = LegacyBacktestEngine.run(CODE, market=market, settings=settings, data_timeframe="5m")
        actual = Axis1BacktestEngine.run(CODE, market=market, settings=settings, data_timeframe="5m")
        assert_nested_numeric_close(self, actual["trades"], expected["trades"])
        assert_nested_numeric_close(self, actual["closed_trades"], expected["closed_trades"])
        assert_nested_numeric_close(self, actual["metrics_numeric"], expected["metrics_numeric"])
        assert_nested_numeric_close(
            self,
            actual["diagnostics"]["risk_exit_order_history"],
            expected["diagnostics"]["risk_exit_order_history"],
        )

    def test_prepared_context_binding_is_consumed_exactly(self):
        market = market_fixture()
        times = tuple(market["time"])
        binding = DSLContextSeriesBinding.from_prepared(
            target_symbol="TEST",
            target_times=times,
            frame_hash="frame-hash",
            registry_hash="registry-hash",
            feature_types={"market.permission": "BOOLEAN"},
            feature_values={"market.permission": tuple(i % 2 == 0 for i in range(len(times)))},
        )
        code = '''strategy "ContextBacktest" {
            timeframe = "5m"
            gate = ctx.market.permission and close > open
            on(gate) { order.buy(type = "MARKET") }
        }'''
        result = Axis1BacktestEngine.run(
            code,
            market=market,
            data_timeframe="5m",
            parent_context_binding=binding,
        )
        self.assertTrue(result["diagnostics"]["parent_context"]["supplied"])
        self.assertEqual(result["diagnostics"]["parent_context"]["binding_hash"], binding.binding_hash)
        self.assertEqual(result["diagnostics"]["parent_context"]["bar_count"], len(times))

        bad = DSLContextSeriesBinding.from_prepared(
            target_symbol="TEST",
            target_times=times[:-1] + ("20260831100000",),
            frame_hash="frame-hash",
            registry_hash="registry-hash",
            feature_types={"market.permission": "BOOLEAN"},
            feature_values={"market.permission": tuple(True for _ in times)},
        )
        with self.assertRaisesRegex(ValueError, "exact binding"):
            Axis1BacktestEngine.run(
                code,
                market=market,
                data_timeframe="5m",
                parent_context_binding=bad,
            )

    def test_timeframe_mismatch_error_matches_legacy(self):
        market = market_fixture()
        with self.assertRaises(ValueError) as legacy_ctx:
            LegacyBacktestEngine.run(CODE, market=market, data_timeframe="15m")
        with self.assertRaises(ValueError) as axis1_ctx:
            Axis1BacktestEngine.run(CODE, market=market, data_timeframe="15m")
        self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_axis1_backtest_modules_have_no_frozen_core_or_provider_import(self):
        for module in (axis1_backtest, axis1_context_adapter):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)
            self.assertNotIn("ParentContextFrame", source)
            self.assertNotIn("ParentFeatureRegistry", source)


if __name__ == "__main__":
    unittest.main()
