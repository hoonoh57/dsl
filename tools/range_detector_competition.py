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
from test_range_detector_equipment import fixtures


def _candidate_permits(result):
    adx = np.asarray(result.permits["adx"], dtype=bool)
    normalized_range = np.asarray(result.permits["normalized_range"], dtype=bool)
    jma_slope = np.asarray(result.permits["jma_slope"], dtype=bool)
    votes = adx.astype(np.int8) + normalized_range.astype(np.int8) + jma_slope.astype(np.int8)
    return {
        "adx_and_range": adx & normalized_range,
        "adx_and_jma": adx & jma_slope,
        "adx_and_range_or_jma": adx & (normalized_range | jma_slope),
        "two_of_three": votes >= 2,
    }


def _summary(rows, names, title):
    print(f"\n{title}")
    range_rows = [r for r in rows if r["label"] == "RANGE"]
    trend_rows = [r for r in rows if r["label"] == "TREND"]
    for name in names:
        range_allow = float(np.mean([r[name] for r in range_rows]))
        trend_allow = float(np.mean([r[name] for r in trend_rows]))
        separation = trend_allow - range_allow
        print(f"{name}: range_allow={range_allow:.3f} trend_allow={trend_allow:.3f} separation={separation:.3f}")


def main():
    warmup = 35
    sensors = ("vhf", "adx", "normalized_range", "jma_slope")
    combinations = ("adx_and_range", "adx_and_jma", "adx_and_range_or_jma", "two_of_three")
    rows = []
    for fixture_id, (market, label) in fixtures().items():
        result = RangeDetectorEquipment.evaluate(market)
        candidate_permits = _candidate_permits(result)
        row = {"fixture": fixture_id, "label": label}
        for sensor in sensors:
            row[sensor] = float(np.mean(np.asarray(result.permits[sensor][warmup:], dtype=float)))
        for name in combinations:
            row[name] = float(np.mean(np.asarray(candidate_permits[name][warmup:], dtype=float)))
        rows.append(row)

    print("fixture\tlabel\t" + "\t".join(sensors))
    for row in rows:
        print(row["fixture"] + "\t" + row["label"] + "\t" + "\t".join(f"{row[s]:.3f}" for s in sensors))

    _summary(rows, sensors, "SENSOR SUMMARY")

    print("\nCOMBINATION FIXTURES")
    print("fixture\tlabel\t" + "\t".join(combinations))
    for row in rows:
        print(row["fixture"] + "\t" + row["label"] + "\t" + "\t".join(f"{row[s]:.3f}" for s in combinations))

    _summary(rows, combinations, "COMBINATION SUMMARY")

    print("\nKEY FAILURE FIXTURES")
    for fixture_id in ("F7_false_breakout", "F8_gap_then_range", "F9_low_vol_trend"):
        row = next(item for item in rows if item["fixture"] == fixture_id)
        values = " ".join(f"{name}={row[name]:.3f}" for name in ("adx",) + combinations)
        print(f"{fixture_id}: {values}")


if __name__ == "__main__":
    main()
