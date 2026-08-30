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


def main():
    warmup = 35
    sensors = ("vhf", "adx", "normalized_range", "jma_slope")
    rows = []
    for fixture_id, (market, label) in fixtures().items():
        result = RangeDetectorEquipment.evaluate(market)
        row = {"fixture": fixture_id, "label": label}
        for sensor in sensors:
            row[sensor] = float(np.mean(np.asarray(result.permits[sensor][warmup:], dtype=float)))
        rows.append(row)

    print("fixture\tlabel\t" + "\t".join(sensors))
    for row in rows:
        print(row["fixture"] + "\t" + row["label"] + "\t" + "\t".join(f"{row[s]:.3f}" for s in sensors))

    print("\nSENSOR SUMMARY")
    range_rows = [r for r in rows if r["label"] == "RANGE"]
    trend_rows = [r for r in rows if r["label"] == "TREND"]
    for sensor in sensors:
        range_allow = float(np.mean([r[sensor] for r in range_rows]))
        trend_allow = float(np.mean([r[sensor] for r in trend_rows]))
        separation = trend_allow - range_allow
        print(f"{sensor}: range_allow={range_allow:.3f} trend_allow={trend_allow:.3f} separation={separation:.3f}")


if __name__ == "__main__":
    main()
