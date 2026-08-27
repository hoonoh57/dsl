import unittest
from pathlib import Path

from core.multi_symbol_group_evidence import (
    ANALYSIS_POLICY,
    GroupEvidencePolicy,
    GroupSnapshotPoint,
    MultiSymbolGroupEvidenceAnalyzer,
)
from core.multi_symbol_snapshot import InstrumentSignalSnapshot, SnapshotUniverse


SYMBOLS = ("A", "B", "C", "D")
TIMES = ("20260827100000", "20260827100500", "20260827101000")


def snapshot(symbol, as_of, value, *, trigger=True, candidate_hash=None):
    return InstrumentSignalSnapshot(
        symbol=symbol,
        as_of=as_of,
        knowledge_cutoff=as_of,
        candidate_hash=candidate_hash or f"candidate-{symbol}",
        family_id="JMA_TREND_CROSS_RESUME_V1",
        generation_hash="generation-trusted",
        tactic_trigger=trigger,
        hard_guards_pass=True,
        locally_admissible=True,
        comparison_metrics={"group_strength": value},
        source="fixture://single-instrument/snapshot",
        evidence_hash=f"evidence-{symbol}-{as_of}-{value}",
    )


def universe(as_of, symbols=SYMBOLS, universe_id="SEMICONDUCTOR_GROUP"):
    return SnapshotUniverse(
        universe_id=universe_id,
        symbols=tuple(symbols),
        as_of=as_of,
        knowledge_cutoff=as_of,
        source_authority="FIXTURE_STATIC_POINT_IN_TIME_GROUP",
    )


def point(as_of, values, *, symbols=SYMBOLS, reverse=False, candidate_override=None):
    items = [
        snapshot(
            symbol,
            as_of,
            values[index],
            candidate_hash=(candidate_override or {}).get(symbol),
        )
        for index, symbol in enumerate(symbols)
    ]
    if reverse:
        items.reverse()
    return GroupSnapshotPoint(universe(as_of, symbols=symbols), tuple(items))


def points(*, reverse=False):
    values = (
        (0.80, 0.70, 0.40, 0.20),
        (0.90, 0.85, 0.45, 0.10),
        (1.00, 0.95, 0.40, 0.20),
    )
    return tuple(point(as_of, row, reverse=reverse) for as_of, row in zip(TIMES, values))


def policy(**overrides):
    kwargs = {
        "policy_id": "MSA2_SEMICONDUCTOR_GROUP",
        "policy_version": "v1",
        "metric_id": "group_strength",
        "direction": "MAX",
        "favorable_threshold": 0.50,
        "leader_count": 1,
        "lookback_points": 3,
        "max_symbols": 8,
        "max_points": 16,
    }
    kwargs.update(overrides)
    return GroupEvidencePolicy(**kwargs)


class MultiSymbolGroupEvidenceTests(unittest.TestCase):
    def test_exact_group_evidence_reports_breadth_leader_follower_and_persistence(self):
        result = MultiSymbolGroupEvidenceAnalyzer.analyze(points=points(), policy=policy())

        self.assertEqual(result["mode"], "OBSERVATION_ONLY")
        self.assertEqual(result["analysis_policy"], ANALYSIS_POLICY)
        self.assertFalse(result["operational_authority"])
        self.assertEqual(result["point_count"], 3)
        latest = result["latest"]
        self.assertEqual(latest["leader_symbols"], ("A",))
        self.assertEqual(latest["follower_symbols"], ("B", "C", "D"))
        self.assertEqual(latest["comparison_eligible_count"], 4)
        self.assertAlmostEqual(latest["favorable_breadth_rate"], 0.5, places=12)
        self.assertAlmostEqual(latest["follower_favorable_rate"], 1.0 / 3.0, places=12)
        self.assertAlmostEqual(latest["leader_follower_spread"], 1.0 - ((0.95 + 0.40 + 0.20) / 3.0), places=12)
        self.assertEqual(latest["leader_persistence"][0]["leader_appearances"], 3)
        self.assertAlmostEqual(latest["leader_persistence"][0]["leader_persistence_rate"], 1.0, places=12)
        for forbidden in ("allowed_symbols", "blocked_symbols", "allocation", "entry_gate", "score"):
            self.assertNotIn(forbidden, result)

    def test_snapshot_input_order_does_not_change_point_or_result_identity(self):
        normal = points(reverse=False)
        reversed_snapshots = points(reverse=True)
        self.assertEqual(
            tuple(item.point_hash for item in normal),
            tuple(item.point_hash for item in reversed_snapshots),
        )
        first = MultiSymbolGroupEvidenceAnalyzer.analyze(points=normal, policy=policy())
        second = MultiSymbolGroupEvidenceAnalyzer.analyze(points=reversed_snapshots, policy=policy())
        self.assertEqual(first["result_hash"], second["result_hash"])
        self.assertEqual(first["latest"], second["latest"])

    def test_timeline_and_static_universe_topology_fail_closed(self):
        ordered = points()
        with self.assertRaisesRegex(ValueError, "오름차순"):
            MultiSymbolGroupEvidenceAnalyzer.analyze(
                points=(ordered[1], ordered[0], ordered[2]),
                policy=policy(),
            )

        changed_symbols = ("A", "B", "C", "E")
        changed = point(TIMES[1], (0.9, 0.85, 0.45, 0.3), symbols=changed_symbols)
        with self.assertRaisesRegex(ValueError, "topology"):
            MultiSymbolGroupEvidenceAnalyzer.analyze(
                points=(ordered[0], changed, ordered[2]),
                policy=policy(),
            )

    def test_tactic_identity_drift_fails_closed(self):
        first, _, third = points()
        changed = point(
            TIMES[1],
            (0.90, 0.85, 0.45, 0.10),
            candidate_override={"A": "candidate-A-new-generation"},
        )
        with self.assertRaisesRegex(ValueError, "identity drift"):
            MultiSymbolGroupEvidenceAnalyzer.analyze(
                points=(first, changed, third),
                policy=policy(),
            )

    def test_explicit_symbol_and_point_bounds_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "max_symbols"):
            MultiSymbolGroupEvidenceAnalyzer.analyze(points=points(), policy=policy(max_symbols=3))

        with self.assertRaisesRegex(ValueError, "max_points"):
            MultiSymbolGroupEvidenceAnalyzer.analyze(
                points=points(),
                policy=policy(lookback_points=2, max_points=2),
            )

    def test_min_direction_uses_explicit_favorable_semantics_and_positive_leader_spread(self):
        risk_points = tuple(
            point(as_of, row)
            for as_of, row in zip(
                TIMES,
                (
                    (0.40, 0.50, 0.80, 1.00),
                    (0.30, 0.45, 0.75, 0.95),
                    (0.20, 0.40, 0.70, 1.00),
                ),
            )
        )
        result = MultiSymbolGroupEvidenceAnalyzer.analyze(
            points=risk_points,
            policy=policy(direction="MIN", favorable_threshold=0.50, leader_count=2),
        )
        latest = result["latest"]
        self.assertEqual(latest["leader_symbols"], ("A", "B"))
        self.assertAlmostEqual(latest["favorable_breadth_rate"], 0.5, places=12)
        self.assertAlmostEqual(latest["leader_follower_spread"], ((0.70 + 1.00) / 2.0) - ((0.20 + 0.40) / 2.0), places=12)

    def test_msa2_module_has_no_execution_provider_or_network_imports(self):
        source = Path("core/multi_symbol_group_evidence.py").read_text(encoding="utf-8")
        for forbidden in (
            "BacktestEngine",
            "BrokerEmulator",
            "DSLRuntime",
            "ParentFeatureProvider",
            "provider.build(",
            "requests.",
            "sqlite3",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
