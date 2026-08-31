from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from axes.axis3_monetization.crud.versioned_store import Axis3StoreError, VersionedArtifactStore
from axes.axis3_monetization.orchestration.run_plan import (
    Axis3OrchestrationError,
    build_strategy_run_plan,
)


def canonical_hash(value):
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def selection_spec(*, condition_version="cond-v1", threshold=80.0):
    body = {
        "schema_version": "axis2_selection_spec/v1",
        "selection_id": "sel-high-beta-hist",
        "condition_version": condition_version,
        "snapshot_id": "snap-0900",
        "snapshot_hash": "snapshot-hash-001",
        "as_of": "20260901090000",
        "knowledge_cutoff": "20260901090000",
        "filters": [
            {
                "rule_id": "hist-pct",
                "feature_id": "selection.hist_normalized",
                "metric": "PERCENTILE",
                "operator": "GTE",
                "operand": threshold,
                "peer_group_id": "HIGH_BETA",
            }
        ],
        "sort": {
            "feature_id": "selection.hist_normalized",
            "metric": "RANK",
            "direction": "ASC",
            "peer_group_id": "HIGH_BETA",
        },
        "top_n": 2,
        "symbol_scope": None,
    }
    return {**body, "selection_hash": canonical_hash(body)}


def candidate_set(spec, *, symbols=("000660", "005930")):
    candidates = [
        {
            "symbol": symbol,
            "ordinal": index + 1,
            "evidence": [
                {
                    "feature_id": "selection.hist_normalized",
                    "observed": 95.0 - index * 3.0,
                    "role": "FILTER",
                }
            ],
        }
        for index, symbol in enumerate(symbols)
    ]
    body = {
        "schema_version": "axis2_candidate_set/v1",
        "selection_id": spec["selection_id"],
        "condition_version": spec["condition_version"],
        "selection_hash": spec["selection_hash"],
        "snapshot_id": spec["snapshot_id"],
        "snapshot_hash": spec["snapshot_hash"],
        "as_of": spec["as_of"],
        "knowledge_cutoff": spec["knowledge_cutoff"],
        "universe_id": "KOSPI-HIGH-BETA-v1",
        "source_symbol_count": 4,
        "eligible_count_before_top_n": len(candidates),
        "selected_count": len(candidates),
        "candidates": candidates,
        "exclusions": [],
        "ordering": {
            "feature_id": "selection.hist_normalized",
            "metric": "RANK",
            "direction": "ASC",
            "peer_group_id": "HIGH_BETA",
            "tie_breaker": "SYMBOL_ASC",
            "top_n": 2,
            "rank_recomputed": False,
        },
    }
    return {**body, "candidate_set_hash": canonical_hash(body)}


class Axis3CrudOrchestrationTests(unittest.TestCase):
    def test_condition_crud_creates_immutable_versions_and_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "axis3.sqlite3")
            store = VersionedArtifactStore(path)
            first_spec = selection_spec(threshold=80.0)
            first = store.create_condition(
                condition_id="cond-alpha",
                name="High beta histogram",
                selection_spec=first_spec,
                created_at="20260901091000",
            )
            second = store.create_condition(
                condition_id="cond-alpha",
                name="High beta histogram tighter",
                selection_spec=selection_spec(condition_version="cond-v2", threshold=90.0),
                created_at="20260901092000",
            )
            self.assertEqual((first.version, second.version), (1, 2))
            self.assertEqual(second.parent_version, 1)
            self.assertNotEqual(first.artifact_hash, second.artifact_hash)
            self.assertEqual(
                [item.version for item in store.list_condition_versions("cond-alpha")], [1, 2]
            )
            original_hash = store.get_condition("cond-alpha", 1).artifact_hash
            store.close()

            reopened = VersionedArtifactStore(path)
            self.assertEqual(reopened.get_condition("cond-alpha", 1).artifact_hash, original_hash)
            self.assertEqual(reopened.get_condition("cond-alpha").version, 2)
            reopened.close()

    def test_strategy_crud_requires_existing_condition_refs_and_compares_versions(self):
        store = VersionedArtifactStore()
        condition = store.create_condition(
            condition_id="cond-alpha",
            name="Condition",
            selection_spec=selection_spec(),
            created_at="20260901091000",
        )
        first = store.create_strategy(
            strategy_id="strategy-a",
            name="A",
            timeframe="15m",
            dsl_code='strategy "A" { timeframe = "15m" x = ta.sma(close, 5) }',
            settings={"allocation_pct": 50.0},
            condition_refs=[{"condition_id": condition.condition_id, "version": condition.version}],
            created_at="20260901093000",
        )
        second = store.create_strategy(
            strategy_id="strategy-a",
            name="A2",
            timeframe="15m",
            dsl_code='strategy "A2" { timeframe = "15m" x = ta.sma(close, 8) }',
            settings={"allocation_pct": 40.0},
            condition_refs=[{"condition_id": condition.condition_id, "version": condition.version}],
            created_at="20260901094000",
        )
        self.assertEqual(second.parent_version, 1)
        comparison = store.compare_strategy_versions("strategy-a", 1, 2)
        self.assertFalse(comparison["same_content"])
        self.assertTrue(comparison["changed"]["dsl_code"])
        self.assertTrue(comparison["changed"]["settings"])
        self.assertEqual(store.get_strategy("strategy-a", 1).artifact_hash, first.artifact_hash)

        with self.assertRaises(Axis3StoreError) as ctx:
            store.create_strategy(
                strategy_id="bad-ref",
                name="Bad",
                timeframe="15m",
                dsl_code='strategy "Bad" { timeframe = "15m" }',
                settings={},
                condition_refs=[{"condition_id": "missing", "version": 1}],
                created_at="20260901095000",
            )
        self.assertEqual(ctx.exception.code, "CONDITION_REF_NOT_FOUND")

    def test_lifecycle_promote_reject_archive_is_separate_and_audited(self):
        store = VersionedArtifactStore()
        condition = store.create_condition(
            condition_id="cond-alpha",
            name="Condition",
            selection_spec=selection_spec(),
            created_at="20260901091000",
        )
        strategy = store.create_strategy(
            strategy_id="strategy-a",
            name="A",
            timeframe="15m",
            dsl_code='strategy "A" { timeframe = "15m" }',
            settings={},
            condition_refs=[{"condition_id": condition.condition_id, "version": 1}],
            created_at="20260901092000",
        )
        condition_hash = condition.artifact_hash
        promoted = store.transition(
            "CONDITION",
            condition.condition_id,
            1,
            to_status="PROMOTED",
            reason="validated",
            event_time="20260901093000",
        )
        rejected = store.transition(
            "STRATEGY",
            strategy.strategy_id,
            1,
            to_status="REJECTED",
            reason="insufficient evidence",
            event_time="20260901093100",
        )
        self.assertEqual(promoted.status, "PROMOTED")
        self.assertEqual(rejected.status, "REJECTED")
        self.assertEqual(store.get_condition(condition.condition_id, 1).artifact_hash, condition_hash)
        with self.assertRaises(Axis3StoreError) as ctx:
            store.transition(
                "STRATEGY",
                strategy.strategy_id,
                1,
                to_status="PROMOTED",
                reason="cannot revive",
                event_time="20260901093200",
            )
        self.assertEqual(ctx.exception.code, "INVALID_TRANSITION")
        archived = store.transition(
            "STRATEGY",
            strategy.strategy_id,
            1,
            to_status="ARCHIVED",
            reason="retained for lineage only",
            event_time="20260901093300",
        )
        self.assertEqual(archived.status, "ARCHIVED")
        self.assertEqual(
            [item["to_status"] for item in store.lifecycle_events("STRATEGY", strategy.strategy_id, 1)],
            ["DRAFT", "REJECTED", "ARCHIVED"],
        )

    def test_orchestration_requires_promoted_exact_artifacts_and_is_deterministic(self):
        store = VersionedArtifactStore()
        spec = selection_spec()
        condition = store.create_condition(
            condition_id="cond-alpha",
            name="Condition",
            selection_spec=spec,
            created_at="20260901091000",
        )
        strategy = store.create_strategy(
            strategy_id="strategy-a",
            name="A",
            timeframe="15m",
            dsl_code='strategy "A" { timeframe = "15m" x = ta.sma(close, 5) }',
            settings={"allocation_pct": 50.0},
            condition_refs=[{"condition_id": condition.condition_id, "version": 1}],
            created_at="20260901092000",
        )
        candidates = candidate_set(spec)

        with self.assertRaises(Axis3OrchestrationError) as ctx:
            build_strategy_run_plan(
                store,
                run_id="run-1",
                strategy_id=strategy.strategy_id,
                strategy_version=1,
                condition_id=condition.condition_id,
                condition_version=1,
                candidate_set=candidates,
            )
        self.assertEqual(ctx.exception.code, "ARTIFACT_NOT_PROMOTED")

        store.transition(
            "CONDITION", "cond-alpha", 1,
            to_status="PROMOTED", reason="validated", event_time="20260901093000"
        )
        store.transition(
            "STRATEGY", "strategy-a", 1,
            to_status="PROMOTED", reason="validated", event_time="20260901093100"
        )
        first = build_strategy_run_plan(
            store,
            run_id="run-1",
            strategy_id="strategy-a",
            strategy_version=1,
            condition_id="cond-alpha",
            condition_version=1,
            candidate_set=candidates,
        )
        second = build_strategy_run_plan(
            store,
            run_id="run-1",
            strategy_id="strategy-a",
            strategy_version=1,
            condition_id="cond-alpha",
            condition_version=1,
            candidate_set=candidates,
        )
        self.assertEqual(first.plan_hash, second.plan_hash)
        self.assertEqual([item.symbol for item in first.intents], ["000660", "005930"])
        self.assertEqual([item.candidate_ordinal for item in first.intents], [1, 2])
        self.assertEqual(first.intents[0].strategy_hash, strategy.artifact_hash)
        json.dumps(first.public_dict(), allow_nan=False)

    def test_orchestration_rejects_candidate_set_tamper_or_binding_drift(self):
        store = VersionedArtifactStore()
        spec = selection_spec()
        condition = store.create_condition(
            condition_id="cond-alpha", name="Condition", selection_spec=spec,
            created_at="20260901091000"
        )
        strategy = store.create_strategy(
            strategy_id="strategy-a", name="A", timeframe="15m",
            dsl_code='strategy "A" { timeframe = "15m" }', settings={},
            condition_refs=[{"condition_id": "cond-alpha", "version": 1}],
            created_at="20260901092000"
        )
        store.transition("CONDITION", "cond-alpha", 1, to_status="PROMOTED", reason="ok", event_time="20260901093000")
        store.transition("STRATEGY", "strategy-a", 1, to_status="PROMOTED", reason="ok", event_time="20260901093100")

        tampered = candidate_set(spec)
        tampered["candidates"][0]["symbol"] = "999999"
        with self.assertRaises(Axis3OrchestrationError) as ctx:
            build_strategy_run_plan(
                store, run_id="run-1", strategy_id="strategy-a", strategy_version=1,
                condition_id="cond-alpha", condition_version=1, candidate_set=tampered
            )
        self.assertEqual(ctx.exception.code, "CANDIDATE_SET_HASH_MISMATCH")

        drift = candidate_set(spec)
        drift_body = {key: value for key, value in drift.items() if key != "candidate_set_hash"}
        drift_body["selection_hash"] = "different-selection"
        drift = {**drift_body, "candidate_set_hash": canonical_hash(drift_body)}
        with self.assertRaises(Axis3OrchestrationError) as ctx:
            build_strategy_run_plan(
                store, run_id="run-1", strategy_id="strategy-a", strategy_version=1,
                condition_id="cond-alpha", condition_version=1, candidate_set=drift
            )
        self.assertEqual(ctx.exception.code, "SELECTION_HASH_MISMATCH")

    def test_store_rejects_nonfinite_or_opaque_artifact_payloads(self):
        store = VersionedArtifactStore()
        bad = selection_spec()
        bad["filters"][0]["operand"] = float("inf")
        with self.assertRaises(Axis3StoreError) as ctx:
            store.create_condition(
                condition_id="bad", name="Bad", selection_spec=bad,
                created_at="20260901091000"
            )
        self.assertEqual(ctx.exception.code, "NONFINITE_VALUE")

        with self.assertRaises(Axis3StoreError) as ctx:
            store.create_strategy(
                strategy_id="opaque", name="Opaque", timeframe="15m",
                dsl_code='strategy "O" { timeframe = "15m" }',
                settings={"x": object()}, condition_refs=[], created_at="20260901092000"
            )
        self.assertEqual(ctx.exception.code, "OPAQUE_VALUE")

    def test_axis3_modules_do_not_import_axis1_axis2_or_frozen_core(self):
        import axes.axis3_monetization.crud.versioned_store as store_module
        import axes.axis3_monetization.orchestration.run_plan as plan_module

        for module in (store_module, plan_module):
            source = Path(module.__file__).read_text(encoding="utf-8")
            for token in (
                "axes.axis1_dsl",
                "axes.axis2_selection",
                "from core",
                "import core",
            ):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
