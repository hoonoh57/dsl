from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
for path in (ROOT, TESTS):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from core.range_detector_equipment import RangeDetectorEquipment
from core.transition_shock_guard import TransitionShockGuard
from test_range_detector_equipment import fixtures


def _allow(mask, warmup=35):
    return float(np.mean(np.asarray(mask[warmup:], dtype=float)))


def main():
    rows = []
    for fixture_id, (market, label) in fixtures().items():
        range_result = RangeDetectorEquipment.evaluate(market)
        shock_result = TransitionShockGuard.evaluate(market)
        adx = np.asarray(range_result.permits["adx"], dtype=bool)
        shock = np.asarray(shock_result.trade_permitted, dtype=bool)
        combined = adx & shock
        rows.append({
            "fixture": fixture_id,
            "label": label,
            "adx": _allow(adx),
            "shock": _allow(shock),
            "combined": _allow(combined),
        })

    print("fixture\tlabel\tadx\tshock\tcombined")
    for row in rows:
        print(f'{row["fixture"]}\t{row["label"]}\t{row["adx"]:.3f}\t{row["shock"]:.3f}\t{row["combined"]:.3f}')

    range_rows = [row for row in rows if row["label"] == "RANGE"]
    trend_rows = [row for row in rows if row["label"] == "TREND"]
    print("\nSUMMARY")
    for key in ("adx", "shock", "combined"):
        range_allow = float(np.mean([row[key] for row in range_rows]))
        trend_allow = float(np.mean([row[key] for row in trend_rows]))
        separation = trend_allow - range_allow
        print(f"{key}: range_allow={range_allow:.3f} trend_allow={trend_allow:.3f} separation={separation:.3f}")

    print("\nKEY FIXTURES")
    for fixture_id in ("F7_false_breakout", "F8_gap_then_range", "F9_low_vol_trend", "F10_high_vol_trend"):
        row = next(item for item in rows if item["fixture"] == fixture_id)
        print(f'{fixture_id}: adx={row["adx"]:.3f} shock={row["shock"]:.3f} combined={row["combined"]:.3f}')


if __name__ == "__main__":
    main()
