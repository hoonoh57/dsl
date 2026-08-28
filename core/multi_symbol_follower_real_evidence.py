"""Admission contract for non-fixture LF2/LFOUT1 research evidence.

LFREAL1 does not fetch market data and cannot prove a declared source exists. It
validates that externally frozen evidence/outcome rows carry explicit provenance,
rejects fixture/synthetic declarations, enforces exact identity coverage and
strict post-observation outcome timing, then delegates outcome-axis evaluation to
trusted LFOUT1 semantics. It grants no operational or deployment authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence

from core.multi_symbol_follower_outcome_validation import (
    FollowerOutcomeContract,
    FollowerOutcomePartition,
    FrozenFollowerOutcome,
    MultiSymbolFollowerOutcomeValidationArena,
)

SCHEMA_VERSION = "multi_symbol_follower_real_evidence/v1"
POLICY = "NON_FIXTURE_DECLARED_PROVENANCE_EXACT_ASOF_POST_OBSERVATION_OUTCOME_LFOUT1_NO_AUTHORITY"
_BLOCKED_SOURCE_KINDS = {"SYNTHETIC", "FIXTURE", "GENERATED", "MOCK", "TEST"}


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _time_key(value: Any, label: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 14:
        raise ValueError(f"{label}은 YYYYMMDDHHMMSS 형식이어야 합니다.")
    return digits


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FrozenEvidenceProvenance:
    evidence_hash: str
    source_id: str
    source_hash: str
    source_kind: str
    observation_cutoff: str
    fixture_only: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.evidence_hash, "LFREAL1 evidence_hash")
        _text(self.source_id, "LFREAL1 source_id")
        _text(self.source_hash, "LFREAL1 source_hash")
        kind = _text(self.source_kind, "LFREAL1 source_kind").upper()
        if kind in _BLOCKED_SOURCE_KINDS:
            raise ValueError(f"LFREAL1 synthetic/fixture source_kind를 허용하지 않습니다: {kind}")
        _time_key(self.observation_cutoff, "LFREAL1 observation_cutoff")
        if type(self.fixture_only) is not bool:
            raise ValueError("LFREAL1 fixture_only는 bool이어야 합니다.")
        if self.fixture_only:
            raise ValueError("LFREAL1 fixture_only provenance를 허용하지 않습니다.")

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "evidence_hash": str(self.evidence_hash).strip(),
            "source_id": str(self.source_id).strip(),
            "source_hash": str(self.source_hash).strip(),
            "source_kind": str(self.source_kind).strip().upper(),
            "observation_cutoff": _time_key(self.observation_cutoff, "LFREAL1 observation_cutoff"),
            "fixture_only": False,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RealEvidenceStudyPartition:
    partition_id: str
    role: str
    evidence_rows: Sequence[Mapping[str, Any]]
    provenances: Sequence[FrozenEvidenceProvenance]
    outcomes: Sequence[FrozenFollowerOutcome]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.partition_id, "LFREAL1 partition_id")
        evidence = tuple(self.evidence_rows)
        provenances = tuple(self.provenances)
        outcomes = tuple(self.outcomes)
        if not evidence or not provenances or not outcomes:
            raise ValueError("LFREAL1 evidence/provenance/outcome이 비어 있으면 안 됩니다.")

        evidence_by_hash: dict[str, Mapping[str, Any]] = {}
        for row in evidence:
            if not isinstance(row, Mapping):
                raise ValueError("LFREAL1 evidence row는 Mapping이어야 합니다.")
            evidence_hash = _text(row.get("evidence_hash"), "LFREAL1 evidence evidence_hash")
            _text(row.get("as_of"), "LFREAL1 evidence as_of")
            if evidence_hash in evidence_by_hash:
                raise ValueError("LFREAL1 evidence_hash에 중복이 있습니다.")
            evidence_by_hash[evidence_hash] = row

        provenance_by_hash: dict[str, FrozenEvidenceProvenance] = {}
        for provenance in provenances:
            if not isinstance(provenance, FrozenEvidenceProvenance):
                raise ValueError("LFREAL1 provenance 타입이 올바르지 않습니다.")
            provenance.validate()
            key = str(provenance.evidence_hash).strip()
            if key in provenance_by_hash:
                raise ValueError("LFREAL1 provenance evidence_hash에 중복이 있습니다.")
            provenance_by_hash[key] = provenance

        outcome_by_hash: dict[str, FrozenFollowerOutcome] = {}
        for outcome in outcomes:
            if not isinstance(outcome, FrozenFollowerOutcome):
                raise ValueError("LFREAL1 outcome 타입이 올바르지 않습니다.")
            outcome.validate()
            key = str(outcome.evidence_hash).strip()
            if key in outcome_by_hash:
                raise ValueError("LFREAL1 outcome evidence_hash에 중복이 있습니다.")
            outcome_by_hash[key] = outcome

        expected = set(evidence_by_hash)
        if set(provenance_by_hash) != expected:
            raise ValueError("LFREAL1 exact provenance coverage가 필요합니다.")
        if set(outcome_by_hash) != expected:
            raise ValueError("LFREAL1 exact outcome coverage가 필요합니다.")

        for evidence_hash, row in evidence_by_hash.items():
            provenance = provenance_by_hash[evidence_hash]
            outcome = outcome_by_hash[evidence_hash]
            evidence_as_of = _time_key(row.get("as_of"), "LFREAL1 evidence as_of")
            if _time_key(provenance.observation_cutoff, "LFREAL1 observation_cutoff") != evidence_as_of:
                raise ValueError("LFREAL1 observation_cutoff은 evidence.as_of와 정확히 같아야 합니다.")

            outcome_meta = dict(outcome.metadata)
            if bool(outcome_meta.get("fixture_only", False)):
                raise ValueError("LFREAL1 fixture_only outcome을 허용하지 않습니다.")
            outcome_kind = _text(outcome_meta.get("source_kind"), "LFREAL1 outcome source_kind").upper()
            if outcome_kind in _BLOCKED_SOURCE_KINDS:
                raise ValueError(f"LFREAL1 synthetic/fixture outcome source_kind를 허용하지 않습니다: {outcome_kind}")
            _text(outcome_meta.get("source_id"), "LFREAL1 outcome source_id")
            _text(outcome_meta.get("source_hash"), "LFREAL1 outcome source_hash")
            _text(outcome_meta.get("horizon_id"), "LFREAL1 outcome horizon_id")
            start = _time_key(outcome_meta.get("outcome_start"), "LFREAL1 outcome_start")
            end = _time_key(outcome_meta.get("outcome_end"), "LFREAL1 outcome_end")
            if start <= evidence_as_of:
                raise ValueError("LFREAL1 outcome_start는 evidence.as_of 이후여야 합니다.")
            if end < start:
                raise ValueError("LFREAL1 outcome_end는 outcome_start보다 빠를 수 없습니다.")

    def as_lfout1_partition(self) -> FollowerOutcomePartition:
        self.validate()
        return FollowerOutcomePartition(
            partition_id=self.partition_id,
            role=self.role,
            evidence_rows=tuple(self.evidence_rows),
            outcomes=tuple(self.outcomes),
            metadata=dict(self.metadata),
        )


class MultiSymbolFollowerRealEvidenceStudy:
    @classmethod
    def run(
        cls,
        *,
        partitions: Sequence[RealEvidenceStudyPartition],
        outcome_contract: FollowerOutcomeContract | None = None,
    ) -> dict[str, Any]:
        frozen = tuple(partitions)
        if not frozen:
            raise ValueError("LFREAL1 partitions가 비어 있습니다.")
        for partition in frozen:
            if not isinstance(partition, RealEvidenceStudyPartition):
                raise ValueError("LFREAL1 partition 타입이 올바르지 않습니다.")
            partition.validate()

        lfout1 = MultiSymbolFollowerOutcomeValidationArena.run(
            partitions=tuple(partition.as_lfout1_partition() for partition in frozen),
            contract=outcome_contract,
        )
        provenance_payload = []
        for partition in frozen:
            provenance_payload.append({
                "partition_id": str(partition.partition_id).strip(),
                "provenance": tuple(sorted(
                    (item.public_dict() for item in partition.provenances),
                    key=lambda item: item["evidence_hash"],
                )),
            })
        provenance_payload = tuple(sorted(provenance_payload, key=lambda item: item["partition_id"]))

        payload = {
            "schema": SCHEMA_VERSION,
            "admission_policy": POLICY,
            "mode": "RESEARCH_EVIDENCE_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "deployment_authority": False,
            "source_content_verified": False,
            "real_data_claim": False,
            "provenance_contract_status": "PASS",
            "outcome_validation_status": lfout1["status"],
            "evidence_status": "ADMISSIBLE" if lfout1["status"] == "PASS" else "REJECTED",
            "lfout1_outcome_evidence_hash": lfout1["outcome_evidence_hash"],
            "provenance": provenance_payload,
            "selection_policy": "DECLARED_NON_FIXTURE_PROVENANCE_AND_LFOUT1_PASS_NO_HIDDEN_SCORE",
        }
        payload["real_evidence_admission_hash"] = _stable_hash(payload)
        return payload
