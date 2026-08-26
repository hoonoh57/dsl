import unittest

from core.tactic_family import TacticFamilyRegistry, TacticFamilySpec
from core.tactical_evolution import CapabilityBudget, EvolutionGeneration, SkillSpec
from core.tactical_failure import TacticalFailureAnalyzer


DSL = '''strategy "Base" {
    timeframe = "5m"
    long_entry = close > open
    long_exit = close < open
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def profile():
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {"candidate_id": "BASE", "candidate_hash": "candidate-base", "complexity_units": 2},
        "case_set_hash": "cases",
        "context_policy": {"require_neutral_context": True, "require_uniform_settings": True},
        "aggregate": {
            "cases": 2,
            "profitable_case_rate": 0.5,
            "average_return_pct": 0.1,
            "median_return_pct": 0.1,
            "worst_case_return_pct": -1.0,
            "worst_mdd_pct": -2.0,
            "total_cost": 10.0,
            "average_mfe_giveback_pct": 1.5,
            "top1_positive_return_concentration": 0.5,
            "complexity_units": 2,
        },
        "results": [
            {"case_id": "A", "return_pct": -1.0, "mdd_pct": -2.0, "profit_factor": 0.5,
             "closed_trade_count": 4, "total_cost": 8.0, "average_mfe_pct": 1.0,
             "average_mae_pct": -1.0, "mfe_giveback_pct": 2.0},
            {"case_id": "B", "return_pct": 1.2, "mdd_pct": -0.5, "profit_factor": 2.0,
             "closed_trade_count": 1, "total_cost": 2.0, "average_mfe_pct": 1.5,
             "average_mae_pct": -0.2, "mfe_giveback_pct": 0.2},
        ],
        "run_hash": "run-base",
    }


class TacticFamilyTests(unittest.TestCase):
    def family(self):
        return TacticFamilySpec(
            family_id="JMA_BASE",
            base_candidate_id="BASE",
            base_dsl=DSL,
            base_complexity_units=2,
            budget=CapabilityBudget(max_skills=2, max_complexity_units=4, max_parameters=6),
            base_usage={"skills": 0, "complexity_units": 2, "indicators": 2, "parameters": 4},
            skills=(
                SkillSpec(
                    skill_id="RANGE_DEFENSE",
                    capability="RANGE_DEFENSE",
                    implementation="cooldown",
                    addresses_failure_tags=("WHIPSAW",),
                    cost={"complexity_units": 1, "parameters": 1},
                ),
                SkillSpec(
                    skill_id="HEAVY_DEFENSE",
                    capability="RANGE_DEFENSE",
                    implementation="too many knobs",
                    addresses_failure_tags=("WHIPSAW",),
                    cost={"complexity_units": 3, "parameters": 5},
                ),
                SkillSpec(
                    skill_id="OPENING_ATTACK",
                    capability="OPENING_OPPORTUNITY",
                    implementation="opening impulse",
                    addresses_failure_tags=("LATE_ENTRY",),
                    cost={"complexity_units": 1},
                ),
            ),
        )

    def test_legal_skills_require_observed_failure_and_remaining_budget(self):
        family = self.family()
        parent_profile = profile()
        failure = TacticalFailureAnalyzer.analyze(parent_profile)
        generation = EvolutionGeneration.create(
            family_id=family.family_id,
            generation_index=0,
            profile=parent_profile,
            capability_usage=family.normalized_base_usage(),
        )
        legal = family.legal_skills(generation=generation, failure_report=failure)
        self.assertEqual([item.skill_id for item in legal], ["RANGE_DEFENSE"])

    def test_base_candidate_carries_family_identity(self):
        candidate = self.family().base_candidate()
        self.assertEqual(candidate.metadata["family_id"], "JMA_BASE")
        self.assertEqual(candidate.complexity_units, 2)

    def test_registry_rejects_duplicate_family(self):
        family = self.family()
        registry = TacticFamilyRegistry((family,))
        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(family)


if __name__ == "__main__":
    unittest.main()
