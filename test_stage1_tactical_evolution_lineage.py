import tempfile
from pathlib import Path
import unittest

from core.tactical_evolution import CapabilityBudget, EvolutionArena, EvolutionGeneration, SkillSpec
from core.tactical_evolution_lineage import TacticalEvolutionLineage
from core.tactical_evolution_store import TacticalEvolutionStore
from core.tactical_failure import TacticalFailureAnalyzer


def profile(candidate_id, candidate_hash, run_hash, *, avg=0.2, mdd=-2.0, worst=-1.0,
            cost=30.0, rate=0.5, giveback=1.5, complexity=2):
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
            "active_cases": 2,
            "no_trade_cases": 0,
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
                "trade_count": 4,
                "closed_trade_count": 4,
                "total_cost": 20.0,
                "average_mfe_pct": 1.5,
                "average_mae_pct": -1.0,
                "mfe_giveback_pct": 2.5,
                "backtest": {"metrics_numeric": {"open_position": 0}},
            },
            {
                "case_id": "WIN",
                "return_pct": 1.4,
                "mdd_pct": -0.4,
                "profit_factor": 2.0,
                "trade_count": 1,
                "closed_trade_count": 1,
                "total_cost": 10.0,
                "average_mfe_pct": 2.0,
                "average_mae_pct": -0.3,
                "mfe_giveback_pct": 0.3,
                "backtest": {"metrics_numeric": {"open_position": 0}},
            },
        ],
        "run_hash": run_hash,
    }


def accepted_arena(g0, g1, decision, failure):
    return {
        "schema": "tactical_validation_arena/v1",
        "family_id": "JMA",
        "parent_generation_hash": g0.generation_hash,
        "parent_candidate_hash": g0.candidate_hash,
        "child_candidate_hash": g1.candidate_hash,
        "skill_id": "RANGE_DEFENSE",
        "failure_hash": failure["failure_hash"],
        "partitions": (
            {
                "partition_id": "train",
                "role": "TRAIN",
                "adjudication": {
                    "status": "ACCEPT",
                    "decision_hash": decision["decision_hash"],
                    "survival_violations": (),
                    "improvements": tuple(decision["improvements"]),
                },
            },
            {
                "partition_id": "validation",
                "role": "VALIDATION",
                "adjudication": {"status": "PASS", "violations": ()},
            },
            {
                "partition_id": "oos",
                "role": "OOS",
                "adjudication": {"status": "PASS", "violations": ()},
            },
            {
                "partition_id": "harsh-gap",
                "role": "HARSH",
                "metadata": {"adverse_reason": "gap stress"},
                "adjudication": {"status": "PASS", "violations": ()},
            },
        ),
        "train_decision": decision,
        "holdout_failures": (),
        "decision": "ACCEPT",
        "promotion_eligible": True,
        "selection_policy": "TRAIN_ACCEPT_PLUS_ALL_HOLDOUTS_PASS_NO_HIDDEN_SCORE",
        "head_policy": "PARENT_REMAINS_HEAD_UNTIL_EXPLICIT_PROMOTION",
        "arena_hash": "arena-accepted-g1",
        "accepted_generation": g1,
    }


class TacticalEvolutionLineageTests(unittest.TestCase):
    def _seed(self, db_path: Path):
        store = TacticalEvolutionStore(db_path)
        memory = TacticalEvolutionLineage(store)
        parent = profile("G0", "candidate-g0", "run-g0")
        child = profile(
            "G1", "candidate-g1", "run-g1",
            avg=0.8, mdd=-1.7, worst=-0.8, cost=20.0,
            rate=0.6, giveback=0.8, complexity=3,
        )
        failure = TacticalFailureAnalyzer.analyze(parent)
        g0 = EvolutionGeneration.create(
            family_id="JMA",
            generation_index=0,
            profile=parent,
            capability_usage={"skills": 0, "complexity_units": 2},
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
        g1 = decision["child_generation"]

        store.record_profile("JMA", parent)
        store.record_failure("JMA", failure)
        store.record_generation(g0)
        store.record_profile("JMA", child)
        store.record_decision("JMA", decision)
        store.record_generation(g1)
        arena = accepted_arena(g0, g1, decision, failure)
        memory.record_validation("JMA", arena)
        return store, memory, g0, g1, failure, decision, arena

    def test_lineage_projects_skill_reason_validation_and_explicit_head_without_promoting(self):
        with tempfile.TemporaryDirectory() as temp:
            store, memory, g0, g1, failure, decision, _arena = self._seed(Path(temp) / "evolution.db")
            store.promote("JMA", g0.generation_hash)

            view = memory.build("JMA")
            self.assertEqual(view["schema"], "tactical_evolution_lineage/v1")
            self.assertEqual(view["projection_policy"], "READ_ONLY_APPEND_ONLY_EVIDENCE_NO_AUTOMATIC_PROMOTION")
            self.assertEqual(view["head_generation_hash"], g0.generation_hash)
            self.assertEqual(len(view["nodes"]), 2)
            self.assertTrue(view["nodes"][0]["is_head"])
            self.assertFalse(view["nodes"][1]["is_head"])
            self.assertEqual(view["nodes"][1]["new_skill"], "RANGE_DEFENSE")
            self.assertEqual(view["nodes"][1]["acquisition_evidence"]["failure_hash"], failure["failure_hash"])
            self.assertIn("WHIPSAW", view["nodes"][1]["acquisition_evidence"]["failure_tags"])
            self.assertEqual(view["nodes"][1]["acquisition_evidence"]["decision_hash"], decision["decision_hash"])
            validation = view["nodes"][1]["acquisition_evidence"]["validation"]
            self.assertEqual(validation["decision"], "ACCEPT")
            self.assertEqual(
                [row["status"] for row in validation["partitions"]],
                ["ACCEPT", "PASS", "PASS", "PASS"],
            )
            # Building the view must never silently move the family head.
            self.assertEqual(store.get_head("JMA")["generation_hash"], g0.generation_hash)

            store.promote("JMA", g1.generation_hash)
            promoted = memory.build("JMA")
            self.assertEqual(promoted["head_generation_hash"], g1.generation_hash)
            self.assertTrue(promoted["nodes"][1]["is_head"])
            self.assertNotEqual(view["lineage_hash"], promoted["lineage_hash"])

    def test_validation_evidence_is_append_only_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            _store, memory, _g0, _g1, _failure, _decision, arena = self._seed(Path(temp) / "evolution.db")
            first = memory.record_validation("JMA", arena)
            second = memory.record_validation("JMA", arena)
            self.assertEqual(first["id"], second["id"])

            broken = dict(arena)
            broken["holdout_failures"] = ("oos",)
            with self.assertRaisesRegex(ValueError, "동일 arena_hash"):
                memory.record_validation("JMA", broken)

    def test_validation_identity_and_promotion_eligibility_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            store, memory, g0, g1, failure, decision, arena = self._seed(Path(temp) / "evolution.db")
            wrong_family = dict(arena)
            wrong_family["arena_hash"] = "arena-wrong-family"
            with self.assertRaisesRegex(ValueError, "family_id"):
                memory.record_validation("OTHER", wrong_family)

            wrong_promotion = dict(arena)
            wrong_promotion["arena_hash"] = "arena-wrong-promotion"
            wrong_promotion["promotion_eligible"] = False
            with self.assertRaisesRegex(ValueError, "promotion_eligible"):
                memory.record_validation("JMA", wrong_promotion)

            rejected = {
                **arena,
                "arena_hash": "arena-rejected",
                "decision": "REJECT",
                "promotion_eligible": False,
                "accepted_generation": None,
                "holdout_failures": ("oos",),
            }
            saved = memory.record_validation("JMA", rejected)
            self.assertEqual(saved["decision"], "REJECT")
            # Rejected evidence is memory only and cannot change explicit head state.
            self.assertIsNone(store.get_head("JMA"))

    def test_lineage_hash_is_deterministic_for_same_append_only_memory(self):
        with tempfile.TemporaryDirectory() as temp:
            store, memory, g0, _g1, _failure, _decision, _arena = self._seed(Path(temp) / "evolution.db")
            store.promote("JMA", g0.generation_hash)
            first = memory.build("JMA")
            second = memory.build("JMA")
            self.assertEqual(first["lineage_hash"], second["lineage_hash"])
            self.assertEqual(first["nodes"], second["nodes"])
            self.assertEqual(first["attempts"], second["attempts"])


if __name__ == "__main__":
    unittest.main()
