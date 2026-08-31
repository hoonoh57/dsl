from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from core import indicators as legacy_indicators
from core import user_indicators as legacy_user
from axes.axis1_dsl.indicators import indicators as axis1_indicators
from axes.axis1_dsl.indicators import user_indicators as axis1_user


def _assert_output_equal(testcase: unittest.TestCase, actual, expected, label: str):
    if isinstance(expected, tuple):
        testcase.assertIsInstance(actual, tuple, label)
        testcase.assertEqual(len(actual), len(expected), label)
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            _assert_output_equal(testcase, actual_item, expected_item, f"{label}[{index}]")
        return
    if isinstance(expected, np.ndarray):
        testcase.assertIsInstance(actual, np.ndarray, label)
        np.testing.assert_allclose(
            np.asarray(actual),
            np.asarray(expected),
            rtol=0.0,
            atol=0.0,
            equal_nan=True,
            err_msg=label,
        )
        expected_colors = getattr(expected, "trend_colors", None)
        actual_colors = getattr(actual, "trend_colors", None)
        if expected_colors is not None or actual_colors is not None:
            testcase.assertIsNotNone(actual_colors, label)
            testcase.assertIsNotNone(expected_colors, label)
            np.testing.assert_array_equal(actual_colors, expected_colors, err_msg=f"{label}.trend_colors")
        return
    testcase.assertEqual(actual, expected, label)


class Axis1IndicatorParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        x = np.arange(1, 121, dtype=np.float64)
        cls.close = 100.0 + 0.15 * x + np.sin(x / 4.0) * 2.0
        cls.high = cls.close + 1.5 + (x % 3) * 0.1
        cls.low = cls.close - 1.4 - (x % 4) * 0.1
        cls.condition = (x.astype(int) % 11 == 0)
        cls.data_condition = (x.astype(int) % 5 == 0)

    def test_public_indicator_methods_match_legacy(self):
        legacy = legacy_indicators.CoreTALib
        axis1 = axis1_indicators.CoreTALib
        cases = (
            ("shift", (self.close, 2)),
            ("highest", (self.close, 7)),
            ("lowest", (self.close, 7)),
            ("rolling_sum", (self.close, 7)),
            ("stdev", (self.close, 7)),
            ("wma", (self.close, 7)),
            ("ma", (self.close, 7, "simple")),
            ("ma", (self.close, 7, "exponential")),
            ("ma", (self.close, 7, "weighted")),
            ("roc", (self.close, 5)),
            ("jma", (self.close, 20, 0, 2)),
            ("supertrend", (self.high, self.low, self.close, 10, 3.0)),
            ("macd", (self.close, 12, 26, "exponential")),
            ("true_range", (self.high, self.low, self.close)),
            ("rma", (self.close, 14)),
            ("atr", (self.high, self.low, self.close, 14)),
            ("trix", (self.close, 12)),
            ("cci", (self.high, self.low, self.close, 20)),
            ("adx", (self.high, self.low, self.close, 14)),
            ("nrange", (self.high, self.low, 10)),
            ("williams_r", (self.high, self.low, self.close, 14)),
            ("abs_range", (self.close, 10)),
            ("sum_abs_r", (self.close, 10)),
            ("vhf", (self.close, 10)),
            ("bars_since", (self.condition,)),
            ("count_since", (self.condition, self.data_condition)),
            ("highest_since", (self.condition, self.close)),
            ("lowest_since", (self.condition, self.close)),
            ("value_when", (1, self.condition, self.close)),
            ("sma", (self.close, 10)),
            ("ema", (self.close, 10)),
            ("rsi", (self.close, 14)),
            ("bbands", (self.close, 20, 2.0)),
            ("crossover", (self.close, legacy.sma(self.close, 10))),
            ("crossunder", (self.close, legacy.sma(self.close, 10))),
        )
        for name, args in cases:
            with self.subTest(name=name, argc=len(args)):
                expected = getattr(legacy, name)(*args)
                actual = getattr(axis1, name)(*args)
                _assert_output_equal(self, actual, expected, name)

    def test_jma_trend_metadata_matches_legacy(self):
        expected = legacy_indicators.CoreTALib.jma(self.close, 12, 35, 2)
        actual = axis1_indicators.CoreTALib.jma(self.close, 12, 35, 2)
        self.assertIsInstance(actual, axis1_indicators.TrendArray)
        _assert_output_equal(self, actual, expected, "jma")

    def test_normalized_macd_components_match_legacy(self):
        self.assertEqual(axis1_user.NORMALIZED_MACD_COMPONENTS, legacy_user.NORMALIZED_MACD_COMPONENTS)
        for component in sorted(legacy_user.NORMALIZED_MACD_COMPONENTS):
            with self.subTest(component=component):
                expected = legacy_user.normalized_macd_component(self.close, component, 12, 26, 9, "exponential")
                actual = axis1_user.normalized_macd_component(self.close, component, 12, 26, 9, "exponential")
                _assert_output_equal(self, actual, expected, component)

    def test_normalized_macd_invalid_component_error_matches_legacy(self):
        with self.assertRaises(ValueError) as legacy_ctx:
            legacy_user.normalized_macd_component(self.close, "unknown")
        with self.assertRaises(ValueError) as axis1_ctx:
            axis1_user.normalized_macd_component(self.close, "unknown")
        self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_axis1_indicator_modules_have_no_legacy_core_runtime_import(self):
        for module in (axis1_indicators, axis1_user):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
