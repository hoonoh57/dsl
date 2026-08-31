from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from core.multitimeframe import MultiTimeframeContext as LegacyMTF
from core.multitimeframe import MultiTimeframeError as LegacyMTFError
from core.dsl_context import DSLContextSeriesBinding as LegacyBinding
from axes.axis1_dsl.runtime.multitimeframe import MultiTimeframeContext as Axis1MTF
from axes.axis1_dsl.runtime.multitimeframe import MultiTimeframeError as Axis1MTFError
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding as Axis1Binding


class Axis1MTFContextParityTests(unittest.TestCase):
    @staticmethod
    def _market():
        size = 18
        close = np.asarray([100.0 + i * 0.7 + (i % 3) * 0.2 for i in range(size)])
        return {
            "date": np.full(size, 20260831),
            "time": np.asarray([90000 + i * 100 for i in range(size)]),
            "open": close - 0.3,
            "high": close + 0.8,
            "low": close - 0.9,
            "close": close,
            "volume": np.asarray([1000.0 + i * 17.0 for i in range(size)]),
        }

    @staticmethod
    def _binding_payload():
        return {
            "target_symbol": "005930",
            "target_times": (
                "20260831090000",
                "20260831090100",
                "20260831090200",
            ),
            "frame_hash": "frame-hash-v1",
            "registry_hash": "registry-hash-v1",
            "feature_types": {
                "market.regime": "STRING",
                "sector.strength": "NUMBER",
                "risk.allowed": "BOOLEAN",
            },
            "feature_values": {
                "market.regime": ("BULL", "BULL", "NEUTRAL"),
                "sector.strength": (1.25, 1.5, 0.75),
                "risk.allowed": (True, True, False),
            },
        }

    def test_confirmed_mtf_fields_match_legacy(self):
        market = self._market()
        legacy = LegacyMTF(market)
        axis1 = Axis1MTF(market)
        for timeframe in ("5m", "15m"):
            for field in ("open", "high", "low", "close", "volume"):
                with self.subTest(timeframe=timeframe, field=field):
                    np.testing.assert_allclose(
                        axis1.field(timeframe, field),
                        legacy.field(timeframe, field),
                        equal_nan=True,
                    )

    def test_confirmed_mtf_sma_matches_legacy(self):
        market = self._market()
        legacy = LegacyMTF(market)
        axis1 = Axis1MTF(market)
        for timeframe, period in (("5m", 2), ("5m", 3), ("15m", 2)):
            with self.subTest(timeframe=timeframe, period=period):
                np.testing.assert_allclose(
                    axis1.sma(timeframe, period),
                    legacy.sma(timeframe, period),
                    equal_nan=True,
                )

    def test_mtf_fail_closed_errors_match_legacy(self):
        market = self._market()
        cases = (
            ("bad", "close"),
            ("0m", "close"),
            ("5m", "median"),
        )
        for timeframe, field in cases:
            with self.subTest(timeframe=timeframe, field=field):
                with self.assertRaises(LegacyMTFError) as legacy_ctx:
                    LegacyMTF(market).field(timeframe, field)
                with self.assertRaises(Axis1MTFError) as axis1_ctx:
                    Axis1MTF(market).field(timeframe, field)
                self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_provider_free_context_binding_matches_legacy_contract(self):
        payload = self._binding_payload()
        legacy = LegacyBinding(**payload)
        legacy.validate()
        axis1 = Axis1Binding.from_prepared(**payload)

        self.assertEqual(axis1.public_dict(), legacy.public_dict())
        self.assertEqual(axis1.binding_hash, legacy.binding_hash)
        self.assertEqual(axis1.semantic_types(), legacy.semantic_types())

        legacy_values = legacy.runtime_values()
        axis1_values = axis1.runtime_values()
        self.assertEqual(set(axis1_values), set(legacy_values))
        for key in legacy_values:
            np.testing.assert_array_equal(axis1_values[key], legacy_values[key])

    def test_context_exact_time_and_value_validation_matches_legacy(self):
        payload = self._binding_payload()
        legacy = LegacyBinding(**payload)
        axis1 = Axis1Binding.from_prepared(**payload)

        shifted = (
            "20260831090000",
            "20260831090100",
            "20260831090300",
        )
        with self.assertRaises(ValueError) as legacy_ctx:
            legacy.validate_target_times(shifted)
        with self.assertRaises(ValueError) as axis1_ctx:
            axis1.validate_target_times(shifted)
        self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

        bad_payload = dict(payload)
        bad_payload["feature_values"] = {
            "market.regime": payload["feature_values"]["market.regime"],
            "sector.strength": payload["feature_values"]["sector.strength"],
        }
        bad_legacy = LegacyBinding(**bad_payload)
        with self.assertRaises(ValueError) as legacy_ctx:
            bad_legacy.validate()
        with self.assertRaises(ValueError) as axis1_ctx:
            Axis1Binding.from_prepared(**bad_payload)
        self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_axis1_boundary_has_no_legacy_provider_runtime_dependency(self):
        mtf_source = Path(__import__("axes.axis1_dsl.runtime.multitimeframe", fromlist=["x"]).__file__).read_text(encoding="utf-8")
        context_module = __import__("axes.axis1_dsl.runtime.dsl_context", fromlist=["x"])
        context_source = Path(context_module.__file__).read_text(encoding="utf-8")
        for source in (mtf_source, context_source):
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)
        self.assertFalse(hasattr(context_module.DSLContextSeriesBinding, "from_frame"))


if __name__ == "__main__":
    unittest.main()
