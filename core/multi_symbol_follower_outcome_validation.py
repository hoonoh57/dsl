"""Bounded outcome validation for frozen LF2 observation evidence.

LFOUT1 joins already-produced LF2 evidence to separately frozen outcome rows by
exact evidence_hash. It does not replay tactics, call execution services, publish
selection gates, or acquire operational authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from statistics import mean
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "multi_symbol_follower_outcome_validation/v1"
CONTRACT_SCHEMA_VERSION = "multi_symbol_follower_outcome_contract/v1"
POLICY = "LF2_FROZEN_EVIDENCE_EXACT_OUTCOME_JOIN_TRAIN_VALIDATION_OOS_HARSH_NO_HIDDEN_SCORE"
_ALLOWED_ROLES = {"TRAIN", "VALIDATION", "OOS", "HARSH"}
_ROLE_ORDER = {"TRAIN": 0, "VALIDATION": 1, "OOS": 2, "HARSH": 3}


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한 NUMBER여야 합니다.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한 NUMBER여야 합니다.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return result


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_evidence(row: Mapping[str, Any]) -> None:
    if not isinstance(row, Mapping):
        raise ValueError("LFOUT1 evidence는 Mapping이어야 합니다.")
    if str(row.get("schema") or "") != "multi_symbol_follower_pending_orchestration/v1":
        raise ValueError("LFOUT1은 LF2 v1 evidence만 허용합니다.")
    if str(row.get("mode") or "") != "OBSERVATION_ONLY":
        raise ValueError("LFOUT1은 OBSERVATION_ONLY evidence만 허용합니다.")
    if bool(row.get("operational_authority")) or bool(row.get("execution_authority")):
        raise ValueError("LFOUT1 입력 evidence에 operational/execution authority가 있으면 안 됩니다.")
    _text(row.get("evidence_hash"), "LFOUT1 evidence_hash")
    _text(row.get("policy_hash"), "LFOUT1 policy_hash")
    _text(row.get("intent"), "LFOUT1 intent")


@dataclass(frozen=True)
class FrozenFollowerOutcome:
    evidence_hash: str
    forward_return_pct: float
    mfe_pct: float
    mae_pct: float
    realized: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.evidence_hash, "LFOUT1 outcome evidence_hash")
        _finite(self.forward_return_pct, "forward_return_pct")
        _finite(self.mfe_pct, "mfe_pct")
        _finite(self.mae_pct, "mae_pct")
        if type(self.realized) is not bool:
            raise ValueError("LFOUT1 realized는 bool이어야 합니다.")

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "evidence_hash": str(self.evidence_hash).strip(),
            "forward_return_pct": float(self.forward_return_pct),
            "mfe_pct": float(self.mfe_pct),
            "mae_pct": float(self.mae_pct),
            "realized": bool(self.realized),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FollowerOutcomePartition:
    partition_id: str
    role: str
    evidence_rows: Sequence[Mapping[str, Any]]
    outcomes: Sequence[FrozenFollowerOutcome]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized_role(self) -> str:
        return str(self.role or "").strip().upper()

    def validate(self) -> None:
        _text(self.partition_id, "LFOUT1 partition_id")
        role = self.normalized_role()
        if role not in _ALLOWED_ROLES:
            raise ValueError(f"LFOUT1 지원하지 않는 role: {self.role!r}")
        if role == "HARSH" and not str(self.metadata.get("adverse_reason") or "").strip():
            raise ValueError("LFOUT1 HARSH partition은 adverse_reason이 필요합니다.")
        evidence = tuple(self.evidence_rows)
        outcomes = tuple(self.outcomes)
        if not evidence or not outcomes:
            raise ValueError("LFOUT1 partition evidence/outcomes가 비어 있으면 안 됩니다.")
        hashes = []
        for row in evidence:
            _validate_evidence(row)
            hashes.append(str(row["evidence_hash"]))
        if len(set(hashes)) != len(hashes):
            raise ValueError("LFOUT1 evidence_hash에 중복이 있습니다.")
        outcome_hashes = []
        for outcome in outcomes:
            if not isinstance(outcome, FrozenFollowerOutcome):
                raise ValueError("LFOUT1 outcome 타입이 올바르지 않습니다.")
            outcome.validate()
            outcome_hashes.append(str(outcome.evidence_hash).strip())
        if len(set(outcome_hashes)) != len(outcome_hashes):
            raise ValueError("LFOUT1 outcome evidence_hash에 중복이 있습니다.")
        if set(hashes) != set(outcome_hashes):
            missing = sorted(set(hashes) - set(outcome_hashes))
            extra = sorted(set(outcome_hashes) - set(hashes))
            raise ValueError(f"LFOUT1 exact outcome coverage가 필요합니다: missing={missing}, extra={extra}")


@dataclass(frozen=True)
class FollowerOutcomeContract:
    min_rows_per_partition: int = 2
    min_arm_return_edge_pct: float = 0.0
    min_arm_mfe_edge_pct: float = 0.0
    max_arm_mae_regression_pct: float = 0.0
    min_cancel_avoided_loss_pct: float = 0.0
    max_holdout_edge_regression_pct: float = 1.0

    def validate(self) -> None:
        if isinstance(self.min_rows_per_partition, bool) or not isinstance(self.min_rows_per_partition, int) or self.min_rows_per_partition < 1:
            raise ValueError("LFOUT1 min_rows_per_partition은 1 이상의 int여야 합니다.")
        for name in (
            "min_arm_return_edge_pct", "min_arm_mfe_edge_pct", "max_arm_mae_regression_pct",
            "min_cancel_avoided_loss_pct", "max_holdout_edge_regression_pct",
        ):
            if _finite(getattr(self, name), f"LFOUT1 {name}") < 0.0:
                raise ValueError(f"LFOUT1 {name}는 0 이상이어야 합니다.")

    @property
    def contract_hash(self) -> str:
        self.validate()
        return _stable_hash({"schema": CONTRACT_SCHEMA_VERSION, **self.__dict__})


class MultiSymbolFollowerOutcomeValidationArena:
    @staticmethod
    def _normalize(partitions: Sequence[FollowerOutcomePartition]) -> tuple[FollowerOutcomePartition, ...]:
        frozen = tuple(partitions)
        if not frozen:
            raise ValueError("LFOUT1 partitions가 비어 있습니다.")
        counts = {role: 0 for role in _ALLOWED_ROLES}
        ids: list[str] = []
        hashes: list[str] = []
        policy_hashes = set()
        for partition in frozen:
            if not isinstance(partition, FollowerOutcomePartition):
                raise ValueError("LFOUT1 partition 타입이 올바르지 않습니다.")
            partition.validate()
            ids.append(str(partition.partition_id).strip())
            counts[partition.normalized_role()] += 1
            for row in partition.evidence_rows:
                hashes.append(str(row["evidence_hash"]))
                policy_hashes.add(str(row["policy_hash"]))
        if len(set(ids)) != len(ids):
            raise ValueError("LFOUT1 partition_id에 중복이 있습니다.")
        for role in ("TRAIN", "VALIDATION", "OOS"):
            if counts[role] != 1:
                raise ValueError(f"LFOUT1은 {role} partition을 정확히 1개 요구합니다.")
        if counts["HARSH"] < 1:
            raise ValueError("LFOUT1은 HARSH partition을 최소 1개 요구합니다.")
        if len(set(hashes)) != len(hashes):
            raise ValueError("LFOUT1 evidence_hash는 partition 간 전역적으로 분리되어야 합니다.")
        if len(policy_hashes) != 1:
            raise ValueError("LFOUT1 partitions는 동일 LF2 policy_hash를 사용해야 합니다.")
        return tuple(sorted(frozen, key=lambda item: (_ROLE_ORDER[item.normalized_role()], str(item.partition_id))))

    @staticmethod
    def _metrics(partition: FollowerOutcomePartition) -> dict[str, Any]:
        by_hash = {item.evidence_hash: item for item in partition.outcomes}
        arms = [by_hash[str(row["evidence_hash"])] for row in partition.evidence_rows if str(row.get("intent")) == "ARM_PENDING"]
        non_arms = [by_hash[str(row["evidence_hash"])] for row in partition.evidence_rows if str(row.get("intent")) != "ARM_PENDING"]
        cancels = [by_hash[str(row["evidence_hash"])] for row in partition.evidence_rows if str(row.get("intent")) == "CANCEL_PENDING"]
        def avg(rows: Sequence[FrozenFollowerOutcome], attr: str) -> float:
            return mean(float(getattr(item, attr)) for item in rows) if rows else 0.0
        arm_return = avg(arms, "forward_return_pct")
        non_arm_return = avg(non_arms, "forward_return_pct")
        arm_mfe = avg(arms, "mfe_pct")
        non_arm_mfe = avg(non_arms, "mfe_pct")
        arm_mae = avg(arms, "mae_pct")
        non_arm_mae = avg(non_arms, "mae_pct")
        cancel_avoided_loss = mean(max(0.0, -float(item.forward_return_pct)) for item in cancels) if cancels else 0.0
        return {
            "row_count": len(partition.evidence_rows),
            "arm_count": len(arms),
            "non_arm_count": len(non_arms),
            "cancel_count": len(cancels),
            "arm_return_edge_pct": arm_return - non_arm_return,
            "arm_mfe_edge_pct": arm_mfe - non_arm_mfe,
            "arm_mae_regression_pct": max(0.0, arm_mae - non_arm_mae),
            "cancel_avoided_loss_pct": cancel_avoided_loss,
        }

    @classmethod
    def run(cls, *, partitions: Sequence[FollowerOutcomePartition], contract: FollowerOutcomeContract | None = None) -> dict[str, Any]:
        resolved = contract or FollowerOutcomeContract()
        resolved.validate()
        ordered = cls._normalize(partitions)
        train = next(item for item in ordered if item.normalized_role() == "TRAIN")
        train_metrics = cls._metrics(train)
        rows_out = []
        all_pass = True
        for partition in ordered:
            metrics = cls._metrics(partition)
            violations = []
            if metrics["row_count"] < resolved.min_rows_per_partition:
                violations.append("insufficient_rows")
            if metrics["arm_count"] == 0 or metrics["non_arm_count"] == 0:
                violations.append("insufficient_comparison_activity")
            if metrics["arm_return_edge_pct"] < resolved.min_arm_return_edge_pct:
                violations.append("arm_return_edge")
            if metrics["arm_mfe_edge_pct"] < resolved.min_arm_mfe_edge_pct:
                violations.append("arm_mfe_edge")
            if metrics["arm_mae_regression_pct"] > resolved.max_arm_mae_regression_pct:
                violations.append("arm_mae_regression")
            if metrics["cancel_count"] and metrics["cancel_avoided_loss_pct"] < resolved.min_cancel_avoided_loss_pct:
                violations.append("cancel_avoided_loss")
            if partition.normalized_role() != "TRAIN":
                if train_metrics["arm_return_edge_pct"] - metrics["arm_return_edge_pct"] > resolved.max_holdout_edge_regression_pct:
                    violations.append("holdout_return_edge_regression")
            status = "PASS" if not violations else "FAIL"
            all_pass = all_pass and status == "PASS"
            row = {
                "partition_id": str(partition.partition_id).strip(),
                "role": partition.normalized_role(),
                "metrics": metrics,
                "violations": tuple(violations),
                "status": status,
                "metadata": dict(partition.metadata),
            }
            row["partition_hash"] = _stable_hash(row)
            rows_out.append(row)
        payload = {
            "schema": SCHEMA_VERSION,
            "validation_policy": POLICY,
            "mode": "EVIDENCE_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "deployment_authority": False,
            "status": "PASS" if all_pass else "FAIL",
            "evidence_status": "VALIDATED" if all_pass else "REJECTED",
            "contract_hash": resolved.contract_hash,
            "partitions": tuple(rows_out),
            "selection_policy": "ALL_DECLARED_OUTCOME_AXES_PASS_NO_HIDDEN_SCORE",
        }
        payload["outcome_evidence_hash"] = _stable_hash(payload)
        return payload
