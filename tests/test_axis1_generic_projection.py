from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.core.multi_output import lower_multi_output
from axes.axis1_dsl.execution.backtest import BacktestEngine as MigratedBacktestEngine
from axes.axis1_dsl.execution import generic_projection
from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine


def market_fixture(size=48):
    index = np.arange(size, dtype=float)
    close = 100.0 + np.sin(index / 3.0) * 4.0 + index * 0.15
    start = datetime(2026, 8, 31, 9, 0, 0)
    times = [
        (start + timedelta(minutes=5 * i)).strftime("%Y%m%d%H%M%S")
        for i in range(size)
    ]
    return {
        "time": times,
        "open": close - 0.4,
        "high": close + 1.2,
        "low": close - 1.1,
        "close": close,
        "volume": 1000.0 + index * 10.0,
        "_meta": {"source": "generic-projection-test", "timeframe": "5m", "instrument": "TEST"},
    }


CODE = '''strategy "GenericProjection" {
    timeframe = "5m"
    baseline = ta.ema(close, 5)
    ceiling, basis, floor = ta.bbands(close, 8, 2)
    trendline, trenddir = ta.supertrend(5, 2)
    gate = close > basis and trenddir > 0
    on(gate) { order.buy(type = "MARKET") }
}'''


class Axis1GenericProjectionTests(unittest.TestCase):
    def test_multi_output_targets_are_joined_generically_by_binding_metadata(self):
        result = Axis1BacktestEngine.run(
            CODE,
            market=market_fixture(),
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
        )
        projection = result["projection"]
        self.assertEqual(projection["schema"], generic_projection.PROJECTION_SCHEMA)
        self.assertEqual(projection["policy"], "EXECUTION_OUTPUT_ONLY_NO_RECOMPUTE_NO_DEFAULT")

        items = {item["name"]: item for item in projection["items"]}
        expected = {
            "ceiling": ("ta.bbands", "upper"),
            "basis": ("ta.bbands", "middle"),
            "floor": ("ta.bbands", "lower"),
            "trendline": ("ta.supertrend", "line"),
            "trenddir": ("ta.supertrend", "direction"),
        }
        for target, (function, component) in expected.items():
            with self.subTest(target=target):
                item = items[target]
                self.assertTrue(item["available"])
                self.assertEqual(item["value_type"], "series<number>")
                self.assertEqual(item["kind"], "numeric_series")
                self.assertEqual(item["source"]["kind"], "multi_output_component")
                self.assertEqual(item["source"]["function"], function)
                self.assertEqual(item["source"]["component"], component)
                self.assertIsInstance(item["indicator_index"], int)

        self.assertEqual(items["baseline"]["source"], {"kind": "assignment"})
        self.assertEqual(items["baseline"]["kind"], "numeric_series")
        self.assertEqual(projection["multi_output_target_count"], 5)
        self.assertEqual(projection["projected_multi_output_target_count"], 5)

    def test_projection_reuses_existing_indicator_data_and_render_intent(self):
        market = market_fixture()
        lowered = lower_multi_output(CODE)
        base = MigratedBacktestEngine.run(
            lowered.source,
            market=market,
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
        )
        projected = Axis1BacktestEngine.run(
            CODE,
            market=market,
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
        )
        base_by_name = {item["name"]: item for item in base["indicators"]}
        projected_by_name = {item["name"]: item for item in projected["indicators"]}
        self.assertEqual(set(projected_by_name), set(base_by_name))
        for name, expected in base_by_name.items():
            with self.subTest(name=name):
                actual = projected_by_name[name]
                self.assertEqual(actual["data"], expected["data"])
                self.assertEqual(actual["overlay"], expected["overlay"])
                self.assertEqual(actual["direction_colored"], expected["direction_colored"])
                manifest = next(item for item in projected["projection"]["items"] if item["name"] == name)
                self.assertEqual(manifest["pane"], "overlay" if expected["overlay"] else "pane")
                self.assertEqual(
                    manifest["style"],
                    "direction_line" if expected["direction_colored"] else "line",
                )

    def test_warmup_only_multi_output_is_not_synthesized(self):
        code = '''strategy "NoSyntheticProjection" {
            timeframe = "5m"
            high_band, mid_band, low_band = ta.bbands(close, 100, 2)
        }'''
        result = Axis1BacktestEngine.run(
            code,
            market=market_fixture(20),
            data_timeframe="5m",
        )
        items = {item["name"]: item for item in result["projection"]["items"]}
        for target in ("high_band", "mid_band", "low_band"):
            with self.subTest(target=target):
                self.assertIn(target, items)
                self.assertFalse(items[target]["available"])
                self.assertIsNone(items[target]["indicator_index"])
                self.assertIsNone(items[target]["pane"])
                self.assertIsNone(items[target]["style"])
        self.assertEqual(result["projection"]["projected_multi_output_target_count"], 0)

    def test_indicator_items_receive_projection_join_fields(self):
        result = Axis1BacktestEngine.run(
            CODE,
            market=market_fixture(),
            data_timeframe="5m",
        )
        for indicator in result["indicators"]:
            self.assertEqual(indicator["projection_id"], f"series:{indicator['name']}")
            self.assertEqual(indicator["projection_kind"], "numeric_series")
            self.assertIn(indicator["projection_pane"], {"overlay", "pane"})

        summary = result["diagnostics"]["projection"]
        self.assertEqual(summary["schema"], generic_projection.PROJECTION_SCHEMA)
        self.assertEqual(summary["item_count"], len(result["projection"]["items"]))

    def test_projection_layer_has_no_calculation_or_frozen_core_dependency(self):
        source = Path(generic_projection.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)
        self.assertNotIn("CoreTALib", source)
        self.assertNotIn("DSLRuntime", source)
        self.assertNotIn("BacktestEngine", source)
        self.assertNotIn("numpy", source)


if __name__ == "__main__":
    unittest.main()
