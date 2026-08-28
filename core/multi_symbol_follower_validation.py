"""Partitioned validation for frozen LF2 follower-intent evidence.

LFVAL1 evaluates already-produced observation-only LF2 evidence across explicit
TRAIN / VALIDATION / OOS / HARSH partitions. It does not replay tactics, produce
orders, publish deployment gates, or acquire operational authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "multi_symbol_follower_validation/v1"
CONTRACT_SCHEMA_VERSION = "multi_symbol_follower_validation_contract/v1"
VALIDATION_POLICY = "LF2_FROZEN_EVIDENCE_TRAIN_VALIDATION_OOS_HARSH_DECLARED_AXES_NO_HIDDEN_SCORE"
_ALLOWED_ROLES = {"TRAIN", "VALIDATION", "OOS", "HARSH"}
_ROLE_ORDER = {"TRAIN": 0, "VALIDATION": 1, "OOS": 2, "HARSH": 3}
_ALLOWED_INTENTS = {"ARM_PENDING", "HOLD", "HOLD_PENDING", "CANCEL_PENDING"}


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _rate(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 0..1 NUMBER여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 0..1 NUMBER여야 합니다.") from exc
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{label}은 0..1 범위여야 합니다.")
    return number


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_row(row: Mapping[str, Any]) -> None:
    if not isinstance(row, Mapping):
        raise ValueError("LFVAL1 row는 Mapping이어야 합니다.")
    if str(row.get("schema") or "") != "multi_symbol_follower_pending_orchestration/v1":
        raise ValueError("LFVAL1은 LF2 v1 evidence만 허용합니다.")
    if str(row.get("mode") or "") != "OBSERVATION_ONLY":
        raise ValueError("LFVAL1은 OBSERVATION_ONLY evidence만 허용합니다.")
    if bool(row.get("operational_authority", False)) or bool(row.get("execution_authority", False)):
        raise ValueError("LFVAL1 입력 evidence에 operational/execution authority가 있으면 안 됩니다.")
    _text(row.get("evidence_hash"), "LFVAL1 evidence_hash")
    _text(row.get("relation_result_hash"), "LFVAL1 relation_result_hash")
    _text(row.get("policy_hash"), "LFVAL1 policy_hash")
    _text(row.get("as_of"), "LFVAL1 as_of")
    _text(row.get("follower_symbol"), "LFVAL1 follower_symbol")
    intent = _text(row.get("intent"), "LFVAL1 intent")
    if intent not in _ALLOWED_INTENTS:
        raise ValueError(f"LFVAL1 지원하지 않는 intent: {intent}")

    required_arm = bool(
        row.get("selection_qualified")
        and row.get("local_setup_pass")
        and row.get("hard_guard_pass")
        and row.get("relation_still_valid")
        and not row.get("pending_order_active")
    )
    if intent == "ARM_PENDING" and not required_arm:
        raise ValueError("LFVAL1 unsafe ARM evidence를 허용하지 않습니다.")
    active_invalid = bool(
        row.get("pending_order_active")
        and (
            not row.get("selection_qualified")
            or not row.get("local_setup_pass")
            or not row.get("hard_guard_pass")
            or not row.get("relation_still_valid")
        )
    )
    if active_invalid and intent != "CANCEL_PENDING":
        raise ValueError("LFVAL1 active invalid pending은 CANCEL_PENDING이어야 합니다.")


@dataclass(frozen=True)
class FollowerValidationPartition:
    partition_id: str
    role: str
    rows: Sequence[Mapping[str, Any]]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized_role(self) -> str:
        return str(self.role or "").strip().upper()

    def validate(self) -> None:
        _text(self.partition_id, "LFVAL1 partition_id")
        role = self.normalized_role()
        if role not in _ALLOWED_ROLES:
            raise ValueError(f"LFVAL1 지원하지 않는 role: {self.role!r}")
        if role == "HARSH" and not str(self.metadata.get("adverse_reason") or "").strip():
            raise ValueError("LFVAL1 HARSH partition은 adverse_reason이 필요합니다.")
        frozen = tuple(self.rows)
        if not frozen:
            raise ValueError("LFVAL1 partition rows가 비어 있습니다.")
        hashes = []
        for row in frozen:
            _validate_row(row)
            hashes.append(str(row["evidence_hash"]))
        if len(set(hashes)) != len(hashes):
            raise ValueError("LFVAL1 partition evidence_hash에 중복이 있습니다.")


@dataclass(frozen=True)
class FollowerValidationContract:
    min_rows_per_partition: int = 2
    min_cancel_safety_rate: float = 1.0
    max_selection_qualified_rate_regression: float = 0.50
    max_arm_rate_regression: float = 0.50
    max_hard_guard_pass_rate_regression: float = 0.50
    max_relation_valid_rate_regression: float = 0.50

    def validate(self) -> None:
        if isinstance(self.min_rows_per_partition, bool) or not isinstance(self.min_rows_per_partition, int) or self.min_rows_per_partition < 1:
            raise ValueError("LFVAL1 min_rows_per_partition은 1 이상의 int여야 합니다.")
        for name in (
            "min_cancel_safety_rate",
            "max_selection_qualified_rate_regression",
            "max_arm_rate_regression",
            "max_hard_guard_pass_rate_regression",
            "max_relation_valid_rate_regression",
        ):
            _rate(getattr(self, name), f"LFVAL1 {name}")

    @property
    def contract_hash(self) -> str:
        self.validate()
        return _stable_hash({
            "schema": CONTRACT_SCHEMA_VERSION,
            "min_rows_per_partition": self.min_rows_per_partition,
            "min_cancel_safety_rate": self.min_cancel_safety_rate,
            "max_selection_qualified_rate_regression": self.max_selection_qualified_rate_regression,
            "max_arm_rate_regression": self.max_arm_rate_regression,
            "max_hard_guard_pass_rate_regression": self.max_hard_guard_pass_rate_regression,
            "max_relation_valid_rate_regression": self.max_relation_valid_rate_regression,
        })


class MultiSymbolFollowerValidationArena:
    @staticmethod
    def _normalize(partitions: Sequence[FollowerValidationPartition]) -> tuple[FollowerValidationPartition, ...]:
        frozen = tuple(partitions)
        if not frozen:
            raise ValueError("LFVAL1 partitions가 비어 있습니다.")
        counts = {role: 0 for role in _ALLOWED_ROLES}
        ids = []
        all_hashes = []
        policy_hashes = set()
        for partition in frozen:
            if not isinstance(partition, FollowerValidationPartition):
                raise ValueError("LFVAL1 partition 타입이 올바르지 않습니다.")
            partition.validate()
            ids.append(str(partition.partition_id).strip())
            counts[partition.normalized_role()] += 1
            for row in partition.rows:
                all_hashes.append(str(row["evidence_hash"]))
                policy_hashes.add(str(row["policy_hash"]))
        if len(set(ids)) != len(ids):
            raise ValueError("LFVAL1 partition_id에 중복이 있습니다.")
        for role in ("TRAIN", "VALIDATION", "OOS"):
            if counts[role] != 1:
                raise ValueError(f"LFVAL1은 {role} partition을 정확히 1개 요구합니다.")
        if counts["HARSH"] < 1:
            raise ValueError("LFVAL1은 HARSH partition을 최소 1개 요구합니다.")
        if len(set(all_hashes)) != len(all_hashes):
            raise ValueError("LFVAL1 evidence_hash는 partition 간에도 전역적으로 분리되어야 합니다.")
        if len(policy_hashes) != 1:
            raise ValueError("LFVAL1 partitions는 동일 LF2 policy_hash를 사용해야 합니다.")
        return tuple(sorted(frozen, key=lambda item: (_ROLE_ORDER[item.normalized_role()], str(item.partition_id))))

    @staticmethod
    def _metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        frozen = tuple(rows)
        total = len(frozen)
        qualified = sum(bool(row.get("selection_qualified")) for row in frozen)
        arms = sum(str(row.get("intent")) == "ARM_PENDING" for row in frozen)
        guards = sum(bool(row.get("hard_guard_pass")) for row in frozen)
        relation_valid = sum(bool(row.get("relation_still_valid")) for row in frozen)
        active_invalid = [
            row for row in frozen
            if bool(row.get("pending_order_active")) and (
                not row.get("selection_qualified")
                or not row.get("local_setup_pass")
                or not row.get("hard_guard_pass")
                or not row.get("relation_still_valid")
            )
        ]
        safe_cancels = sum(str(row.get("intent")) == "CANCEL_PENDING" for row in active_invalid)
        cancel_safety_rate = 1.0 if not active_invalid else safe_cancels / len(active_invalid)
        return {
            "row_count": total,
            "selection_qualified_rate": qualified / total,
            "arm_rate": arms / total,
            "hard_guard_pass_rate": guards / total,
            "relation_valid_rate": relation_valid / total,
            "active_invalid_count": len(active_invalid),
            "cancel_safety_rate": cancel_safety_rate,
        }

    @classmethod
    def run(
        cls,
        *,
        partitions: Sequence[FollowerValidationPartition],
        contract: FollowerValidationContract | None = None,
    ) -> dict[str, Any]:
        resolved_contract = contract or FollowerValidationContract()
        resolved_contract.validate()
        ordered = cls._normalize(partitions)
        train = next(item for item in ordered if item.normalized_role() == "TRAIN")
        train_metrics = cls._metrics(train.rows)
        rows_out = []
        all_pass = True
        for partition in ordered:
            metrics = cls._metrics(partition.rows)
            violations = []
            if metrics["row_count"] < resolved_contract.min_rows_per_partition:
                violations.append("insufficient_rows")
            if metrics["cancel_safety_rate"] < resolved_contract.min_cancel_safety_rate:
                violations.append("cancel_safety_regression")
            if partition.normalized_role() != "TRAIN":
                checks = (
                    ("selection_qualified_rate", resolved_contract.max_selection_qualified_rate_regression),
                    ("arm_rate", resolved_contract.max_arm_rate_regression),
                    ("hard_guard_pass_rate", resolved_contract.max_hard_guard_pass_rate_regression),
                    ("relation_valid_rate", resolved_contract.max_relation_valid_rate_regression),
                )
                for metric_name, tolerance in checks:
                    if train_metrics[metric_name] - metrics[metric_name] > tolerance:
                        violations.append(f"{metric_name}_regression")
            status = "PASS" if not violations else "FAIL"
            all_pass = all_pass and status == "PASS"
            partition_payload = {
                "partition_id": str(partition.partition_id).strip(),
                "role": partition.normalized_role(),
                "metrics": metrics,
                "violations": tuple(violations),
                "status": status,
                "metadata": dict(partition.metadata),
            }
            partition_payload["partition_hash"] = _stable_hash(partition_payload)
            rows_out.append(partition_payload)

        payload = {
            "schema": SCHEMA_VERSION,
            "validation_policy": VALIDATION_POLICY,
            "mode": "EVIDENCE_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "status": "PASS" if all_pass else "FAIL",
            "evidence_status": "VALIDATED" if all_pass else "REJECTED",
            "deployment_authority": False,
            "contract_hash": resolved_contract.contract_hash,
            "partitions": tuple(rows_out),
            "selection_policy": "ALL_DECLARED_PARTITIONS_PASS_NO_HIDDEN_SCORE",
        }
        payload["validation_evidence_hash"] = _stable_hash(payload)
        return payload
