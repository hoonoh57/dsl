import unittest
from datetime import datetime, timedelta

from core.backtest import BacktestEngine
from core.dsl_parser import DSLParser
from core.tactic_family_catalog import jma_trend_cross_resume_family
from core.tactical_evolution import EvolutionGeneration
from core.tactical_failure import TacticalFailureAnalyzer
from core.tactical_skill_generator import BoundedStructuralSkillGenerator


def profile_for(candidate, *, run_hash="run-g0", case_set_hash="cases-fixed"):
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "candidate_hash": candidate.candidate_hash,
            "complexity_units": candidate.complexity_units,
            "metadata": dict(candidate.metadata),
        },
        "run_hash": run_hash,
        "case_set_hash": case_set_hash,
        "context_policy": {
            "require_neutral_context": True,
            "require_uniform_settings": True,
        },
        "aggregate": {
            "cases": 2,
            "complexity_units": candidate.complexity_units,
            "average_return_pct": -0.7,
            "median_return_pct": -0.7,
            "profitable_case_rate": 0.0,
            "worst_mdd_pct": -1.5,
            "worst_case_return_pct": -1.0,
            "total_cost": 1000.0,
            "average_mfe_giveback_pct": 0.2,
            "top1_positive_return_concentration": None,
        },
        "results": (
            {
                "case_id": "20260826:A000001",
                "return_pct": -1.0,
                "mdd_pct": -1.5,
                "trade_count": 3,
                "closed_trade_count": 3,
                "average_mae_pct": -0.8,
                "average_mfe_pct": 0.4,
                "mfe_giveback_pct": 0.2,
                "backtest": {"metrics_numeric": {"open_position": 0}},
            },
            {
                "case_id": "20260826:A000002",
                "return_pct": -0.4,
                "mdd_pct": -0.9,
                "trade_count": 3,
                "closed_trade_count": 3,
                "average_mae_pct": -0.5,
                "average_mfe_pct": 0.3,
                "mfe_giveback_pct": 0.1,
                "backtest": {"metrics_numeric": {"open_position": 0}},
            },
        ),
    }


def characterization_for(family, generation, failure, *, hash_value="char-g0"):
    return {
        "schema": "tactical_characterization/v1",
        "profile_run_hash": generation.profile_run_hash,
        "case_set_hash": generation.case_set_hash,
        "family_id": family.family_id,
        "generation_hash": generation.generation_hash,
        "characterization_hash": hash_value,
        "case_failure_analysis": failure,
        "causal_dataset_hash": "causal-fixture",
        "labeled_dataset_hash": "labels-fixture",
        "feature_strata": {},
    }


def market_5m():
    start = datetime(2026, 8, 27, 9, 0, 0)
    time = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    previous = 100.0
    for index in range(90):
        stamp = start + timedelta(minutes=5 * index)
        wave = ((index % 10) - 4.5) * 0.12
        current = 100.0 + index * 0.04 + wave
        time.append(stamp.strftime("%Y%m%d%H%M%S"))
        open_.append(previous)
        close.append(current)
        high.append(max(previous, current) + 0.25)
        low.append(min(previous, current) - 0.25)
        volume.append(1000.0 + index * 10.0)
        previous = current
    return {
        "time": time,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "_meta": {
            "source": "test://skill-generator",
            "instrument": "A000001",
            "timeframe": "5m",
        },
    }


class BoundedStructuralSkillGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.family = jma_trend_cross_resume_family()
        self.parent = self.family.base_candidate()
        self.profile = profile_for(self.parent)
        self.generation = EvolutionGeneration.create(
            family_id=self.family.family_id,
            generation_index=0,
            profile=self.profile,
            capability_usage=self.family.normalized_base_usage(),
        )
        self.failure = TacticalFailureAnalyzer.analyze(self.profile)
        self.characterization = characterization_for(
            self.family,
            self.generation,
            self.failure,
        )

    def test_only_currently_legal_registered_skills_are_proposed_without_ranking(self):
        result = BoundedStructuralSkillGenerator.propose(
            family=self.family,
            parent_generation=self.generation,
            parent_candidate=self.parent,
            failure_report=self.failure,
            characterization=self.characterization,
        )
        self.assertEqual(result["schema"], "tactical_skill_generator/v1")
        self.assertEqual(
            result["legal_skill_ids"],
            ("JMA_RANGE_COOLDOWN", "JMA_ADX_ENTRY_QUALITY"),
        )
        self.assertEqual(
            [row["skill_id"] for row in result["proposals"]],
            ["JMA_RANGE_COOLDOWN", "JMA_ADX_ENTRY_QUALITY"],
        )
        self.assertEqual(
            result["selection_policy"],
            "LEGAL_REGISTERED_SKILLS_ONLY_NO_AUTOMATIC_RANKING",
        )
        self.assertEqual(
            result["promotion_policy"],
            "PROPOSAL_ONLY_REQUIRES_REPLAY_AND_EVOLUTION_ARENA",
        )
        self.assertNotIn("score", result)
        self.assertNotIn("best", result)
        self.assertNotIn("decision", result)

    def test_range_child_preserves_parent_structure_and_exposes_only_declared_numeric_input(self):
        result = BoundedStructuralSkillGenerator.propose(
            family=self.family,
            parent_generation=self.generation,
            parent_candidate=self.parent,
            failure_report=self.failure,
            characterization=self.characterization,
            requested_skill_id="JMA_RANGE_COOLDOWN",
        )
        proposal = result["proposals"][0]
        candidate = BoundedStructuralSkillGenerator.materialize_candidate(proposal)
        DSLParser.parse(candidate.dsl_code)
        self.assertIn("input cooldown_bars = 10", candidate.dsl_code)
        self.assertIn("cooldown_ok = ta.bars_since(ta.crossunder(fast, slow)) > cooldown_bars", candidate.dsl_code)
        self.assertIn("and (cooldown_ok)", candidate.dsl_code)
        self.assertNotIn("adx_length", candidate.dsl_code)
        self.assertEqual(
            proposal["parameter_manifest"]["cooldown_bars"],
            {"type": "int", "min": 1, "max": 30, "default": 10, "target": "dsl"},
        )
        self.assertEqual(candidate.metadata["proposed_skill_id"], "JMA_RANGE_COOLDOWN")
        self.assertEqual(candidate.metadata["mutation_policy"], "ONE_REGISTERED_SKILL_ONLY")
        # Generated DSL must reach the trusted semantic/backtest path without a
        # hidden renderer-only language extension.
        result_bt = BacktestEngine.run(candidate.dsl_code, market=market_5m(), data_timeframe="5m")
        self.assertIn("metrics_numeric", result_bt)

    def test_dependency_skill_becomes_legal_only_after_required_parent_skill_is_acquired(self):
        first = BoundedStructuralSkillGenerator.propose(
            family=self.family,
            parent_generation=self.generation,
            parent_candidate=self.parent,
            failure_report=self.failure,
            characterization=self.characterization,
            requested_skill_id="JMA_RANGE_COOLDOWN",
        )
        range_proposal = first["proposals"][0]
        range_candidate = BoundedStructuralSkillGenerator.materialize_candidate(range_proposal)
        g1_profile = profile_for(range_candidate, run_hash="run-g1")
        g1 = EvolutionGeneration.create(
            family_id=self.family.family_id,
            generation_index=1,
            profile=g1_profile,
            acquired_skills=("JMA_RANGE_COOLDOWN",),
            capability_usage=range_proposal["projected_capability_usage"],
            parent_generation_hash=self.generation.generation_hash,
            acquired_from_failure_hash=self.failure["failure_hash"],
        )
        g1_failure = TacticalFailureAnalyzer.analyze(g1_profile)
        g1_characterization = characterization_for(
            self.family,
            g1,
            g1_failure,
            hash_value="char-g1",
        )
        next_result = BoundedStructuralSkillGenerator.propose(
            family=self.family,
            parent_generation=g1,
            parent_candidate=range_candidate,
            failure_report=g1_failure,
            characterization=g1_characterization,
            requested_skill_id="JMA_CONFIRM_AFTER_RANGE",
        )
        confirm = BoundedStructuralSkillGenerator.materialize_candidate(next_result["proposals"][0])
        self.assertIn("cooldown_ok", confirm.dsl_code)
        self.assertIn("input confirm_bars = 2", confirm.dsl_code)
        self.assertIn("range_confirmed = state.persist(fast > slow and close > fast, confirm_bars)", confirm.dsl_code)
        self.assertIn("and (range_confirmed)", confirm.dsl_code)
        BacktestEngine.run(confirm.dsl_code, market=market_5m(), data_timeframe="5m")

    def test_illegal_dependency_skill_and_mismatched_characterization_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "legal"):
            BoundedStructuralSkillGenerator.propose(
                family=self.family,
                parent_generation=self.generation,
                parent_candidate=self.parent,
                failure_report=self.failure,
                characterization=self.characterization,
                requested_skill_id="JMA_CONFIRM_AFTER_RANGE",
            )

        broken = dict(self.characterization)
        broken["generation_hash"] = "wrong-generation"
        with self.assertRaisesRegex(ValueError, "generation_hash"):
            BoundedStructuralSkillGenerator.propose(
                family=self.family,
                parent_generation=self.generation,
                parent_candidate=self.parent,
                failure_report=self.failure,
                characterization=broken,
            )

    def test_generator_identity_is_deterministic(self):
        kwargs = dict(
            family=self.family,
            parent_generation=self.generation,
            parent_candidate=self.parent,
            failure_report=self.failure,
            characterization=self.characterization,
        )
        first = BoundedStructuralSkillGenerator.propose(**kwargs)
        second = BoundedStructuralSkillGenerator.propose(**kwargs)
        self.assertEqual(first["generator_hash"], second["generator_hash"])
        self.assertEqual(
            [row["proposal_hash"] for row in first["proposals"]],
            [row["proposal_hash"] for row in second["proposals"]],
        )
        self.assertEqual(
            [row["candidate"]["candidate_hash"] for row in first["proposals"]],
            [row["candidate"]["candidate_hash"] for row in second["proposals"]],
        )


if __name__ == "__main__":
    unittest.main()
