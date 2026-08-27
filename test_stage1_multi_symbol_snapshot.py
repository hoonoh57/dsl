import unittest
from pathlib import Path

from core.multi_symbol_snapshot import (
    ANALYSIS_POLICY,
    InstrumentSignalSnapshot,
    MultiSymbolSnapshotAnalyzer,
    SnapshotAnalysisPolicy,
    SnapshotComparisonAxis,
    SnapshotUniverse,
)


AS_OF = "20260827101500"


def snapshot(
    symbol,
    *,
    setup_quality,
    risk_pct,
    trigger=True,
    guards=True,
    admissible=True,
    as_of=AS_OF,
    evidence_suffix="v1",
):
    return InstrumentSignalSnapshot(
        symbol=symbol,
        as_of=as_of,
        knowledge_cutoff=as_of,
        candidate_hash=f"candidate-{symbol}",
        family_id="JMA_TREND_CROSS_RESUME_V1",
        generation_hash="generation-trusted",
        tactic_trigger=trigger,
        hard_guards_pass=guards,
        locally_admissible=admissible,
        comparison_metrics={
            "setup_quality": setup_quality,
            "risk_pct": risk_pct,
        },
        source="fixture://single-instrument/signal",
        evidence_hash=f"evidence-{symbol}-{evidence_suffix}",
        metadata={"export_policy": "POINT_IN_TIME_ONLY"},
    )


def universe(symbols=("A", "B", "C"), *, as_of=AS_OF):
    return SnapshotUniverse(
        universe_id="SEMICONDUCTOR_COHORT_1015",
        symbols=tuple(symbols),
        as_of=as_of,
        knowledge_cutoff=as_of,
        source_authority="FIXTURE_POINT_IN_TIME_COHORT",
    )


def policy():
    return SnapshotAnalysisPolicy(
        policy_id="MSA1_PARETO_FIXTURE",
        policy_version="v1",
        axes=(
            SnapshotComparisonAxis("setup_quality", "MAX"),
            SnapshotComparisonAxis("risk_pct", "MIN"),
        ),
    )


class MultiSymbolSnapshotTests(unittest.TestCase):
    def test_snapshot_identity_is_deterministic_and_changes_with_causal_evidence(self):
        first = snapshot("A", setup_quality=0.8, risk_pct=1.2)
        same = snapshot("A", setup_quality=0.8, risk_pct=1.2)
        changed = snapshot("A", setup_quality=0.81, risk_pct=1.2)

        self.assertEqual(first.snapshot_hash, same.snapshot_hash)
        self.assertNotEqual(first.snapshot_hash, changed.snapshot_hash)
        self.assertEqual(first.public_dict()["causality_policy"], "POINT_IN_TIME_ONLY")

    def test_observation_only_analysis_has_per_axis_leaderboards_and_pareto(self):
        snapshots = (
            snapshot("A", setup_quality=0.8, risk_pct=1.2),
            snapshot("B", setup_quality=0.9, risk_pct=1.5),
            snapshot("C", setup_quality=0.7, risk_pct=0.8, trigger=False),
        )
        result = MultiSymbolSnapshotAnalyzer.analyze(
            universe=universe(),
            snapshots=snapshots,
            policy=policy(),
        )

        self.assertEqual(result["mode"], "OBSERVATION_ONLY")
        self.assertEqual(result["analysis_policy"], ANALYSIS_POLICY)
        self.assertFalse(result["operational_authority"])
        self.assertEqual(result["comparison_eligible_symbols"], ("A", "B"))
        self.assertEqual(result["pareto_symbols"], ("A", "B"))
        self.assertEqual(
            [row["symbol"] for row in result["leaderboards"]["setup_quality"]],
            ["B", "A"],
        )
        self.assertEqual(
            [row["symbol"] for row in result["leaderboards"]["risk_pct"]],
            ["A", "B"],
        )
        c_row = next(row for row in result["rows"] if row["symbol"] == "C")
        self.assertFalse(c_row["comparison_eligible"])
        self.assertEqual(c_row["comparison_reasons"], ("TACTIC_NOT_TRIGGERED",))
        self.assertNotIn("allowed_symbols", result)
        self.assertNotIn("blocked_symbols", result)
        self.assertNotIn("score", result)

    def test_snapshot_input_order_does_not_change_analysis_identity(self):
        a = snapshot("A", setup_quality=0.8, risk_pct=1.2)
        b = snapshot("B", setup_quality=0.9, risk_pct=1.5)
        c = snapshot("C", setup_quality=0.7, risk_pct=0.8, guards=False)
        first = MultiSymbolSnapshotAnalyzer.analyze(
            universe=universe(), snapshots=(a, b, c), policy=policy()
        )
        second = MultiSymbolSnapshotAnalyzer.analyze(
            universe=universe(), snapshots=(c, a, b), policy=policy()
        )
        self.assertEqual(first["result_hash"], second["result_hash"])
        self.assertEqual(first["input_snapshot_hashes"], second["input_snapshot_hashes"])
        self.assertEqual(first["leaderboards"], second["leaderboards"])

    def test_exact_universe_and_time_alignment_fail_closed(self):
        a = snapshot("A", setup_quality=0.8, risk_pct=1.2)
        b = snapshot("B", setup_quality=0.9, risk_pct=1.5)
        c = snapshot("C", setup_quality=0.7, risk_pct=0.8)

        with self.assertRaisesRegex(ValueError, "membership"):
            MultiSymbolSnapshotAnalyzer.analyze(
                universe=universe(), snapshots=(a, b), policy=policy()
            )

        future_c = snapshot(
            "C",
            setup_quality=0.7,
            risk_pct=0.8,
            as_of="20260827102000",
        )
        with self.assertRaisesRegex(ValueError, "exact time"):
            MultiSymbolSnapshotAnalyzer.analyze(
                universe=universe(), snapshots=(a, b, future_c), policy=policy()
            )

    def test_missing_policy_metric_and_nonfinite_metric_fail_closed(self):
        broken = InstrumentSignalSnapshot(
            symbol="A",
            as_of=AS_OF,
            knowledge_cutoff=AS_OF,
            candidate_hash="candidate-A",
            family_id="family",
            generation_hash="generation",
            tactic_trigger=True,
            hard_guards_pass=True,
            locally_admissible=True,
            comparison_metrics={"setup_quality": 0.8},
            source="fixture://signal",
            evidence_hash="evidence-A",
        )
        with self.assertRaisesRegex(ValueError, "누락"):
            MultiSymbolSnapshotAnalyzer.analyze(
                universe=universe(("A",)), snapshots=(broken,), policy=policy()
            )

        invalid = snapshot("A", setup_quality=float("nan"), risk_pct=1.0)
        with self.assertRaisesRegex(ValueError, "NaN/Infinity"):
            invalid.validate()

    def test_addon_module_has_no_execution_or_provider_imports(self):
        source = Path("core/multi_symbol_snapshot.py").read_text(encoding="utf-8")
        for forbidden in (
            "from core.backtest",
            "import BacktestEngine",
            "from core.broker",
            "BrokerEmulator",
            "DSLRuntime",
            "ParentFeatureProvider",
            "provider.build(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
