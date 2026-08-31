from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

import axis1_reference_indicators as ref
from axes.axis1_dsl.core.function_registry import FUNCTION_SPECS
from axes.axis1_dsl.indicators.indicators import CoreTALib
from axes.axis1_dsl.indicators.user_indicators import normalized_macd_component
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime


RTOL = 1e-12
ATOL = 1e-12


DIFFERENTIAL_COVERAGE = {
    "ta.sma", "ta.ema", "ta.wma", "ta.rma", "ta.ma", "ta.rsi",
    "ta.crossover", "ta.crossunder", "ta.highest", "ta.lowest", "ta.sum",
    "ta.stdev", "ta.roc", "ta.jma", "ta.supertrend", "ta.supertrend_direction",
    "ta.macd", "user.macd_normalized", "ta.atr", "ta.adx", "ta.trix", "ta.cci",
    "ta.nrange", "ta.williams_r", "ta.abs_range", "ta.sum_abs_r", "ta.vhf",
    "ta.shift", "ta.count_since", "ta.bars_since", "ta.highest_since",
    "ta.lowest_since", "ta.value_when",
}


def fixture(size=192):
    x = np.arange(1, size + 1, dtype=float)
    close = 100.0 + 0.11 * x + np.sin(x / 3.7) * 2.8 + np.cos(x / 11.0) * 1.3
    high = close + 1.1 + (x.astype(int) % 5) * 0.08
    low = close - 1.0 - (x.astype(int) % 7) * 0.06
    volume = 1000.0 + (x.astype(int) % 13) * 37.0 + x * 2.0
    condition = (x.astype(int) % 13 == 0) | (x.astype(int) % 17 == 0)
    reset = x.astype(int) % 19 == 0
    return close, high, low, volume, condition, reset


def runtime_market(size=192):
    close, high, low, volume, _condition, _reset = fixture(size)
    return {
        "open": close - 0.25,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "date": np.full(size, 20260901.0),
        "time": 90000.0 + np.arange(size, dtype=float) * 100.0,
    }


def assert_numeric(testcase, actual, expected, label):
    np.testing.assert_allclose(
        np.asarray(actual, dtype=float),
        np.asarray(expected, dtype=float),
        rtol=RTOL,
        atol=ATOL,
        equal_nan=True,
        err_msg=label,
    )


class Axis1ReferenceDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.close, cls.high, cls.low, cls.volume, cls.condition, cls.reset = fixture()

    def test_independent_reference_module_has_no_axis1_or_frozen_core_import(self):
        text = Path(ref.__file__).read_text(encoding="utf-8")
        self.assertNotIn("axes.axis1_dsl", text)
        self.assertNotIn("from core", text)
        self.assertNotIn("import core", text)

    def test_registry_ta_and_user_surface_has_explicit_reference_coverage(self):
        registered = {
            name
            for name, spec in FUNCTION_SPECS.items()
            if spec.category in {"ta", "user"}
        }
        self.assertEqual(registered, DIFFERENTIAL_COVERAGE)

    def test_core_indicator_families_match_independent_reference(self):
        cases = (
            ("shift", CoreTALib.shift(self.close, 3), ref.shift(self.close, 3)),
            ("highest", CoreTALib.highest(self.close, 9), ref.highest(self.close, 9)),
            ("lowest", CoreTALib.lowest(self.close, 9), ref.lowest(self.close, 9)),
            ("rolling_sum", CoreTALib.rolling_sum(self.close, 9), ref.rolling_sum(self.close, 9)),
            ("stdev", CoreTALib.stdev(self.close, 9), ref.stdev(self.close, 9)),
            ("sma", CoreTALib.sma(self.close, 9), ref.sma(self.close, 9)),
            ("ema", CoreTALib.ema(self.close, 9), ref.ema(self.close, 9)),
            ("rma", CoreTALib.rma(self.close, 9), ref.rma(self.close, 9)),
            ("wma", CoreTALib.wma(self.close, 9), ref.wma(self.close, 9)),
            ("ma-simple", CoreTALib.ma(self.close, 9, "simple"), ref.ma(self.close, 9, "simple")),
            ("ma-exponential", CoreTALib.ma(self.close, 9, "exponential"), ref.ma(self.close, 9, "exponential")),
            ("ma-weighted", CoreTALib.ma(self.close, 9, "weighted"), ref.ma(self.close, 9, "weighted")),
            ("roc", CoreTALib.roc(self.close, 7), ref.roc(self.close, 7)),
            ("true_range", CoreTALib.true_range(self.high, self.low, self.close), ref.true_range(self.high, self.low, self.close)),
            ("atr", CoreTALib.atr(self.high, self.low, self.close, 14), ref.atr(self.high, self.low, self.close, 14)),
            ("rsi", CoreTALib.rsi(self.close, 14), ref.rsi(self.close, 14)),
            ("macd", CoreTALib.macd(self.close, 5, 17, "exponential"), ref.macd(self.close, 5, 17, "exponential")),
            ("trix", CoreTALib.trix(self.close, 7), ref.trix(self.close, 7)),
            ("cci", CoreTALib.cci(self.high, self.low, self.close, 12), ref.cci(self.high, self.low, self.close, 12)),
            ("adx", CoreTALib.adx(self.high, self.low, self.close, 10), ref.adx(self.high, self.low, self.close, 10)),
            ("nrange", CoreTALib.nrange(self.high, self.low, 11), ref.nrange(self.high, self.low, 11)),
            ("williams_r", CoreTALib.williams_r(self.high, self.low, self.close, 11), ref.williams_r(self.high, self.low, self.close, 11)),
            ("abs_range", CoreTALib.abs_range(self.close, 11), ref.abs_range(self.close, 11)),
            ("sum_abs_r", CoreTALib.sum_abs_r(self.close, 11), ref.sum_abs_r(self.close, 11)),
            ("vhf", CoreTALib.vhf(self.close, 11), ref.vhf(self.close, 11)),
            ("bars_since", CoreTALib.bars_since(self.condition), ref.bars_since(self.condition)),
            ("count_since", CoreTALib.count_since(self.reset, self.condition), ref.count_since(self.reset, self.condition)),
            ("highest_since", CoreTALib.highest_since(self.condition, self.close), ref.highest_since(self.condition, self.close)),
            ("lowest_since", CoreTALib.lowest_since(self.condition, self.close), ref.lowest_since(self.condition, self.close)),
            ("value_when", CoreTALib.value_when(1, self.condition, self.close), ref.value_when(1, self.condition, self.close)),
            ("crossover", CoreTALib.crossover(self.close, CoreTALib.sma(self.close, 8)), ref.crossover(self.close, ref.sma(self.close, 8))),
            ("crossunder", CoreTALib.crossunder(self.close, CoreTALib.sma(self.close, 8)), ref.crossunder(self.close, ref.sma(self.close, 8))),
        )
        for label, actual, expected in cases:
            with self.subTest(label=label):
                if np.asarray(expected).dtype == bool:
                    np.testing.assert_array_equal(actual, expected, err_msg=label)
                else:
                    assert_numeric(self, actual, expected, label)

    def test_period_matrix_catches_warmup_and_recursive_drift(self):
        for period in (2, 3, 5, 8, 14, 21):
            cases = (
                ("sma", CoreTALib.sma(self.close, period), ref.sma(self.close, period)),
                ("ema", CoreTALib.ema(self.close, period), ref.ema(self.close, period)),
                ("rma", CoreTALib.rma(self.close, period), ref.rma(self.close, period)),
                ("wma", CoreTALib.wma(self.close, period), ref.wma(self.close, period)),
                ("highest", CoreTALib.highest(self.close, period), ref.highest(self.close, period)),
                ("lowest", CoreTALib.lowest(self.close, period), ref.lowest(self.close, period)),
                ("sum", CoreTALib.rolling_sum(self.close, period), ref.rolling_sum(self.close, period)),
                ("stdev", CoreTALib.stdev(self.close, period), ref.stdev(self.close, period)),
                ("rsi", CoreTALib.rsi(self.close, period), ref.rsi(self.close, period)),
                ("atr", CoreTALib.atr(self.high, self.low, self.close, period), ref.atr(self.high, self.low, self.close, period)),
                ("cci", CoreTALib.cci(self.high, self.low, self.close, period), ref.cci(self.high, self.low, self.close, period)),
            )
            for label, actual, expected in cases:
                with self.subTest(period=period, label=label):
                    assert_numeric(self, actual, expected, f"{label}:{period}")

    def test_nan_and_flat_edge_fixtures_match_reference_contract(self):
        source = self.close.copy()
        source[:3] = np.nan
        source[37] = np.nan
        flat = np.full(64, 100.0)
        for period in (4, 9):
            for label, actual, expected in (
                ("sma-nan", CoreTALib.sma(source, period), ref.sma(source, period)),
                ("ema-nan", CoreTALib.ema(source, period), ref.ema(source, period)),
                ("rma-nan", CoreTALib.rma(source, period), ref.rma(source, period)),
                ("stdev-nan", CoreTALib.stdev(source, period), ref.stdev(source, period)),
                ("bbands-nan", CoreTALib.bbands(source, period, 2.0), ref.bbands(source, period, 2.0)),
                ("williams-flat", CoreTALib.williams_r(flat + 1, flat - 1, flat, period), ref.williams_r(flat + 1, flat - 1, flat, period)),
                ("vhf-flat", CoreTALib.vhf(flat, period), ref.vhf(flat, period)),
            ):
                with self.subTest(period=period, label=label):
                    if isinstance(expected, tuple):
                        for index, (a, e) in enumerate(zip(actual, expected)):
                            assert_numeric(self, a, e, f"{label}[{index}]")
                    else:
                        assert_numeric(self, actual, expected, label)

    def test_jma_supertrend_and_bbands_match_reference_state_machines(self):
        for length, phase, power in ((3, -50, 1), (12, 35, 2), (20, 0, 2)):
            actual = CoreTALib.jma(self.close, length, phase, power)
            expected, colors = ref.jma(self.close, length, phase, power)
            assert_numeric(self, actual, expected, f"jma:{length}:{phase}:{power}")
            np.testing.assert_array_equal(actual.trend_colors, colors)

        for period, multiplier in ((3, 1.5), (10, 3.0), (21, 2.25)):
            actual_line, actual_direction = CoreTALib.supertrend(self.high, self.low, self.close, period, multiplier)
            expected_line, expected_direction = ref.supertrend(self.high, self.low, self.close, period, multiplier)
            assert_numeric(self, actual_line, expected_line, f"supertrend:{period}:{multiplier}")
            np.testing.assert_array_equal(actual_direction, expected_direction)
            np.testing.assert_array_equal(actual_line.trend_colors, expected_direction)

        for period, multiplier in ((4, 1.5), (20, 2.0)):
            actual = CoreTALib.bbands(self.close, period, multiplier)
            expected = ref.bbands(self.close, period, multiplier)
            for index, (a, e) in enumerate(zip(actual, expected)):
                assert_numeric(self, a, e, f"bbands:{period}:{index}")

    def test_user_normalized_macd_components_match_independent_reference(self):
        for method in ("simple", "exponential", "weighted"):
            for component in ("macd", "signal", "hist", "hist_abs_pct"):
                with self.subTest(method=method, component=component):
                    actual = normalized_macd_component(self.close, component, 5, 17, 4, method)
                    expected = ref.normalized_macd(self.close, component, 5, 17, 4, method)
                    assert_numeric(self, actual, expected, f"normalized:{method}:{component}")

    def test_registered_runtime_mapping_matches_reference_outputs(self):
        code = '''strategy "ReferenceDifferential" {
    timeframe = "5m"
    sma5 = ta.sma(close, 5)
    sma5_shift = ta.sma(close, 5, 2)
    ema7 = ta.ema(close, 7)
    wma6 = ta.wma(close, 6)
    rma8 = ta.rma(close, 8)
    ma_simple = ta.ma(close, 6, "simple")
    ma_exp = ta.ma(close, 6, "exponential")
    rsi_default = ta.rsi(9)
    rsi_series = ta.rsi(close, 9)
    highest7 = ta.highest(close, 7)
    lowest7 = ta.lowest(close, 7)
    sum_all = ta.sum(close)
    sum7 = ta.sum(close, 7)
    sum7_shift = ta.sum(close, 7, 2)
    stdev7 = ta.stdev(close, 7)
    roc5 = ta.roc(close, 5)
    jma12 = ta.jma(close, 12, 35, 2)
    jma_default = ta.jma(12, 35, 2)
    st = ta.supertrend(10, 3)
    st_dir = ta.supertrend_direction(10, 3)
    macd_line = ta.macd(close, 5, 17, "exponential")
    norm_hist = user.macd_normalized(close, "hist", 5, 17, 4, "exponential")
    atr10 = ta.atr(10)
    adx10 = ta.adx(10)
    trix7 = ta.trix(7)
    cci12 = ta.cci(12)
    nrange9 = ta.nrange(9)
    will9 = ta.williams_r(9)
    abs9 = ta.abs_range(9)
    sum_abs9 = ta.sum_abs_r(9)
    vhf9 = ta.vhf(9)
    shifted = ta.shift(close, 3)
    cond = close > sma5
    reset = close < ema7
    crossed_up = ta.crossover(close, sma5)
    crossed_down = ta.crossunder(close, sma5)
    bars = ta.bars_since(crossed_up)
    counted = ta.count_since(reset, cond)
    high_since = ta.highest_since(crossed_up, close)
    low_since = ta.lowest_since(crossed_down, close)
    previous_hit = ta.value_when(1, crossed_up, close)
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        close = market["close"]
        high = market["high"]
        low = market["low"]
        st_line, st_direction = ref.supertrend(high, low, close, 10, 3)
        expected = {
            "sma5": ref.sma(close, 5),
            "sma5_shift": ref.shift(ref.sma(close, 5), 2),
            "ema7": ref.ema(close, 7),
            "wma6": ref.wma(close, 6),
            "rma8": ref.rma(close, 8),
            "ma_simple": ref.ma(close, 6, "simple"),
            "ma_exp": ref.ma(close, 6, "exponential"),
            "rsi_default": ref.rsi(close, 9),
            "rsi_series": ref.rsi(close, 9),
            "highest7": ref.highest(close, 7),
            "lowest7": ref.lowest(close, 7),
            "sum_all": np.cumsum(np.nan_to_num(close)),
            "sum7": ref.rolling_sum(close, 7),
            "sum7_shift": ref.shift(ref.rolling_sum(close, 7), 2),
            "stdev7": ref.stdev(close, 7),
            "roc5": ref.roc(close, 5),
            "jma12": ref.jma(close, 12, 35, 2)[0],
            "jma_default": ref.jma(close, 12, 35, 2)[0],
            "st": st_line,
            "st_dir": st_direction,
            "macd_line": ref.macd(close, 5, 17, "exponential"),
            "norm_hist": ref.normalized_macd(close, "hist", 5, 17, 4, "exponential"),
            "atr10": ref.atr(high, low, close, 10),
            "adx10": ref.adx(high, low, close, 10),
            "trix7": ref.trix(close, 7),
            "cci12": ref.cci(high, low, close, 12),
            "nrange9": ref.nrange(high, low, 9),
            "will9": ref.williams_r(high, low, close, 9),
            "abs9": ref.abs_range(close, 9),
            "sum_abs9": ref.sum_abs_r(close, 9),
            "vhf9": ref.vhf(close, 9),
            "shifted": ref.shift(close, 3),
        }
        cond = close > expected["sma5"]
        reset = close < expected["ema7"]
        crossed_up = ref.crossover(close, expected["sma5"])
        crossed_down = ref.crossunder(close, expected["sma5"])
        expected.update({
            "cond": cond,
            "reset": reset,
            "crossed_up": crossed_up,
            "crossed_down": crossed_down,
            "bars": ref.bars_since(crossed_up),
            "counted": ref.count_since(reset, cond),
            "high_since": ref.highest_since(crossed_up, close),
            "low_since": ref.lowest_since(crossed_down, close),
            "previous_hit": ref.value_when(1, crossed_up, close),
        })
        for name, values in expected.items():
            with self.subTest(name=name):
                if np.asarray(values).dtype == bool:
                    np.testing.assert_array_equal(compiled.values[name], values)
                else:
                    assert_numeric(self, compiled.values[name], values, name)

    def test_multi_output_lowering_matches_reference_components(self):
        code = '''strategy "ReferenceMultiOutput" {
    timeframe = "5m"
    upper, middle, lower = ta.bbands(close, 8, 2)
    st_line, st_direction = ta.supertrend(9, 2.5)
    macd, signal, hist, strength = user.macd_normalized_all(close, 5, 17, 4, "exponential")
}'''
        market = runtime_market()
        compiled = Axis1DSLRuntime.compile(code, {key: value.copy() for key, value in market.items()})
        bands = ref.bbands(market["close"], 8, 2)
        trend = ref.supertrend(market["high"], market["low"], market["close"], 9, 2.5)
        normalized = tuple(
            ref.normalized_macd(market["close"], component, 5, 17, 4, "exponential")
            for component in ("macd", "signal", "hist", "hist_abs_pct")
        )
        expected = {
            "upper": bands[0], "middle": bands[1], "lower": bands[2],
            "st_line": trend[0], "st_direction": trend[1],
            "macd": normalized[0], "signal": normalized[1], "hist": normalized[2], "strength": normalized[3],
        }
        for name, values in expected.items():
            with self.subTest(name=name):
                assert_numeric(self, compiled.values[name], values, name)


if __name__ == "__main__":
    unittest.main()
