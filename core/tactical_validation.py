"""Cohort/window-level validation manifests for tactical research.

Unlike the legacy single-symbol final-bar holdout, this contract partitions
point-in-time cohort snapshots.  It does not execute or peek at held-out
outcomes; it only freezes which cohort snapshots belong to train/validation/OOS.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Sequence

from core.tactical_cohort import CohortSnapshot


def _hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ordered_unique(values: Iterable[str], label: str) -> tuple[str, ...]:
    items = tuple(str(value).strip() for value in values)
    if any(not item for item in items):
        raise ValueError(f"{label}에 빈 snapshot hash가 있습니다.")
    if len(set(items)) != len(items):
        raise ValueError(f"{label}에 중복 snapshot hash가 있습니다.")
    return items


@dataclass(frozen=True)
class TacticalValidationManifest:
    schema: str
    unit_id: str
    train_snapshot_hashes: tuple[str, ...]
    validation_snapshot_hashes: tuple[str, ...]
    oos_snapshot_hashes: tuple[str, ...]
    split_axis: str
    manifest_hash: str

    @classmethod
    def create(
        cls,
        *,
        unit_id: str,
        train: Sequence[CohortSnapshot],
        validation: Sequence[CohortSnapshot] = (),
        oos: Sequence[CohortSnapshot],
    ) -> "TacticalValidationManifest":
        if not unit_id.strip():
            raise ValueError("unit_id가 필요합니다.")
        if not train:
            raise ValueError("train cohort snapshot이 최소 1개 필요합니다.")
        if not oos:
            raise ValueError("OOS cohort snapshot이 최소 1개 필요합니다.")
        all_snapshots = list(train) + list(validation) + list(oos)
        wrong_unit = [item.unit_id for item in all_snapshots if item.unit_id != unit_id]
        if wrong_unit:
            raise ValueError(f"validation manifest에 다른 Tactical Unit이 섞였습니다: {wrong_unit}")
        train_hashes = _ordered_unique((item.snapshot_hash for item in train), "train")
        validation_hashes = _ordered_unique((item.snapshot_hash for item in validation), "validation")
        oos_hashes = _ordered_unique((item.snapshot_hash for item in oos), "oos")
        if set(train_hashes) & set(validation_hashes):
            raise ValueError("train과 validation cohort snapshot이 겹칩니다.")
        if set(train_hashes) & set(oos_hashes):
            raise ValueError("train과 OOS cohort snapshot이 겹칩니다.")
        if set(validation_hashes) & set(oos_hashes):
            raise ValueError("validation과 OOS cohort snapshot이 겹칩니다.")
        payload = {
            "schema": "tactical_validation_manifest/v1",
            "unit_id": unit_id,
            "split_axis": "POINT_IN_TIME_COHORT_SNAPSHOT",
            "train_snapshot_hashes": list(train_hashes),
            "validation_snapshot_hashes": list(validation_hashes),
            "oos_snapshot_hashes": list(oos_hashes),
        }
        return cls(
            schema=payload["schema"],
            unit_id=unit_id,
            train_snapshot_hashes=train_hashes,
            validation_snapshot_hashes=validation_hashes,
            oos_snapshot_hashes=oos_hashes,
            split_axis=payload["split_axis"],
            manifest_hash=_hash(payload),
        )

    def partition_of(self, snapshot_hash: str) -> str | None:
        value = str(snapshot_hash)
        if value in self.train_snapshot_hashes:
            return "TRAIN"
        if value in self.validation_snapshot_hashes:
            return "VALIDATION"
        if value in self.oos_snapshot_hashes:
            return "OOS"
        return None
