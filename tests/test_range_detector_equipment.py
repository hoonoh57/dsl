from __future__ import annotations

import unittest
import numpy as np

from core.range_detector_equipment import RangeDetectorEquipment


def market_from_close(close, spread=0.6):
    close = np.asarray(close, dtype=float)
    open_ = np.concatenate(([close[0]], close[:-1]))
    high = np.maximum(open_, close) + float(spread)
    low = np.minimum(open_, close) - float(spread)
    return {"open": open_, "high": high, "low": low, "close": close, "volume": np.full(len(close), 1000.0)}


def fixtures():
    n = 160
    t = np.arange(n, dtype=float)
    rng = np.random.default_rng(20260831)
    return {
        "F1_small_range": (market_from_close(100 + 0.35 * np.sin(t / 2.0)), "RANGE"),
        "F2_wide_chop": (market_from_close(100 + 3.0 * np.sin(t / 2.2), 1.0), "RANGE"),
        "F3_uptrend": (market_from_close(100 + 0.22 * t + 0.15 * np.sin(t / 5.0)), "TREND"),
        "F4_downtrend": (market_from_close(140 - 0.20 * t + 0.15 * np.sin(t / 5.0)), "TREND"),
        "F5_range_breakout": (market_from_close(np.r_[100 + 0.3*np.sin(t[:80]/2), 100 + 0.55*np.arange(80)]), "MIXED"),
        "F6_trend_exhaust_range": (market_from_close(np.r_[100 + 0.45*np.arange(80), 136 + 0.4*np.sin(t[:80]/2)]), "MIXED"),
        "F7_false_breakout": (market_from_close(np.r_[100 + 0.3*np.sin(t[:70]/2), np.linspace(100,106,8), np.linspace(106,100,8), 100 + 0.3*np.sin(t[:74]/2)]), "RANGE"),
        "F8_gap_then_range": (market_from_close(np.r_[100 + 0.2*np.sin(t[:50]/2), 108 + 0.4*np.sin(t[:110]/2)]), "RANGE"),
        "F9_low_vol_trend": (market_from_close(100 + 0.06*t + 0.03*np.sin(t/7), 0.15), "TREND"),
        "F10_high_vol_trend": (market_from_close(100 + 0.30*t + rng.normal(0,0.8,n), 1.2), "TREND"),
    }


class RangeDetectorEquipmentTests(unittest.TestCase):
    def test_deterministic_and_complete_sensor_pack(self):
        market, _ = fixtures()["F3_uptrend"]
        a = RangeDetectorEquipment.evaluate(market)
        b = RangeDetectorEquipment.evaluate(market)
        self.assertEqual(set(a.permits), {"vhf", "adx", "normalized_range", "jma_slope"})
        for name in a.permits:
            np.testing.assert_array_equal(a.permits[name], b.permits[name])
            self.assertEqual(len(a.permits[name]), len(market["close"]))

    def test_competition_report_has_range_and_trend_discrimination(self):
        rows = []
        for fixture_id, (market, label) in fixtures().items():
            result = RangeDetectorEquipment.evaluate(market)
            warmup = 35
            row = {"fixture": fixture_id, "label": label}
            for name, permit in result.permits.items():
                row[name] = float(np.mean(np.asarray(permit[warmup:], dtype=float)))
            rows.append(row)

        range_rows = [row for row in rows if row["label"] == "RANGE"]
        trend_rows = [row for row in rows if row["label"] == "TREND"]
        self.assertGreaterEqual(len(range_rows), 4)
        self.assertGreaterEqual(len(trend_rows), 4)

        # Competition invariant: at least one independent sensor must materially
        # distinguish the deterministic range basket from the trend basket.
        separations = {}
        for sensor in ("vhf", "adx", "normalized_range", "jma_slope"):
            trend_allow = float(np.mean([row[sensor] for row in trend_rows]))
            range_allow = float(np.mean([row[sensor] for row in range_rows]))
            separations[sensor] = trend_allow - range_allow
        self.assertGreater(max(separations.values()), 0.25, msg=str({"rows": rows, "separations": separations}))

    def test_wide_chop_and_low_vol_trend_are_not_equated_with_volatility(self):
        wide = RangeDetectorEquipment.evaluate(fixtures()["F2_wide_chop"][0])
        lowtrend = RangeDetectorEquipment.evaluate(fixtures()["F9_low_vol_trend"][0])
        warmup = 35
        # Compare the sensor itself, not a provisional thresholded permit.  A
        # threshold can legitimately saturate both fixtures at True while the
        # underlying directional-efficiency signal still separates them.
        wide_vhf = float(np.nanmean(wide.vhf[warmup:]))
        lowtrend_vhf = float(np.nanmean(lowtrend.vhf[warmup:]))
        self.assertGreater(lowtrend_vhf, wide_vhf, msg={"wide_vhf": wide_vhf, "lowtrend_vhf": lowtrend_vhf})


if __name__ == "__main__":
    unittest.main()
