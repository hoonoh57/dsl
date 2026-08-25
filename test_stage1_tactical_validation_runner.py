import unittest

from core.tactical_cohort import CohortMember, CohortSnapshot
from core.tactical_validation import TacticalValidationManifest
from core.tactical_validation_runner import TacticalValidationRunner


def snap(day):
    return CohortSnapshot.create(
        unit_id="U",
        as_of=f"{day}090500",
        members=(CohortMember("000001", f"{day}090500", {"x": 1}),),
        source="fixture",
    )


class TacticalValidationRunnerTests(unittest.TestCase):
    def test_summary_uses_manifest_partition_without_reselecting_by_outcome(self):
        train = snap("20260701")
        valid = snap("20260702")
        oos = snap("20260703")
        manifest = TacticalValidationManifest.create(
            unit_id="U",
            train=[train],
            validation=[valid],
            oos=[oos],
        )
        reports = []
        for s, ret, positive in (
            (train, 1.0, 1),
            (valid, -1.0, 0),
            (oos, 2.0, 1),
        ):
            reports.append({
                "cohort_snapshot_hash": s.snapshot_hash,
                "cohort_symbols": 2,
                "official_mission_positive": positive,
                "strategy_profitable_symbols": int(ret > 0),
                "positive_and_profitable": int(ret > 0 and positive),
                "average_strategy_return_pct": ret,
            })
        summary = TacticalValidationRunner.summarize(manifest, reports)
        self.assertEqual(summary["partitions"]["TRAIN"]["cohorts"], 1)
        self.assertEqual(summary["partitions"]["VALIDATION"]["cohorts"], 1)
        self.assertEqual(summary["partitions"]["OOS"]["cohorts"], 1)

    def test_missing_manifest_report_fails_closed(self):
        train = snap("20260701")
        oos = snap("20260703")
        manifest = TacticalValidationManifest.create(unit_id="U", train=[train], oos=[oos])
        with self.assertRaisesRegex(ValueError, "누락"):
            TacticalValidationRunner.summarize(
                manifest,
                [{"cohort_snapshot_hash": train.snapshot_hash}],
            )


if __name__ == "__main__":
    unittest.main()
