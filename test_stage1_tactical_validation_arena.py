import unittest
from datetime import datetime, timedelta

from core.tactical_discovery import BattleCase, TacticCandidate, TacticalDiscoveryEngine
from core.tactical_evolution import CapabilityBudget, EvolutionGeneration, SkillSpec
from core.tactical_failure import TacticalFailureAnalyzer
from core.tactical_validation_arena import (
    HoldoutContract,
    TacticalValidationArena,
    ValidationPartition,
)


PARENT_DSL = '''strategy "ArenaParent" {
    timeframe = "5m"
    long_entry = true
    long_exit = close < open
    short_entry = false
    short_exit = false
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''

CHILD_DSL = '''strategy "ArenaChild" {
    timeframe = "5m"
    long_entry = false
    long_exit = close < open
    short_entry = false
    short_exit = false
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def falling_market(symbol: str, session_date: str) -> dict:
    start = datetime.strptime(session_date + "090000", "%Y%m%d%H%M%S")
    time = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    previous = 100.0
    for index in range(16):
        stamp = start + timedelta(minutes=5 * index)
        current = 100.0 - (index + 1) * 0.5
        time.append(stamp.strftime("%Y%m%d%H%M%S"))
        open_.append(previous)
        close.append(current)
        high.append(max(previous, current) + 0.1)
        low.append(min(previous, current) - 0.1)
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
            "source": "test://validation-arena",
            "instrument": symbol,
            "timeframe": "5m",
        },
    }


def battle(case_id: str, symbol: str, session_date: str) -> BattleCase:
    return BattleCase(
        case_id=case_id,
        symbol=symbol,
        session_date=session_date,
        market=falling_market(symbol, session_date),
        settings={"signal_mode": "bar_close", "total_capital": 100000.0},
        knowledge_cutoff=session_date + "101500",
        metadata={"fixture_only": True},
    )


class TacticalValidationArenaTests(unittest.TestCase):
    def setUp(self):
        self.train_case = battle("TRAIN:A", "A000001", "20260820")
        self.parent = TacticCandidate(
            "ARENA_PARENT",
            PARENT_DSL,
            complexity_units=1,
            metadata={"family_id": "ARENA_FIXTURE"},
        )
        self.train_parent_profile = TacticalDiscoveryEngine.evaluate(
            candidate=self.parent,
            cases=(self.train_case,),
            max_workers=1,
        )
        self.generation = EvolutionGeneration.create(
            family_id="ARENA_FIXTURE",
            generation_index=0,
            profile=self.train_parent_profile,
            capability_usage={
                "skills": 0,
                "complexity_units": 1,
                "indicators": 0,
                "parameters": 0,
                "state_variables": 0,
                "branches": 1,
                "setup_variants": 1,
            },
        )
        self.failure = TacticalFailureAnalyzer.analyze(self.train_parent_profile)
        self.skill = SkillSpec(
            skill_id="SKIP_LOSSES",
            capability="ENGAGEMENT_DISCIPLINE",
            implementation="fixture-only abstention child",
            addresses_failure_tags=("LOSS",),
            cost={},
        )
        self.child = TacticCandidate(
            "ARENA_CHILD",
            CHILD_DSL,
            complexity_units=1,
            metadata={
                "family_id": "ARENA_FIXTURE",
                "parent_generation_hash": self.generation.generation_hash,
                "proposed_skill_id": self.skill.skill_id,
                "mutation_policy": "ONE_REGISTERED_SKILL_ONLY",
                "failure_hash": self.failure["failure_hash"],
            },
        )
        self.budget = CapabilityBudget(
            max_skills=1,
            max_complexity_units=2,
            max_indicators=1,
            max_parameters=1,
            max_state_variables=1,
            max_branches=2,
            max_setup_variants=1,
        )
        self.partitions = (
            ValidationPartition("train", "TRAIN", (self.train_case,)),
            ValidationPartition(
                "validation",
                "VALIDATION",
                (battle("VAL:A", "A000002", "20260821"),),
            ),
            ValidationPartition(
                "oos",
                "OOS",
                (battle("OOS:A", "A000003", "20260822"),),
            ),
            ValidationPartition(
                "harsh-downtrend",
                "HARSH",
                (battle("HARSH:A", "A000004", "20260823"),),
                metadata={"adverse_reason": "persistent falling-session fixture"},
            ),
        )

    def run_arena(self, **overrides):
        kwargs = dict(
            parent_generation=self.generation,
            parent_candidate=self.parent,
            child_candidate=self.child,
            skill=self.skill,
            failure_report=self.failure,
            budget=self.budget,
            partitions=self.partitions,
            max_workers=2,
        )
        kwargs.update(overrides)
        return TacticalValidationArena.run(**kwargs)

    def test_default_holdout_blocks_total_engagement_collapse(self):
        result = self.run_arena()
        self.assertEqual(result["schema"], "tactical_validation_arena/v1")
        self.assertEqual(result["train_decision"]["decision"], "ACCEPT")
        self.assertEqual(result["decision"], "REJECT")
        self.assertFalse(result["promotion_eligible"])
        self.assertEqual(
            result["holdout_failures"],
            ("validation", "oos", "harsh-downtrend"),
        )
        for row in result["partitions"]:
            if row["role"] != "TRAIN":
                self.assertIn("engagement_collapse", row["adjudication"]["violations"])

    def test_explicit_abstention_policy_can_accept_without_hidden_score_or_auto_head_change(self):
        result = self.run_arena(
            holdout_contract=HoldoutContract(require_child_activity_if_parent_active=False)
        )
        self.assertEqual(result["decision"], "ACCEPT")
        self.assertTrue(result["promotion_eligible"])
        self.assertIn("accepted_generation", result)
        self.assertEqual(result["accepted_generation"].generation_index, 1)
        self.assertEqual(
            result["selection_policy"],
            "TRAIN_ACCEPT_PLUS_ALL_HOLDOUTS_PASS_NO_HIDDEN_SCORE",
        )
        self.assertEqual(
            result["head_policy"],
            "PARENT_REMAINS_HEAD_UNTIL_EXPLICIT_PROMOTION",
        )
        self.assertNotIn("score", result)
        self.assertNotIn("best", result)
        self.assertNotIn("head_generation", result)
        self.assertTrue(
            all(
                row["adjudication"]["status"] in {"ACCEPT", "PASS"}
                for row in result["partitions"]
            )
        )

    def test_partition_order_and_worker_count_do_not_change_arena_identity(self):
        contract = HoldoutContract(require_child_activity_if_parent_active=False)
        one = self.run_arena(
            holdout_contract=contract,
            partitions=tuple(reversed(self.partitions)),
            max_workers=1,
        )
        many = self.run_arena(
            holdout_contract=contract,
            partitions=self.partitions,
            max_workers=3,
        )
        self.assertEqual(one["arena_hash"], many["arena_hash"])
        self.assertEqual(
            [row["partition_id"] for row in one["partitions"]],
            ["train", "validation", "oos", "harsh-downtrend"],
        )
        self.assertEqual(
            [row["partition_hash"] for row in one["partitions"]],
            [row["partition_hash"] for row in many["partitions"]],
        )

    def test_partitions_are_explicit_disjoint_and_harsh_requires_reason(self):
        without_harsh = self.partitions[:-1]
        with self.assertRaisesRegex(ValueError, "HARSH"):
            self.run_arena(partitions=without_harsh)

        duplicate = ValidationPartition(
            "harsh-overlap",
            "HARSH",
            (self.train_case,),
            metadata={"adverse_reason": "intentional overlap should fail in v1"},
        )
        with self.assertRaisesRegex(ValueError, "전역적으로"):
            self.run_arena(partitions=(*self.partitions[:-1], duplicate))

        no_reason = ValidationPartition(
            "harsh-no-reason",
            "HARSH",
            (battle("HARSH:B", "A000005", "20260824"),),
        )
        with self.assertRaisesRegex(ValueError, "adverse_reason"):
            self.run_arena(partitions=(*self.partitions[:-1], no_reason))

    def test_child_provenance_mismatch_fails_closed(self):
        broken = TacticCandidate(
            "BROKEN_CHILD",
            CHILD_DSL,
            complexity_units=1,
            metadata={
                **dict(self.child.metadata),
                "proposed_skill_id": "OTHER_SKILL",
            },
        )
        with self.assertRaisesRegex(ValueError, "proposed_skill_id"):
            self.run_arena(child_candidate=broken)


if __name__ == "__main__":
    unittest.main()
