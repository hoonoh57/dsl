import unittest
from pathlib import Path

from core.multi_symbol_group_evidence import GroupEvidencePolicy, GroupSnapshotPoint
from core.multi_symbol_leader_follower_relation import (
    ANALYSIS_POLICY,
    LeaderFollowerRelationPolicy,
    MultiSymbolLeaderFollowerRelationAnalyzer,
)
from core.multi_symbol_snapshot import InstrumentSignalSnapshot, SnapshotUniverse


SYMBOLS = ("A", "B", "C", "D")
TIMES = tuple(f"2026082810{minute:02d}00" for minute in range(0, 40, 5))


def snapshot(symbol, as_of, value, *, trigger=True):
    return InstrumentSignalSnapshot(
        symbol=symbol,
        as_of=as_of,
        knowledge_cutoff=as_of,
        candidate_hash=f"candidate-{symbol}",
        family_id="JMA_TREND_CROSS_RESUME_V1",
        generation_hash="generation-trusted",
        tactic_trigger=trigger,
        hard_guards_pass=True,
        locally_admissible=True,
        comparison_metrics={"lead_metric": value},
        source="fixture://lf1/snapshot",
        evidence_hash=f"evidence-{symbol}-{as_of}-{value}-{trigger}",
    )


def point(as_of, values, *, reverse=False, trigger_overrides=None):
    trigger_overrides = trigger_overrides or {}
    items = [
        snapshot(symbol, as_of, values[index], trigger=trigger_overrides.get(symbol, True))
        for index, symbol in enumerate(SYMBOLS)
    ]
    if reverse:
        items.reverse()
    return GroupSnapshotPoint(
        SnapshotUniverse(
            universe_id="SEMICONDUCTOR_GROUP",
            symbols=SYMBOLS,
            as_of=as_of,
            knowledge_cutoff=as_of,
            source_authority="FIXTURE_STATIC_POINT_IN_TIME_GROUP",
        ),
        tuple(items),
    )


def max_points(*, reverse=False):
    rows = (
        (1.00, 0.50, 0.40, 0.30),
        (1.30, 0.50, 0.40, 0.30),
        (1.30, 0.80, 0.40, 0.30),
        (1.60, 0.80, 0.70, 0.30),
        (1.60, 1.10, 0.70, 0.30),
        (1.90, 1.10, 0.70, 0.30),
        (1.90, 1.40, 1.00, 0.30),
        (2.20, 1.40, 1.00, 0.30),
    )
    return tuple(point(as_of, values, reverse=reverse) for as_of, values in zip(TIMES, rows))


def group_policy(**overrides):
    values = {
        "policy_id": "LF1_GROUP_POLICY",
        "policy_version": "v1",
        "metric_id": "lead_metric",
        "direction": "MAX",
        "favorable_threshold": 0.0,
        "leader_count": 1,
        "lookback_points": 4,
        "max_symbols": 8,
        "max_points": 32,
    }
    values.update(overrides)
    return GroupEvidencePolicy(**values)


def relation_policy(**overrides):
    values = {
        "policy_id": "LF1_RELATION_POLICY",
        "policy_version": "v1",
        "leader_impulse_threshold": 0.25,
        "follower_response_threshold": 0.25,
        "max_lag_points": 2,
        "min_observable_impulses": 2,
        "min_follow_rate": 0.60,
        "min_leader_persistence_rate": 0.75,
        "min_leader_spread": 0.20,
        "max_symbols": 8,
        "max_points": 32,
    }
    values.update(overrides)
    return LeaderFollowerRelationPolicy(**values)


class MultiSymbolLeaderFollowerRelationTests(unittest.TestCase):
    def test_explicit_leader_and_lagged_follow_rate_identify_best_follower(self):
        result = MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
            points=max_points(),
            group_policy=group_policy(),
            relation_policy=relation_policy(),
        )
        self.assertEqual(result["mode"], "OBSERVATION_ONLY")
        self.assertEqual(result["analysis_policy"], ANALYSIS_POLICY)
        self.assertFalse(result["operational_authority"])
        self.assertEqual(result["leader_symbol"], "A")
        self.assertTrue(result["leader_role_qualified"])
        self.assertEqual(result["leader_impulse_count"], 3)
        self.assertEqual(result["censored_leader_impulse_count"], 1)
        self.assertEqual(result["top_follow_rate_follower"], "B")
        self.assertEqual(result["follow_rate_leaderboard"], ("B", "C"))

        pairs = {row["follower_symbol"]: row for row in result["pairs"]}
        self.assertAlmostEqual(pairs["B"]["follow_rate"], 1.0, places=12)
        self.assertAlmostEqual(pairs["B"]["mean_lag_points"], 1.0, places=12)
        self.assertTrue(pairs["B"]["qualified"])
        self.assertAlmostEqual(pairs["C"]["follow_rate"], 2.0 / 3.0, places=12)
        self.assertAlmostEqual(pairs["C"]["mean_lag_points"], 1.5, places=12)
        self.assertTrue(pairs["C"]["qualified"])
        self.assertAlmostEqual(pairs["D"]["follow_rate"], 0.0, places=12)
        self.assertFalse(pairs["D"]["qualified"])

    def test_no_hidden_universal_score_or_execution_authority_is_emitted(self):
        result = MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
            points=max_points(),
            group_policy=group_policy(),
            relation_policy=relation_policy(),
        )
        self.assertEqual(result["selection_axis"], "FOLLOW_RATE_ONLY_EXPLICIT_NO_HIDDEN_SCORE")
        for forbidden in (
            "allowed_symbols",
            "blocked_symbols",
            "allocation",
            "entry_gate",
            "broker_order",
            "universal_score",
        ):
            self.assertNotIn(forbidden, result)

    def test_censored_tail_impulse_is_not_misclassified_as_follower_failure(self):
        result = MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
            points=max_points(),
            group_policy=group_policy(),
            relation_policy=relation_policy(),
        )
        pairs = {row["follower_symbol"]: row for row in result["pairs"]}
        self.assertEqual(result["censored_leader_impulse_count"], 1)
        self.assertEqual(pairs["B"]["observable_impulse_count"], 3)
        self.assertEqual(pairs["B"]["matched_response_count"], 3)

    def test_snapshot_input_order_does_not_change_relation_identity(self):
        first = MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
            points=max_points(reverse=False),
            group_policy=group_policy(),
            relation_policy=relation_policy(),
        )
        second = MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
            points=max_points(reverse=True),
            group_policy=group_policy(),
            relation_policy=relation_policy(),
        )
        self.assertEqual(first["result_hash"], second["result_hash"])
        self.assertEqual(first["pairs"], second["pairs"])

    def test_min_direction_normalizes_decline_as_positive_leader_and_follower_response(self):
        rows = (
            (2.00, 2.50, 3.00, 3.50),
            (1.70, 2.50, 3.00, 3.50),
            (1.70, 2.20, 3.00, 3.50),
            (1.40, 2.20, 2.70, 3.50),
            (1.40, 1.90, 2.70, 3.50),
            (1.10, 1.90, 2.70, 3.50),
            (1.10, 1.60, 2.40, 3.50),
            (0.80, 1.60, 2.40, 3.50),
        )
        points = tuple(point(as_of, values) for as_of, values in zip(TIMES, rows))
        result = MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
            points=points,
            group_policy=group_policy(direction="MIN", favorable_threshold=10.0),
            relation_policy=relation_policy(),
        )
        self.assertEqual(result["leader_symbol"], "A")
        self.assertEqual(result["top_follow_rate_follower"], "B")
        pairs = {row["follower_symbol"]: row for row in result["pairs"]}
        self.assertAlmostEqual(pairs["B"]["follow_rate"], 1.0, places=12)

    def test_v1_requires_single_explicit_leader_and_enough_points(self):
        with self.assertRaisesRegex(ValueError, "leader_count=1"):
            MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
                points=max_points(),
                group_policy=group_policy(leader_count=2),
                relation_policy=relation_policy(),
            )
        with self.assertRaisesRegex(ValueError, "충분한 point"):
            MultiSymbolLeaderFollowerRelationAnalyzer.analyze(
                points=max_points()[:4],
                group_policy=group_policy(),
                relation_policy=relation_policy(max_lag_points=2),
            )

    def test_lf1_module_has_no_execution_provider_or_network_authority(self):
        source = Path("core/multi_symbol_leader_follower_relation.py").read_text(encoding="utf-8")
        for forbidden in (
            "BacktestEngine",
            "BrokerEmulator",
            "DSLRuntime",
            "ParentFeatureProvider",
            "provider.build(",
            "broker.submit(",
            "broker.cancel(",
            "requests.",
            "sqlite3",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
