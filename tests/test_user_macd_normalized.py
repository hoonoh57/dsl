import unittest

import numpy as np

from core.dsl_feature_catalog import FEATURE_CASES
from core.dsl_runtime import DSLRuntime, DSLRuntimeError
from core.function_registry import FUNCTION_SPECS
from core.indicators import CoreTALib
from core.user_indicators import normalized_macd_component


class NormalizedMacdUserIndicatorTests(unittest.TestCase):
    @staticmethod
    def market(size=160):
        x = np.arange(size, dtype=float)
        close = 1000.0 + (x * 0.7) + (np.sin(x / 4.0) * 12.0)
        open_ = close - np.cos(x / 5.0)
        high = np.maximum(open_, close) + 2.0
        low = np.minimum(open_, close) - 2.0
        return {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(size, 1000.0),
            "date": np.arange(size, dtype=float),
            "time": np.arange(size, dtype=float),
        }

    def test_registered_as_user_indicator_feature(self):
        spec = FUNCTION_SPECS["user.macd_normalized"]
        self.assertEqual(spec.category, "user")
        self.assertEqual(spec.returns, "series<number>")
        self.assertIn("user.macd_normalized", FEATURE_CASES)

    def test_all_observable_components_are_available_without_tuple_output(self):
        market = self.market()
        code = '''strategy "NormalizedMacdObservable" {
    timeframe = "1d"
    macd_line = user.macd_normalized(close, "macd", 12, 26, 9, "exponential")
    signal_line = user.macd_normalized(close, "signal", 12, 26, 9, "exponential")
    histogram = user.macd_normalized(close, "hist", 12, 26, 9, "exponential")
    hist_abs_pct = user.macd_normalized(close, "hist_abs_pct", 12, 26, 9, "exponential")
    entry_cond = hist_abs_pct > 999
    on(entry_cond) { order.buy(type = "MARKET") }
}'''
        compiled = DSLRuntime.compile(code, market)

        expected_macd = CoreTALib.macd(market["close"], 12, 26, "exponential")
        expected_signal = CoreTALib.ema(expected_macd, 9)
        expected_hist = expected_macd - expected_signal
        expected_pct = np.divide(
            np.abs(expected_hist) * 100.0,
            np.abs(market["close"]),
            out=np.full_like(expected_hist, np.nan),
            where=np.abs(market["close"]) != 0,
        )

        np.testing.assert_allclose(compiled.values["macd_line"], expected_macd, equal_nan=True)
        np.testing.assert_allclose(compiled.values["signal_line"], expected_signal, equal_nan=True)
        np.testing.assert_allclose(compiled.values["histogram"], expected_hist, equal_nan=True)
        np.testing.assert_allclose(compiled.values["hist_abs_pct"], expected_pct, equal_nan=True)

    def test_direct_component_formula_matches_dsl_contract(self):
        market = self.market()
        hist_pct = normalized_macd_component(market["close"], "hist_abs_pct", 12, 26, 9, "exponential")
        self.assertTrue(np.nanmax(hist_pct) >= 0.0)
        self.assertTrue(np.all(hist_pct[np.isfinite(hist_pct)] >= 0.0))

    def test_unknown_component_fails_closed(self):
        market = self.market()
        code = '''strategy "NormalizedMacdBadComponent" {
    timeframe = "1d"
    value = user.macd_normalized(close, "unknown", 12, 26, 9, "exponential")
    entry_cond = false
    on(entry_cond) { order.buy(type = "MARKET") }
}'''
        with self.assertRaisesRegex(DSLRuntimeError, "component"):
            DSLRuntime.compile(code, market)


if __name__ == "__main__":
    unittest.main()
