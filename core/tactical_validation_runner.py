"""Aggregate immutable tactical reports by cohort-level validation partition."""
from __future__ import annotations

from statistics import mean
from typing import Any, Mapping, Sequence

from core.tactical_validation import TacticalValidationManifest


def _partition_summary(items: Sequence[Mapping[str, Any]]) -> dict:
    cohorts = len(items)
    symbols = sum(int(item.get("cohort_symbols") or 0) for item in items)
    positives = sum(int(item.get("official_mission_positive") or 0) for item in items)
    profitable = sum(int(item.get("strategy_profitable_symbols") or 0) for item in items)
    positive_profitable = sum(int(item.get("positive_and_profitable") or 0) for item in items)
    returns = [
        float(value)
        for item in items
        for value in [item.get("average_strategy_return_pct")]
        if value is not None
    ]
    return {
        "cohorts": cohorts,
        "symbols": symbols,
        "official_mission_positive": positives,
        "strategy_profitable_symbols": profitable,
        "positive_and_profitable": positive_profitable,
        "mission_positive_profitable_retention": (
            positive_profitable / positives if positives else None
        ),
        "profitable_precision_against_mission": (
            positive_profitable / profitable if profitable else None
        ),
        "mean_cohort_strategy_return_pct": float(mean(returns)) if returns else None,
    }


class TacticalValidationRunner:
    """Summarize already-executed immutable cohort reports.

    This class does not construct cohorts or inspect future labels to choose
    partitions. The supplied ``TacticalValidationManifest`` is the authority.
    """

    @staticmethod
    def summarize(
        manifest: TacticalValidationManifest,
        reports: Sequence[Mapping[str, Any]],
    ) -> dict:
        seen = set()
        partitions = {"TRAIN": [], "VALIDATION": [], "OOS": []}
        for report in reports:
            snapshot_hash = str(report.get("cohort_snapshot_hash") or "").strip()
            if not snapshot_hash:
                raise ValueError("validation report에 cohort_snapshot_hash가 없습니다.")
            if snapshot_hash in seen:
                raise ValueError(f"validation report cohort 중복: {snapshot_hash}")
            seen.add(snapshot_hash)
            partition = manifest.partition_of(snapshot_hash)
            if partition is None:
                raise ValueError(
                    f"validation manifest에 없는 cohort report가 포함되었습니다: {snapshot_hash}"
                )
            partitions[partition].append(report)
        expected = set(
            manifest.train_snapshot_hashes
            + manifest.validation_snapshot_hashes
            + manifest.oos_snapshot_hashes
        )
        if seen != expected:
            missing = sorted(expected - seen)
            raise ValueError(f"validation manifest cohort report가 누락되었습니다: {missing}")
        return {
            "schema": "tactical_validation_summary/v1",
            "unit_id": manifest.unit_id,
            "manifest_hash": manifest.manifest_hash,
            "split_axis": manifest.split_axis,
            "partitions": {
                name: _partition_summary(items) for name, items in partitions.items()
            },
        }
