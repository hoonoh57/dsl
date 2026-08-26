import tempfile
from pathlib import Path
import unittest

from core.tactical_evolution import CapabilityBudget, EvolutionArena, EvolutionGeneration, SkillSpec
from core.tactical_evolution_store import TacticalEvolutionStore
from core.tactical_failure import TacticalFailureAnalyzer


def profile(candidate_id, candidate_hash, run_hash, *, avg=0.2, mdd=-2.0, worst=-1.0, cost=30.0,
            rate=0.5, giveback=1.5, complexity=2):
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {
            "candidate_id": candidate_id,
            "candidate_hash": candidate_hash,
            "complexity_units": complexity,
        },
        "case_set_hash": "frozen-cases",
        "context_policy": {
            "require_neutral_context": True,
            "require_uniform_settings": True,
        },
        "aggregate": {
            "cases": 2,
            "profitable_case_rate": rate,
            "average_return_pct": avg,
            "median_return_pct": avg,
            "worst_case_return_pct": worst,
            "worst_mdd_pct": mdd,
            "total_cost": cost,
            "average_mfe_giveback_pct": giveback,
            "top1_positive_return_concentration": 0.5,
            "complexity_units": complexity,
        },
        "results": [
            {
                "case_id": "LOSS",
                "return_pct": -1.0,
                "mdd_pct": -2.0,
                "profit_factor": 0.4,
                "closed_trade_count": 4,
                "total_cost": 20.0,
                "average_mfe_pct": 1.5,
                "average_mae_pct": -1.0,
                "mfe_giveback_pct": 2.5,
            },
            {
                "case_id": "WIN",
                "return_pct": 1.4,
                "mdd_pct": -0.4,
                "profit_factor": 2.0,
                "closed_trade_count": 1,
                "total_cost": 10.0,
                "average_mfe_pct": 2.0,
                "average_mae_pct": -0.3,
                "mfe_giveback_pct": 0.3,
            },
        ],
        "run_hash": run_hash,
    }


class TacticalEvolutionStoreTests(unittest.TestCase):
    def test_full_generation_experience_is_append_only_and_head_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            store = TacticalEvolutionStore(Path(temp) / "evolution.db")
            parent = profile("G0", "candidate-g0", "run-g0")
            failure = TacticalFailureAnalyzer.analyze(parent)
            g0 = EvolutionGeneration.create(
                family_id="JMA",
                generation_index=0,
                profile=parent,
                capability_usage={"skills": 0, "complexity_units": 2},
            )
            store.record_profile("JMA", parent)
            store.record_failure("JMA", failure)
            store.record_generation(g0)
            self.assertIsNone(store.get_head("JMA"))
            store.promote("JMA", g0.generation_hash)
            self.assertEqual(store.get_head("JMA")["generation_hash"], g0.generation_hash)

            child = profile(
                "G1", "candidate-g1", "run-g1",
                avg=0.8, mdd=-1.7, worst=-0.8, cost=20.0,
                rate=0.6, giveback=0.8, complexity=3,
            )
            skill = SkillSpec(
                skill_id="RANGE_DEFENSE",
                capability="RANGE_DEFENSE",
                implementation="crossover cooldown",
                addresses_failure_tags=("WHIPSAW",),
                cost={"complexity_units": 1, "parameters": 1},
            )
            decision = EvolutionArena.evaluate_upgrade(
                parent_generation=g0,
                parent_profile=parent,
                child_profile=child,
                skill=skill,
                failure_report=failure,
                budget=CapabilityBudget(),
            )
            self.assertEqual(decision["decision"], "ACCEPT")
            store.record_profile("JMA", child)
            store.record_decision("JMA", decision)
            g1 = decision["child_generation"]
            store.record_generation(g1)

            # Recording a successful child does not silently promote it.
            self.assertEqual(store.get_head("JMA")["generation_hash"], g0.generation_hash)
            store.promote("JMA", g1.generation_hash)
            self.assertEqual(store.get_head("JMA")["generation_hash"], g1.generation_hash)
            self.assertEqual(store.get_head("JMA")["generation"]["payload"]["parent_generation_hash"], g0.generation_hash)

    def test_failure_requires_parent_profile_to_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            store = TacticalEvolutionStore(Path(temp) / "evolution.db")
            parent = profile("G0", "candidate-g0", "run-g0")
            failure = TacticalFailureAnalyzer.analyze(parent)
            with self.assertRaisesRegex(ValueError, "parent profile"):
                store.record_failure("JMA", failure)

    def test_generation_lineage_cannot_skip_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            store = TacticalEvolutionStore(Path(temp) / "evolution.db")
            child = profile("G1", "candidate-g1", "run-g1", complexity=3)
            store.record_profile("JMA", child)
            g1 = EvolutionGeneration.create(
                family_id="JMA",
                generation_index=1,
                profile=child,
                acquired_skills=("RANGE_DEFENSE",),
                capability_usage={"skills": 1, "complexity_units": 3},
                parent_generation_hash="missing-parent",
            )
            with self.assertRaisesRegex(ValueError, "parent lineage"):
                store.record_generation(g1)


if __name__ == "__main__":
    unittest.main()
