from __future__ import annotations

import json
from pathlib import Path
import unittest

from axes.axis2_selection.engine.selection import (
    AXIS2_CANDIDATE_SET_SCHEMA,
    AXIS2_SELECTION_SPEC_SCHEMA,
    Axis2SelectionEngine,
    SelectionError,
    SelectionSpec,
)
from axes.axis2_selection.snapshots.exact_asof import (
    AXIS2_SNAPSHOT_SCHEMA,
    PointInTimeSnapshot,
)


CUTOFF = "20260901090000"
SOURCE = "prepared:axis2-selection-test"
VERSION = "features-v1"


def row(
    symbol,
    feature_id,
    value,
    *,
    value_type="NUMBER",
    validity="VALID",
    ranking=None,
):
    return {
        "symbol": symbol,
        "feature_id": feature_id,
        "value_type": value_type,
        "value": value,
        "validity": validity,
        "provenance": {
            "source_ref": SOURCE,
            "observed_as_of": "20260901085900",
            "knowledge_cutoff": CUTOFF,
            "formula_version": VERSION,
        },
        **({} if ranking is None else {"ranking": ranking}),
    }


def ranking(rank, *, eligible=4, percentile=None, peer="HIGH_BETA"):
    if percentile is None:
        percentile = 100.0 - ((rank - 1) * 100.0 / max(1, eligible))
    return {
        "ranking_method": "DESCENDING_DENSE_V1",
        "eligible_count": eligible,
        "rank": rank,
        "percentile": percentile,
        "peer_group_id": peer,
    }


def snapshot(*rows):
    return PointInTimeSnapshot.from_dict(
        {
            "schema_version": AXIS2_SNAPSHOT_SCHEMA,
            "snapshot_id": "selection-snapshot-1",
            "as_of": CUTOFF,
            "knowledge_cutoff": CUTOFF,
            "universe_id": "TEST-UNIVERSE-v1",
            "feature_version": VERSION,
            "source_refs": [SOURCE],
            "rows": list(rows),
        }
    )


def spec_payload(snap, *, filters=None, sort=None, top_n=None, symbol_scope=None):
    return {
        "schema_version": AXIS2_SELECTION_SPEC_SCHEMA,
        "selection_id": "selection-1",
        "condition_version": "condition-v1",
        "snapshot_id": snap.snapshot_id,
        "snapshot_hash": snap.snapshot_hash,
        "as_of": snap.as_of,
        "knowledge_cutoff": snap.knowledge_cutoff,
        "filters": list(filters or []),
        "sort": sort,
        "top_n": top_n,
        "symbol_scope": symbol_scope,
    }


class Axis2SelectionEngineTests(unittest.TestCase):
    def test_numeric_filter_value_sort_top_n_is_deterministic_with_symbol_tie_break(self):
        snap = snapshot(
            row("A", "selection.high_beta", True, value_type="BOOLEAN"),
            row("B", "selection.high_beta", True, value_type="BOOLEAN"),
            row("C", "selection.high_beta", False, value_type="BOOLEAN"),
            row("D", "selection.high_beta", True, value_type="BOOLEAN"),
            row("A", "selection.hist_normalized", 1.5),
            row("B", "selection.hist_normalized", 2.0),
            row("C", "selection.hist_normalized", 9.0),
            row("D", "selection.hist_normalized", 2.0),
        )
        payload = spec_payload(
            snap,
            filters=[
                {
                    "rule_id": "high-beta",
                    "feature_id": "selection.high_beta",
                    "metric": "VALUE",
                    "operator": "EQ",
                    "operand": True,
                },
                {
                    "rule_id": "hist-positive",
                    "feature_id": "selection.hist_normalized",
                    "metric": "VALUE",
                    "operator": "GT",
                    "operand": 0.0,
                },
            ],
            sort={
                "feature_id": "selection.hist_normalized",
                "metric": "VALUE",
                "direction": "DESC",
            },
            top_n=2,
        )
        plan = SelectionSpec.from_dict(payload)
        first = Axis2SelectionEngine.select(snap, plan)
        second = Axis2SelectionEngine.select(snap, SelectionSpec.from_dict(payload))

        self.assertEqual([item.symbol for item in first.candidates], ["B", "D"])
        self.assertEqual([item.ordinal for item in first.candidates], [1, 2])
        self.assertEqual(first.eligible_count_before_top_n, 3)
        self.assertEqual(first.candidate_set_hash, second.candidate_set_hash)
        self.assertEqual(first.public_dict(), second.public_dict())
        self.assertFalse(first.ordering["rank_recomputed"])
        json.dumps(first.public_dict(), allow_nan=False)

    def test_frozen_rank_sort_uses_snapshot_rank_not_raw_feature_value(self):
        snap = snapshot(
            row("A", "selection.hist_normalized", 999.0, ranking=ranking(3, eligible=3, percentile=33.0)),
            row("B", "selection.hist_normalized", 1.0, ranking=ranking(1, eligible=3, percentile=100.0)),
            row("C", "selection.hist_normalized", 2.0, ranking=ranking(2, eligible=3, percentile=66.0)),
        )
        result = Axis2SelectionEngine.select(
            snap,
            spec_payload(
                snap,
                sort={
                    "feature_id": "selection.hist_normalized",
                    "metric": "RANK",
                    "direction": "ASC",
                    "peer_group_id": "HIGH_BETA",
                },
                top_n=2,
            ),
        )
        self.assertEqual([item.symbol for item in result.candidates], ["B", "C"])
        self.assertEqual(result.ordering["metric"], "RANK")
        self.assertFalse(result.ordering["rank_recomputed"])
        rank_evidence = result.candidates[0].evidence[-1]
        self.assertEqual(rank_evidence["ranking"]["rank"], 1)
        self.assertEqual(rank_evidence["observed"], 1.0)

    def test_boolean_string_and_percentile_filters_compose_over_same_snapshot(self):
        rows = []
        data = {
            "A": ("TECH", True, 92.0, 1),
            "B": ("CHIP", True, 84.0, 2),
            "C": ("BIO", True, 98.0, 1),
            "D": ("TECH", False, 88.0, 3),
        }
        for symbol, (sector, liquid, pct, rank_value) in data.items():
            rows.extend(
                [
                    row(symbol, "sector.id", sector, value_type="STRING"),
                    row(symbol, "selection.liquid", liquid, value_type="BOOLEAN"),
                    row(
                        symbol,
                        "selection.hist_normalized",
                        pct / 10.0,
                        ranking=ranking(rank_value, eligible=4, percentile=pct),
                    ),
                ]
            )
        snap = snapshot(*rows)
        result = Axis2SelectionEngine.select(
            snap,
            spec_payload(
                snap,
                filters=[
                    {
                        "rule_id": "sector",
                        "feature_id": "sector.id",
                        "metric": "VALUE",
                        "operator": "IN",
                        "operand": ["TECH", "CHIP"],
                    },
                    {
                        "rule_id": "liquid",
                        "feature_id": "selection.liquid",
                        "metric": "VALUE",
                        "operator": "EQ",
                        "operand": True,
                    },
                    {
                        "rule_id": "hist-percentile",
                        "feature_id": "selection.hist_normalized",
                        "metric": "PERCENTILE",
                        "operator": "GTE",
                        "operand": 80.0,
                        "peer_group_id": "HIGH_BETA",
                    },
                ],
            ),
        )
        self.assertEqual([item.symbol for item in result.candidates], ["A", "B"])

    def test_missing_invalid_and_absent_evidence_are_explicit_exclusions_without_defaults(self):
        snap = snapshot(
            row("A", "selection.flow", 1.2),
            row("B", "selection.flow", None, validity="MISSING"),
            row("C", "selection.flow", None, validity="INVALID"),
            row("D", "selection.other", 10.0),
        )
        result = Axis2SelectionEngine.select(
            snap,
            spec_payload(
                snap,
                filters=[
                    {
                        "rule_id": "flow-positive",
                        "feature_id": "selection.flow",
                        "metric": "VALUE",
                        "operator": "GT",
                        "operand": 0.0,
                    }
                ],
            ),
        )
        self.assertEqual([item.symbol for item in result.candidates], ["A"])
        excluded = {item["symbol"]: item["reason_codes"] for item in result.exclusions}
        self.assertEqual(excluded["B"], ["ROW_MISSING"])
        self.assertEqual(excluded["C"], ["ROW_INVALID"])
        self.assertEqual(excluded["D"], ["ROW_NOT_FOUND"])

    def test_peer_group_is_required_when_same_feature_has_multiple_rank_contexts(self):
        snap = snapshot(
            row("A", "selection.hist", 3.0, ranking=ranking(1, eligible=1, peer="MARKET")),
            row("A", "selection.hist", 3.0, ranking=ranking(1, eligible=1, peer="SECTOR:TECH")),
        )
        ambiguous = spec_payload(
            snap,
            filters=[
                {
                    "rule_id": "rank",
                    "feature_id": "selection.hist",
                    "metric": "RANK",
                    "operator": "LTE",
                    "operand": 1,
                }
            ],
        )
        with self.assertRaises(SelectionError) as ctx:
            Axis2SelectionEngine.select(snap, ambiguous)
        self.assertEqual(ctx.exception.code, "AMBIGUOUS_FEATURE")

        exact = spec_payload(
            snap,
            filters=[
                {
                    "rule_id": "rank",
                    "feature_id": "selection.hist",
                    "metric": "RANK",
                    "operator": "LTE",
                    "operand": 1,
                    "peer_group_id": "SECTOR:TECH",
                }
            ],
        )
        result = Axis2SelectionEngine.select(snap, exact)
        self.assertEqual([item.symbol for item in result.candidates], ["A"])

    def test_selection_is_bound_to_exact_snapshot_identity_asof_and_cutoff(self):
        snap = snapshot(row("A", "selection.beta", 1.4))
        base = spec_payload(snap)
        cases = (
            ("snapshot_id", "other", "SNAPSHOT_ID_MISMATCH"),
            ("snapshot_hash", "0" * 64, "SNAPSHOT_HASH_MISMATCH"),
            ("as_of", "20260901090001", "AS_OF_MISMATCH"),
            ("knowledge_cutoff", "20260901085959", "CUTOFF_MISMATCH"),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                payload = {**base, field: value}
                with self.assertRaises(SelectionError) as ctx:
                    Axis2SelectionEngine.select(snap, payload)
                self.assertEqual(ctx.exception.code, code)

    def test_selection_spec_and_type_contracts_fail_closed(self):
        snap = snapshot(row("A", "selection.beta", 1.4))

        unknown = spec_payload(snap)
        unknown["nearest_time"] = True
        with self.assertRaises(SelectionError) as ctx:
            SelectionSpec.from_dict(unknown)
        self.assertEqual(ctx.exception.code, "UNKNOWN_FIELD")

        with self.assertRaises(SelectionError) as ctx:
            SelectionSpec.from_dict(spec_payload(snap, top_n=1))
        self.assertEqual(ctx.exception.code, "TOP_N_REQUIRES_SORT")

        bad_number = spec_payload(
            snap,
            filters=[
                {
                    "rule_id": "beta",
                    "feature_id": "selection.beta",
                    "metric": "VALUE",
                    "operator": "GT",
                    "operand": float("inf"),
                }
            ],
        )
        with self.assertRaises(SelectionError) as ctx:
            SelectionSpec.from_dict(bad_number)
        self.assertEqual(ctx.exception.code, "NONFINITE_VALUE")

        wrong_type = spec_payload(
            snap,
            filters=[
                {
                    "rule_id": "beta",
                    "feature_id": "selection.beta",
                    "metric": "VALUE",
                    "operator": "EQ",
                    "operand": "1.4",
                }
            ],
        )
        with self.assertRaises(SelectionError) as ctx:
            Axis2SelectionEngine.select(snap, wrong_type)
        self.assertEqual(ctx.exception.code, "TYPE_MISMATCH")

        duplicate = spec_payload(
            snap,
            filters=[
                {
                    "rule_id": "same",
                    "feature_id": "selection.beta",
                    "metric": "VALUE",
                    "operator": "GT",
                    "operand": 1.0,
                },
                {
                    "rule_id": "same",
                    "feature_id": "selection.beta",
                    "metric": "VALUE",
                    "operator": "LT",
                    "operand": 2.0,
                },
            ],
        )
        with self.assertRaises(SelectionError) as ctx:
            SelectionSpec.from_dict(duplicate)
        self.assertEqual(ctx.exception.code, "DUPLICATE_RULE_ID")

    def test_symbol_scope_is_canonical_and_cannot_invent_universe_members(self):
        snap = snapshot(
            row("A", "selection.beta", 1.0),
            row("B", "selection.beta", 2.0),
            row("C", "selection.beta", 3.0),
        )
        plan = SelectionSpec.from_dict(spec_payload(snap, symbol_scope=["C", "A"]))
        self.assertEqual(plan.symbol_scope, ("A", "C"))
        result = Axis2SelectionEngine.select(snap, plan)
        self.assertEqual([item.symbol for item in result.candidates], ["A", "C"])

        invented = spec_payload(snap, symbol_scope=["A", "Z"])
        with self.assertRaises(SelectionError) as ctx:
            Axis2SelectionEngine.select(snap, invented)
        self.assertEqual(ctx.exception.code, "SYMBOL_NOT_IN_SNAPSHOT")

    def test_engine_and_contract_schemas_are_axis_isolated(self):
        import axes.axis2_selection.engine.selection as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in (
            "axes.axis1_dsl",
            "axes.axis3_monetization",
            "from core",
            "import core",
            "providers.",
        ):
            self.assertNotIn(token, source)

        directory = Path(module.__file__).parent
        selection_schema = json.loads((directory / "selection_spec.v1.schema.json").read_text(encoding="utf-8"))
        candidate_schema = json.loads((directory / "candidate_set.v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(selection_schema["$id"], AXIS2_SELECTION_SPEC_SCHEMA)
        self.assertEqual(candidate_schema["$id"], AXIS2_CANDIDATE_SET_SCHEMA)
        self.assertFalse(selection_schema["additionalProperties"])
        self.assertFalse(candidate_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
