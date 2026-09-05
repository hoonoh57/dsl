from __future__ import annotations

import inspect
import unittest

import numpy as np

from core.indicator_preview import INDICATOR_PREVIEW_SCHEMA, evaluate_indicator
from core.indicators import CoreTALib


def sample_bars(count: int = 80):
    rows = []
    for index in range(count):
        close = 100.0 + index * 0.35 + (index % 7) * 0.12
        rows.append({
            "time": 1_700_000_000 + index * 300,
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 10_000 + index,
        })
    return rows


class IndicatorPreviewTests(unittest.TestCase):
    def test_jma_preview_compiles_exact_catalog_expression_on_exact_bar_times(self):
        bars = sample_bars()
        result = evaluate_indicator(
            "jma",
            parameters={"length": 7, "phase": -25, "power": 3},
            timeframe="5m",
            bars=bars,
        )
        self.assertEqual(result["schema"], INDICATOR_PREVIEW_SCHEMA)
        self.assertEqual(result["indicator_id"], "jma")
        self.assertEqual(result["title"], "JMA")
        self.assertEqual(result["timeframe"], "5m")
        self.assertEqual(result["dsl_expression"], "ta.jma(close, 7, -25, 3)")
        self.assertIn("indicator_value = ta.jma(close, 7, -25, 3)", result["dsl_code"])
        self.assertEqual(
            result["renderer"],
            {"kind": "line", "pane": "price", "color_by_direction": True},
        )
        self.assertEqual(result["bar_count"], len(bars))
        self.assertEqual(result["points"][-1]["time"], bars[-1]["time"])

        expected = CoreTALib.jma(np.asarray([row["close"] for row in bars], dtype=float), 7, -25, 3)
        self.assertAlmostEqual(result["points"][-1]["value"], float(expected[-1]), places=12)

    def test_supertrend_and_atr_use_same_runtime_semantics(self):
        bars = sample_bars()
        supertrend = evaluate_indicator(
            "supertrend",
            parameters={"period": 10, "multiplier": 2.5},
            timeframe="1d",
            bars=bars,
        )
        self.assertEqual(supertrend["dsl_expression"], "ta.supertrend(10, 2.5)")
        self.assertEqual(supertrend["renderer"]["pane"], "price")
        self.assertTrue(supertrend["points"])
        self.assertTrue(supertrend["direction_colored"])
        self.assertTrue({point["direction"] for point in supertrend["points"]}.issubset({-1, 1}))

        atr = evaluate_indicator("atr", parameters={"period": 14}, timeframe="1d", bars=bars)
        self.assertEqual(atr["dsl_expression"], "ta.atr(14)")
        self.assertEqual(
            atr["renderer"],
            {"kind": "line", "pane": "separate", "color_by_direction": False},
        )
        self.assertTrue(atr["points"])
        expected = CoreTALib.atr(
            np.asarray([row["high"] for row in bars], dtype=float),
            np.asarray([row["low"] for row in bars], dtype=float),
            np.asarray([row["close"] for row in bars], dtype=float),
            14,
        )
        self.assertAlmostEqual(atr["points"][-1]["value"], float(expected[-1]), places=12)

    def test_preview_fails_closed_on_catalog_parameter_or_market_contract_errors(self):
        bars = sample_bars()
        with self.assertRaises(ValueError):
            evaluate_indicator("jma", parameters={"phase": 101}, timeframe="1d", bars=bars)
        broken = [dict(row) for row in bars]
        broken[3].pop("volume")
        with self.assertRaisesRegex(ValueError, "volume"):
            evaluate_indicator("atr", parameters=None, timeframe="1d", bars=broken)
        with self.assertRaises(ValueError):
            evaluate_indicator("atr", parameters=None, timeframe="tick", bars=bars)

    def test_preview_has_no_direct_ta_dispatch_or_chart_authority(self):
        import core.indicator_preview as module

        source = inspect.getsource(module)
        self.assertIn("DSLRuntime.compile", source)
        for token in ("CoreTALib", "LightweightCharts", "ChartDirector", "sqlite", "pymysql"):
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
