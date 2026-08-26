import unittest
from dataclasses import replace

from core.backtest import BacktestEngine
from core.tactic_family import TacticFamilySpec
from core.tactic_family_catalog import (
    JMA_TREND_CROSS_RESUME_V1,
    build_default_tactic_family_registry,
    jma_trend_cross_resume_family,
)
from core.tactical_evolution import EvolutionGeneration, SkillSpec


def profile(run_hash="run-jma"):
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {
            "candidate_id": "JMA_TCR_G0",
            "candidate_hash": "candidate-jma-g0",
            "complexity_units": 3,
        },
        "case_set_hash": "frozen-korean-regular-session-cases",
        "context_policy": {
            "require_neutral_context": True,
            "require_uniform_settings": True,
        },
        "aggregate": {
            "cases": 3,
            "profitable_case_rate": 0.3333333333,
            "average_return_pct": -0.1,
            "median_return_pct": -0.2,
            "worst_case_return_pct": -1.0,
            "worst_mdd_pct": -2.0,
            "total_cost": 12.0,
            "average_mfe_giveback_pct": 1.4,
            "top1_positive_return_concentration": 1.0,
            "complexity_units": 3,
        },
        "results": [],
        "run_hash": run_hash,
    }


def failure(run_hash, *tags):
    return {
        "schema": "tactical_failure/v1",
        "profile_run_hash": run_hash,
        "clusters": tuple({"failure_tag": tag} for tag in tags),
    }


def usage_after(family, *skill_ids):
    usage = family.normalized_base_usage()
    for skill_id in skill_ids:
        skill = family.skill(skill_id)
        usage["skills"] = int(usage.get("skills", 0)) + 1
        for key, value in skill.cost.items():
            usage[key] = int(usage.get(key, 0)) + int(value)
    return usage


class TacticFamilyCatalogTests(unittest.TestCase):
    def test_default_registry_contains_only_first_validated_jma_family(self):
        registry = build_default_tactic_family_registry()
        self.assertEqual(registry.list_ids(), (JMA_TREND_CROSS_RESUME_V1,))
        family = registry.get(JMA_TREND_CROSS_RESUME_V1)
        family.validate()
        self.assertEqual(family.metadata["mutation_policy"], "one-skill-only")
        self.assertEqual(family.normalized_base_usage()["skills"], 0)

    def test_jma_base_dsl_executes_through_trusted_backtest_boundary(self):
        family = jma_trend_cross_resume_family()
        result = BacktestEngine.run(family.base_dsl, bars_count=500)
        self.assertIn("metrics", result)
        self.assertTrue(family.base_candidate().candidate_hash)

    def test_generation_zero_legal_skills_are_failure_relevant_and_prerequisite_safe(self):
        family = jma_trend_cross_resume_family()
        parent = profile()
        generation = EvolutionGeneration.create(
            family_id=family.family_id,
            generation_index=0,
            profile=parent,
            capability_usage=family.normalized_base_usage(),
        )
        legal = family.legal_skills(
            generation=generation,
            failure_report=failure(
                parent["run_hash"], "WHIPSAW", "LOSS", "MFE_GIVEBACK"
            ),
        )
        ids = tuple(item.skill_id for item in legal)
        self.assertEqual(
            ids,
            (
                "JMA_RANGE_COOLDOWN",
                "JMA_ADX_ENTRY_QUALITY",
                "JMA_FAST_PROFIT_PROTECTION",
            ),
        )
        self.assertNotIn("JMA_CONFIRM_AFTER_RANGE", ids)

    def test_confirmation_skill_unlocks_only_after_range_defense_is_acquired(self):
        family = jma_trend_cross_resume_family()
        parent = profile("run-jma-g1")
        generation = EvolutionGeneration.create(
            family_id=family.family_id,
            generation_index=1,
            profile=parent,
            acquired_skills=("JMA_RANGE_COOLDOWN",),
            capability_usage=usage_after(family, "JMA_RANGE_COOLDOWN"),
            parent_generation_hash="parent-generation",
            acquired_from_failure_hash="parent-failure",
        )
        legal = family.legal_skills(
            generation=generation,
            failure_report=failure(parent["run_hash"], "LOSS", "SEVERE_LOSS", "WHIPSAW"),
        )
        ids = tuple(item.skill_id for item in legal)
        self.assertIn("JMA_CONFIRM_AFTER_RANGE", ids)
        self.assertNotIn("JMA_RANGE_COOLDOWN", ids)

    def test_skill_dependency_cycle_fails_closed(self):
        family = jma_trend_cross_resume_family()
        first = SkillSpec(
            skill_id="A",
            capability="A",
            implementation="a",
            addresses_failure_tags=("LOSS",),
            metadata={"requires_skills": ("B",)},
        )
        second = SkillSpec(
            skill_id="B",
            capability="B",
            implementation="b",
            addresses_failure_tags=("LOSS",),
            metadata={"requires_skills": ("A",)},
        )
        bad = TacticFamilySpec(
            family_id="BAD_CYCLE",
            base_candidate_id=family.base_candidate_id,
            base_dsl=family.base_dsl,
            base_complexity_units=family.base_complexity_units,
            budget=family.budget,
            base_usage=family.base_usage,
            skills=(first, second),
        )
        with self.assertRaisesRegex(ValueError, "cycle"):
            bad.validate()

    def test_unknown_dependency_fails_closed(self):
        family = jma_trend_cross_resume_family()
        bad_skill = replace(
            family.skills[0],
            metadata={**dict(family.skills[0].metadata), "requires_skills": ("MISSING",)},
        )
        bad = replace(family, skills=(bad_skill,) + family.skills[1:])
        with self.assertRaisesRegex(ValueError, "알 수 없는 skill"):
            bad.validate()


if __name__ == "__main__":
    unittest.main()
