from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest

from axes.axis2_selection.snapshots.exact_asof import (
    AXIS2_SNAPSHOT_SCHEMA,
    ExactAsOfSnapshotError,
    PointInTimeSnapshot,
)


def row(
    symbol: str,
    feature_id: str,
    value,
    *,
    value_type="NUMBER",
    validity="VALID",
    cutoff="20260901090000",
    observed="20260901085900",
    formula_version="features-v1",
    source_ref="prepared:market-20260901",
    ranking=None,
):
    payload = {
        "symbol": symbol,
        "feature_id": feature_id,
        "value_type": value_type,
        "value": value,
        "validity": validity,
        "provenance": {
            "source_ref": source_ref,
            "observed_as_of": observed,
            "knowledge_cutoff": cutoff,
            "formula_version": formula_version,
        },
    }
    if ranking is not None:
        payload["ranking"] = ranking
    return payload


def snapshot_payload(*rows):
    return {
        "schema_version": AXIS2_SNAPSHOT_SCHEMA,
        "snapshot_id": "snapshot-20260901-090000",
        "as_of": "20260901090000",
        "knowledge_cutoff": "20260901090000",
        "universe_id": "KOSPI-HIGH-BETA-v1",
        "feature_version": "features-v1",
        "source_refs": ["prepared:market-20260901"],
        "rows": list(rows),
    }


class Axis2ExactAsOfSnapshotTests(unittest.TestCase):
    def test_snapshot_is_immutable_versioned_hash_stable_and_roundtrips(self):
        payload = snapshot_payload(
            row("005930", "market.trend_score", 0.72),
            row("000660", "market.trend_score", 0.61),
        )
        first = PointInTimeSnapshot.from_dict(payload)
        second = PointInTimeSnapshot.from_dict(first.public_dict())

        self.assertEqual(first.schema_version, AXIS2_SNAPSHOT_SCHEMA)
        self.assertEqual(first.snapshot_hash, second.snapshot_hash)
        self.assertEqual(first.public_dict(), second.public_dict())
        json.dumps(first.public_dict(), allow_nan=False)
        with self.assertRaises(FrozenInstanceError):
            first.as_of = "20260901090500"
        with self.assertRaises(FrozenInstanceError):
            first.rows[0].value = 0.0

    def test_future_values_mixed_cutoffs_and_mixed_formula_versions_fail_closed(self):
        future = snapshot_payload(
            row(
                "005930",
                "selection.beta",
                1.4,
                observed="20260901090100",
                cutoff="20260901090000",
            )
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(future)
        self.assertEqual(ctx.exception.code, "FUTURE_OBSERVATION")

        mixed_cutoff = snapshot_payload(
            row("005930", "selection.beta", 1.4),
            row(
                "000660",
                "selection.beta",
                1.6,
                cutoff="20260901085959",
                observed="20260901085900",
            ),
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(mixed_cutoff)
        self.assertEqual(ctx.exception.code, "MIXED_KNOWLEDGE_CUTOFF")

        mixed_formula = snapshot_payload(
            row("005930", "selection.beta", 1.4),
            row("000660", "selection.beta", 1.6, formula_version="features-v2"),
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(mixed_formula)
        self.assertEqual(ctx.exception.code, "MIXED_FORMULA_VERSION")

    def test_missing_or_invalid_value_is_explicit_and_never_default_filled(self):
        payload = snapshot_payload(
            row("005930", "selection.capital_flow", None, validity="MISSING"),
            row("000660", "selection.capital_flow", None, validity="INVALID"),
        )
        snapshot = PointInTimeSnapshot.from_dict(payload)
        self.assertIsNone(snapshot.rows[0].value)
        self.assertIsNone(snapshot.rows[1].value)
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            snapshot.row("005930", "selection.capital_flow")
        self.assertEqual(ctx.exception.code, "ROW_NOT_VALID")

        defaulted = snapshot_payload(
            row("005930", "selection.capital_flow", 0.0, validity="MISSING")
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(defaulted)
        self.assertEqual(ctx.exception.code, "INVALID_ROW_HAS_VALUE")

    def test_rank_evidence_is_frozen_validated_and_peer_contract_is_consistent(self):
        rank1 = {
            "ranking_method": "DESCENDING_DENSE_V1",
            "eligible_count": 20,
            "rank": 1,
            "percentile": 100.0,
            "peer_group_id": "HIGH_BETA",
        }
        rank2 = {
            "ranking_method": "DESCENDING_DENSE_V1",
            "eligible_count": 20,
            "rank": 2,
            "percentile": 95.0,
            "peer_group_id": "HIGH_BETA",
        }
        snapshot = PointInTimeSnapshot.from_dict(
            snapshot_payload(
                row("005930", "selection.hist_normalized", 2.3, ranking=rank1),
                row("000660", "selection.hist_normalized", 2.1, ranking=rank2),
            )
        )
        selected = snapshot.row(
            "005930", "selection.hist_normalized", peer_group_id="HIGH_BETA"
        )
        self.assertEqual(selected.ranking.rank, 1)
        self.assertEqual(selected.ranking.eligible_count, 20)

        inconsistent = snapshot_payload(
            row("005930", "selection.hist_normalized", 2.3, ranking=rank1),
            row(
                "000660",
                "selection.hist_normalized",
                2.1,
                ranking={**rank2, "eligible_count": 19},
            ),
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(inconsistent)
        self.assertEqual(ctx.exception.code, "MIXED_RANKING_CONTRACT")

    def test_exact_asof_lookup_has_no_nearest_time_or_fill_forward_mode(self):
        snapshot = PointInTimeSnapshot.from_dict(
            snapshot_payload(row("005930", "market.regime_id", "TREND_UP", value_type="STRING"))
        )
        self.assertIs(
            snapshot.require_exact(
                as_of="20260901090000", knowledge_cutoff="20260901090000"
            ),
            snapshot,
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            snapshot.require_exact(as_of="20260901090001")
        self.assertEqual(ctx.exception.code, "AS_OF_NOT_EXACT")
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            snapshot.require_exact(
                as_of="20260901090000", knowledge_cutoff="20260901085959"
            )
        self.assertEqual(ctx.exception.code, "CUTOFF_NOT_EXACT")

    def test_duplicate_identity_nonfinite_unknown_and_opaque_values_fail_closed(self):
        duplicate = snapshot_payload(
            row("005930", "selection.beta", 1.2),
            row("005930", "selection.beta", 1.3),
        )
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(duplicate)
        self.assertEqual(ctx.exception.code, "DUPLICATE_ROW")

        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(
                snapshot_payload(row("005930", "selection.beta", float("inf")))
            )
        self.assertEqual(ctx.exception.code, "NONFINITE_VALUE")

        opaque = snapshot_payload(row("005930", "selection.beta", object()))
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(opaque)
        self.assertEqual(ctx.exception.code, "BAD_NUMBER")

        unknown = snapshot_payload(row("005930", "selection.beta", 1.2))
        unknown["nearest_time"] = True
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(unknown)
        self.assertEqual(ctx.exception.code, "UNKNOWN_FIELD")

    def test_snapshot_hash_detects_payload_tampering(self):
        snapshot = PointInTimeSnapshot.from_dict(
            snapshot_payload(row("005930", "selection.beta", 1.4))
        )
        payload = snapshot.public_dict()
        payload["rows"][0]["value"] = 1.5
        with self.assertRaises(ExactAsOfSnapshotError) as ctx:
            PointInTimeSnapshot.from_dict(payload)
        self.assertEqual(ctx.exception.code, "SNAPSHOT_HASH_MISMATCH")

    def test_snapshot_contract_has_no_axis1_axis3_provider_or_frozen_core_import(self):
        import axes.axis2_selection.snapshots.exact_asof as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        forbidden = (
            "axes.axis1_dsl",
            "axes.axis3_monetization",
            "from core",
            "import core",
            "providers.",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

        schema_path = Path(module.__file__).with_name("point_in_time_snapshot.v1.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], AXIS2_SNAPSHOT_SCHEMA)
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
