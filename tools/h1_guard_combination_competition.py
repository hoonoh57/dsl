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


def _permit_from_blocked(mask):
    return ~np.asarray(mask, dtype=bool)


def main():
    rows = []
    component_keys = ("gap_shock", "large_bar_shock", "false_breakout", "post_breakout_failure")
    for fixture_id, (market, label) in fixtures().items():
        range_result = RangeDetectorEquipment.evaluate(market)
        shock_result = TransitionShockGuard.evaluate(market)
        adx = np.asarray(range_result.permits["adx"], dtype=bool)
        shock = np.asarray(shock_result.trade_permitted, dtype=bool)
        combined = adx & shock

        component_permits = {
            key: _permit_from_blocked(shock_result.blocked[key])
            for key in component_keys
        }
        no_large_bar = (
            component_permits["gap_shock"]
            & component_permits["false_breakout"]
            & component_permits["post_breakout_failure"]
        )
        adx_no_large_bar = adx & no_large_bar

        row = {
            "fixture": fixture_id,
            "label": label,
            "adx": _allow(adx),
            "shock": _allow(shock),
            "combined": _allow(combined),
            "no_large_bar": _allow(no_large_bar),
            "adx_no_large_bar": _allow(adx_no_large_bar),
        }
        for key, permit in component_permits.items():
            row[key] = _allow(permit)
        rows.append(row)

    print("fixture\tlabel\tadx\tshock\tcombined")
    for row in rows:
        print(f'{row["fixture"]}\t{row["label"]}\t{row["adx"]:.3f}\t{row["shock"]:.3f}\t{row["combined"]:.3f}')

    range_rows = [row for row in rows if row["label"] == "RANGE"]
    trend_rows = [row for row in rows if row["label"] == "TREND"]
    print("\nSUMMARY")
    for key in ("adx", "shock", "combined", "no_large_bar", "adx_no_large_bar"):
        range_allow = float(np.mean([row[key] for row in range_rows]))
        trend_allow = float(np.mean([row[key] for row in trend_rows]))
        separation = trend_allow - range_allow
        print(f"{key}: range_allow={range_allow:.3f} trend_allow={trend_allow:.3f} separation={separation:.3f}")

    print("\nSHOCK COMPONENT ALLOW SUMMARY")
    for key in component_keys:
        range_allow = float(np.mean([row[key] for row in range_rows]))
        trend_allow = float(np.mean([row[key] for row in trend_rows]))
        print(f"{key}: range_allow={range_allow:.3f} trend_allow={trend_allow:.3f}")

    print("\nKEY FIXTURES")
    for fixture_id in ("F7_false_breakout", "F8_gap_then_range", "F9_low_vol_trend", "F10_high_vol_trend"):
        row = next(item for item in rows if item["fixture"] == fixture_id)
        print(
            f'{fixture_id}: adx={row["adx"]:.3f} shock={row["shock"]:.3f} combined={row["combined"]:.3f} '
            f'gap={row["gap_shock"]:.3f} large_bar={row["large_bar_shock"]:.3f} '
            f'false_breakout={row["false_breakout"]:.3f} post_failure={row["post_breakout_failure"]:.3f} '
            f'no_large_bar={row["no_large_bar"]:.3f} adx_no_large_bar={row["adx_no_large_bar"]:.3f}'
        )


if __name__ == "__main__":
    main()
