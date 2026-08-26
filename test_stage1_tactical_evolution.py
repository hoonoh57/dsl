import unittest

from core.tactical_evolution import (
    CapabilityBudget,
    EvolutionArena,
    EvolutionGeneration,
    PromotionContract,
    SkillSpec,
)
from core.tactical_failure import FailureAnalysisPolicy, TacticalFailureAnalyzer


def profile(candidate_id, candidate_hash, run_hash, *, case_set="battle-set", avg=0.4,
            median=0.2, rate=0.5, mdd=-2.5, worst=-1.5, cost=40.0,
            giveback=1.8, concentration=0.45, complexity=2, results=None):
    if results is None:
        results = [
            {
                "case_id": "A",
                "return_pct": -1.0,
                "mdd_pct": -2.5,
                "profit_factor": 0.5,
                "closed_trade_count": 4,
                "total_cost": 15.0,
                "average_mfe_pct": 1.8,
                "average_mae_pct": -1.2,
                "mfe_giveback_pct": 2.8,
            },
            {
                "case_id": "B",
                "return_pct": 1.8,
                "mdd_pct": -0.8,
                "profit_factor": 2.0,
                "closed_trade_count": 1,
                "total_cost": 10.0,
                "average_mfe_pct": 2.2,
                "average_mae_pct": -0.5,
                "mfe_giveback_pct": 0.4,
            },
            {
                "case_id": "C",
                "return_pct": 0.0,
                "mdd_pct": 0.0,
                "profit_factor": 0.0,
                "closed_trade_count": 0,
                "total_cost": 0.0,
                "average_mfe_pct": 0.0,
                "average_mae_pct": 0.0,
                "mfe_giveback_pct": 0.0,
            },
        ]
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {
            "candidate_id": candidate_id,
            "candidate_hash": candidate_hash,
            "complexity_units": complexity,
        },
        "case_set_hash": case_set,
        "context_policy": {
            "require_neutral_context": True,
            "require_uniform_settings": True,
        },
        "aggregate": {
            "cases": 3,
            "active_cases": 2,
            "no_trade_cases": 1,
            "profitable_cases": 1,
            "losing_cases": 1,
            "profitable_case_rate": rate,
            "average_return_pct": avg,
            "median_return_pct": median,
            "worst_case_return_pct": worst,
            "worst_mdd_pct": mdd,
            "total_cost": cost,
            "average_mfe_giveback_pct": giveback,
            "top1_positive_return_concentration": concentration,
            "complexity_units": complexity,
        },
        "results": results,
        "run_hash": run_hash,
    }


class TacticalEvolutionTests(unittest.TestCase):
    def setUp(self):
        self.parent = profile("G0", "candidate-g0", "run-g0")
        self.failure = TacticalFailureAnalyzer.analyze(
            self.parent,
            FailureAnalysisPolicy(whipsaw_min_closed_trades=3, giveback_threshold_pct=1.0),
        )
        self.g0 = EvolutionGeneration.create(
            family_id="JMA_WARRIOR",
            generation_index=0,
            profile=self.parent,
            capability_usage={
                "skills": 0,
                "complexity_units": 2,
                "indicators": 2,
                "parameters": 4,
                "state_variables": 0,
                "branches": 2,
                "setup_variants": 1,
            },
        )
        self.range_skill = SkillSpec(
            skill_id="RANGE_DEFENSE_V1",
            capability="RANGE_DEFENSE",
            implementation="crossover-density cooldown",
            addresses_failure_tags=("WHIPSAW",),
            cost={"complexity_units": 1, "parameters": 1, "state_variables": 1, "branches": 1},
        )

    def test_failure_analysis_treats_no_trade_as_abstention_not_failure(self):
        tags = {row["failure_tag"] for row in self.failure["clusters"]}
        self.assertIn("WHIPSAW", tags)
        self.assertIn("MFE_GIVEBACK", tags)
        self.assertEqual(self.failure["no_trade_cases"], ("C",))
        self.assertEqual(self.failure["no_trade_policy"], "ABSTENTION_IS_NOT_FAILURE_BY_DEFAULT")

    def test_one_skill_upgrade_accepts_only_same_battlefield_with_survival_preserved(self):
        child = profile(
            "G1", "candidate-g1", "run-g1",
            avg=0.9, median=0.5, rate=0.6, mdd=-2.0, worst=-1.2,
            cost=30.0, giveback=1.0, concentration=0.40, complexity=3,
        )
        decision = EvolutionArena.evaluate_upgrade(
            parent_generation=self.g0,
            parent_profile=self.parent,
            child_profile=child,
            skill=self.range_skill,
            failure_report=self.failure,
            budget=CapabilityBudget(),
        )
        self.assertEqual(decision["decision"], "ACCEPT")
        self.assertEqual(decision["promotion_policy"], "ONE_SKILL_EVIDENCE_GATED_NO_HIDDEN_SCORE")
        generation = decision["child_generation"]
        self.assertEqual(generation.generation_index, 1)
        self.assertEqual(generation.acquired_skills, ("RANGE_DEFENSE_V1",))
        self.assertEqual(generation.parent_generation_hash, self.g0.generation_hash)
        self.assertEqual(generation.acquired_from_failure_hash, self.failure["failure_hash"])

    def test_survival_regression_prevents_auto_promotion_even_if_average_return_rises(self):
        child = profile(
            "HOT_BUT_FRAGILE", "candidate-hot", "run-hot",
            avg=2.0, median=0.8, rate=0.6, mdd=-5.0, worst=-3.5,
            cost=30.0, giveback=1.0, concentration=0.40, complexity=3,
        )
        decision = EvolutionArena.evaluate_upgrade(
            parent_generation=self.g0,
            parent_profile=self.parent,
            child_profile=child,
            skill=self.range_skill,
            failure_report=self.failure,
            budget=CapabilityBudget(),
        )
        self.assertEqual(decision["decision"], "REVIEW")
        self.assertIn("worst_mdd_pct", decision["survival_violations"])
        self.assertIn("worst_case_return_pct", decision["survival_violations"])
        self.assertNotIn("child_generation", decision)

    def test_skill_must_address_observed_failure(self):
        irrelevant = SkillSpec(
            skill_id="OPENING_ATTACK",
            capability="OPENING_ATTACK",
            implementation="early impulse entry",
            addresses_failure_tags=("LATE_ENTRY",),
            cost={"complexity_units": 1},
        )
        child = profile("G1", "candidate-g1", "run-g1", complexity=3)
        with self.assertRaisesRegex(ValueError, "관찰된 failure"):
            EvolutionArena.evaluate_upgrade(
                parent_generation=self.g0,
                parent_profile=self.parent,
                child_profile=child,
                skill=irrelevant,
                failure_report=self.failure,
                budget=CapabilityBudget(),
            )

    def test_personal_arsenal_budget_rejects_heavy_upgrade(self):
        heavy = SkillSpec(
            skill_id="HEAVY_SYSTEM",
            capability="RANGE_DEFENSE",
            implementation="oversized multi-state defense",
            addresses_failure_tags=("WHIPSAW",),
            cost={"complexity_units": 20, "parameters": 20, "state_variables": 20},
        )
        child = profile("G1", "candidate-heavy", "run-heavy", complexity=22)
        with self.assertRaisesRegex(ValueError, "CapabilityBudget"):
            EvolutionArena.evaluate_upgrade(
                parent_generation=self.g0,
                parent_profile=self.parent,
                child_profile=child,
                skill=heavy,
                failure_report=self.failure,
                budget=CapabilityBudget(),
            )

    def test_child_cannot_change_frozen_battlecase_set(self):
        child = profile("G1", "candidate-g1", "run-g1", case_set="easier-cases", complexity=3)
        with self.assertRaisesRegex(ValueError, "case_set_hash"):
            EvolutionArena.evaluate_upgrade(
                parent_generation=self.g0,
                parent_profile=self.parent,
                child_profile=child,
                skill=self.range_skill,
                failure_report=self.failure,
                budget=CapabilityBudget(),
            )

    def test_declared_tolerance_can_route_tradeoff_to_accept_only_when_survival_contract_allows_it(self):
        child = profile(
            "G1", "candidate-g1", "run-g1",
            avg=1.2, median=0.6, rate=0.5, mdd=-2.7, worst=-1.6,
            cost=40.0, giveback=1.2, concentration=0.45, complexity=3,
        )
        decision = EvolutionArena.evaluate_upgrade(
            parent_generation=self.g0,
            parent_profile=self.parent,
            child_profile=child,
            skill=self.range_skill,
            failure_report=self.failure,
            budget=CapabilityBudget(),
            contract=PromotionContract(
                max_worst_mdd_regression_pct=0.3,
                max_worst_case_regression_pct=0.11,
            ),
        )
        self.assertEqual(decision["decision"], "ACCEPT")


if __name__ == "__main__":
    unittest.main()
