import tempfile
import unittest
from pathlib import Path

from core.tactical_cohort import CohortMember, CohortSnapshot, StaticCohortProvider
from core.tactical_store import TacticalScenarioStore


class TacticalStoreAndCohortTest(unittest.TestCase):
    def test_point_in_time_cohort_rejects_future_capture_and_outcome_leakage(self):
        with self.assertRaisesRegex(ValueError, "미래"):
            CohortSnapshot.create(
                unit_id="1516_0905",
                as_of="20260825090500",
                members=(CohortMember("A", "20260825091000"),),
                source="fixture",
            )
        with self.assertRaisesRegex(ValueError, "사후 outcome"):
            CohortSnapshot.create(
                unit_id="1516_0905",
                as_of="20260825090500",
                members=(CohortMember("A", "20260825090500", {"mission_success": True}),),
                source="fixture",
            )

    def test_static_provider_requires_explicit_matching_rows(self):
        provider = StaticCohortProvider([
            {
                "unit_id": "1516_0905",
                "as_of": "20260825090500",
                "symbol": "A",
                "capture_time": "20260825090500",
                "features": {"trading_value": 10},
            }
        ])
        snapshot = provider.load(unit_id="1516_0905", as_of="20260825090500")
        self.assertEqual(snapshot.symbols, ("A",))
        self.assertEqual(snapshot.capture_times["A"], "20260825090500")
        self.assertTrue(snapshot.snapshot_hash)
        with self.assertRaisesRegex(ValueError, "찾지 못했습니다"):
            provider.load(unit_id="HIGH_BETA", as_of="20260825090500")

    def test_scenario_and_run_are_immutable_and_promotion_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            store = TacticalScenarioStore(Path(folder) / "tactical.db")
            definition = {
                "scenario_hash": "scenario-1",
                "regime": {"regime_id": "risk-on"},
                "unit": {"unit_id": "HIGH_BETA"},
            }
            scenario = store.create_scenario(definition)
            same = store.create_scenario(definition)
            self.assertEqual(scenario["id"], same["id"])
            result = {
                "scenario_hash": "scenario-1",
                "run_hash": "run-1",
                "status": "COMPLETED",
                "cohort": {"symbols": 2},
            }
            run = store.record_run(scenario["id"], result)
            self.assertIsNone(store.get_head("HIGH_BETA"))
            head = store.promote(run["id"])
            self.assertEqual(head["run_id"], run["id"])
            self.assertEqual(head["run"]["result"]["run_hash"], "run-1")

    def test_run_rejects_wrong_scenario_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            store = TacticalScenarioStore(Path(folder) / "tactical.db")
            scenario = store.create_scenario({
                "scenario_hash": "scenario-1",
                "regime": {"regime_id": "risk-on"},
                "unit": {"unit_id": "HIGH_BETA"},
            })
            with self.assertRaisesRegex(ValueError, "scenario_hash"):
                store.record_run(scenario["id"], {
                    "scenario_hash": "other",
                    "run_hash": "run-2",
                    "status": "COMPLETED",
                })


if __name__ == "__main__":
    unittest.main()
