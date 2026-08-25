import unittest

from core.tactical_cohort import CohortMember, CohortSnapshot
from core.tactical_validation import TacticalValidationManifest


def snapshot(day: str, symbol: str = "A", unit_id: str = "1516_0905"):
    as_of = day + "090500"
    return CohortSnapshot.create(
        unit_id=unit_id,
        as_of=as_of,
        members=(CohortMember(symbol, as_of, {"captured": True}),),
        source="fixture",
        knowledge_cutoff=as_of,
    )


class TacticalValidationTest(unittest.TestCase):
    def test_manifest_partitions_point_in_time_cohorts_not_bars(self):
        train = [snapshot("20260820"), snapshot("20260821")]
        validation = [snapshot("20260822")]
        oos = [snapshot("20260825")]
        manifest = TacticalValidationManifest.create(
            unit_id="1516_0905", train=train, validation=validation, oos=oos
        )
        self.assertEqual(manifest.split_axis, "POINT_IN_TIME_COHORT_SNAPSHOT")
        self.assertEqual(manifest.partition_of(train[0].snapshot_hash), "TRAIN")
        self.assertEqual(manifest.partition_of(validation[0].snapshot_hash), "VALIDATION")
        self.assertEqual(manifest.partition_of(oos[0].snapshot_hash), "OOS")
        self.assertTrue(manifest.manifest_hash)

    def test_manifest_rejects_overlap(self):
        shared = snapshot("20260820")
        with self.assertRaisesRegex(ValueError, "겹칩니다"):
            TacticalValidationManifest.create(
                unit_id="1516_0905", train=[shared], oos=[shared]
            )

    def test_manifest_rejects_mixed_tactical_units(self):
        with self.assertRaisesRegex(ValueError, "다른 Tactical Unit"):
            TacticalValidationManifest.create(
                unit_id="1516_0905",
                train=[snapshot("20260820")],
                oos=[snapshot("20260825", unit_id="HIGH_BETA")],
            )

    def test_manifest_requires_train_and_oos(self):
        item = snapshot("20260820")
        with self.assertRaisesRegex(ValueError, "train"):
            TacticalValidationManifest.create(unit_id="1516_0905", train=[], oos=[item])
        with self.assertRaisesRegex(ValueError, "OOS"):
            TacticalValidationManifest.create(unit_id="1516_0905", train=[item], oos=[])


if __name__ == "__main__":
    unittest.main()
