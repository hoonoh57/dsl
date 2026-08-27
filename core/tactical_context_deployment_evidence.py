"""Validated deployment-policy evidence bridge for registered parent context.

CTXDEP1 is deliberately non-operational. It consumes one immutable CTXVAL1
validation-arena result, verifies the arena identity, selects one independently
validated registered context slice, and produces an E8 ContextDeploymentPolicy
whose validation_evidence_hash is anchored to that slice.

This module never calls BacktestEngine, DSLRuntime, BrokerEmulator, providers,
or installs an entry gate. The output is policy evidence only.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

from core.tactical_context_attribution import ContextDeploymentPolicy, ContextSliceRule
from core.tactical_context_validation import (
    CONTEXT_POLICY as CTXVAL1_CONTEXT_POLICY,
    EXECUTION_INTEGRATION as CTXVAL1_EXECUTION_INTEGRATION,
    SCHEMA_VERSION as CTXVAL1_SCHEMA_VERSION,
    VALIDATION_POLICY as CTXVAL1_VALIDATION_POLICY,
)


SCHEMA_VERSION = "validated_context_deployment_policy_evidence/v1"
PROMOTION_POLICY = (
    "CTXVAL1_VALIDATED_SLICE_TO_E8_DEPLOYMENT_POLICY_EVIDENCE_"
    "NO_ENTRY_GATE_NO_BROKER_AUTHORITY"
)
EXECUTION_INTEGRATION = "POLICY_EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER"


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한한 숫자여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한한 숫자여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}은 유한한 숫자여야 합니다.")
    return number


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("deployment policy evidence에 NaN/Infinity를 사용할 수 없습니다.")
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _rule_from_public(raw: Mapping[str, Any]) -> ContextSliceRule:
    if not isinstance(raw, Mapping):
        raise ValueError("validated slice rule은 Mapping이어야 합니다.")
    rule = ContextSliceRule(
        slice_id=_text(raw.get("slice_id"), "validated slice rule.slice_id"),
        layer=_text(raw.get("layer"), "validated slice rule.layer"),
        context_id=_text(raw.get("context_id"), "validated slice rule.context_id"),
        feature_key=_text(raw.get("feature_key"), "validated slice rule.feature_key"),
        operator=_text(raw.get("operator"), "validated slice rule.operator"),
        value=raw.get("value"),
        metadata=dict(raw.get("metadata") or {}),
    )
    rule.validate()
    return rule


def _validate_arena(arena: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(arena, Mapping):
        raise ValueError("CTXDEP1 validation_arena는 Mapping이어야 합니다.")
    frozen = dict(arena)
    if frozen.get("schema") != CTXVAL1_SCHEMA_VERSION:
        raise ValueError("CTXDEP1은 tactical_context_validation_arena/v1만 허용합니다.")
    if frozen.get("validation_policy") != CTXVAL1_VALIDATION_POLICY:
        raise ValueError("CTXDEP1 validation_policy가 CTXVAL1과 다릅니다.")
    if frozen.get("context_policy") != CTXVAL1_CONTEXT_POLICY:
        raise ValueError("CTXDEP1 context_policy가 CTXVAL1과 다릅니다.")
    if frozen.get("operational_authority") is not False:
        raise ValueError("CTXDEP1 source arena는 operational_authority=false여야 합니다.")
    if frozen.get("execution_integration") != CTXVAL1_EXECUTION_INTEGRATION:
        raise ValueError("CTXDEP1 source arena execution integration이 CTXVAL1과 다릅니다.")

    candidate_hash = _text(frozen.get("candidate_hash"), "CTXVAL1 candidate_hash")
    contract = frozen.get("contract")
    if not isinstance(contract, Mapping):
        raise ValueError("CTXVAL1 contract evidence가 필요합니다.")
    contract_hash = _text(contract.get("contract_hash"), "CTXVAL1 contract_hash")
    partitions = tuple(frozen.get("partitions") or ())
    slices = tuple(frozen.get("slices") or ())
    if not partitions or not slices:
        raise ValueError("CTXVAL1 partitions/slices evidence가 비어 있습니다.")
    if any(not isinstance(item, Mapping) for item in partitions + slices):
        raise ValueError("CTXVAL1 partitions/slices evidence 타입이 올바르지 않습니다.")

    partition_ids = [_text(item.get("partition_id"), "CTXVAL1 partition_id") for item in partitions]
    if len(set(partition_ids)) != len(partition_ids):
        raise ValueError("CTXVAL1 partition_id에 중복이 있습니다.")
    roles = [str(item.get("role") or "").strip().upper() for item in partitions]
    if roles.count("TRAIN") != 1 or roles.count("VALIDATION") != 1 or roles.count("OOS") != 1:
        raise ValueError("CTXVAL1 TRAIN/VALIDATION/OOS partition evidence가 완전하지 않습니다.")
    if roles.count("HARSH") < 1:
        raise ValueError("CTXVAL1 HARSH partition evidence가 필요합니다.")
    for item in partitions:
        _text(item.get("attribution_hash"), "CTXVAL1 partition attribution_hash")

    slice_ids = [_text(item.get("slice_id"), "CTXVAL1 slice_id") for item in slices]
    if len(set(slice_ids)) != len(slice_ids):
        raise ValueError("CTXVAL1 slice_id에 중복이 있습니다.")

    identity = {
        "schema": CTXVAL1_SCHEMA_VERSION,
        "validation_policy": CTXVAL1_VALIDATION_POLICY,
        "context_policy": CTXVAL1_CONTEXT_POLICY,
        "candidate_hash": candidate_hash,
        "contract_hash": contract_hash,
        "partitions": partitions,
        "slices": slices,
    }
    expected_arena_hash = _stable_hash(identity)
    actual_arena_hash = _text(frozen.get("arena_hash"), "CTXVAL1 arena_hash")
    if actual_arena_hash != expected_arena_hash:
        raise ValueError("CTXVAL1 arena_hash가 validation evidence payload와 일치하지 않습니다.")

    validated_ids = tuple(str(item).strip() for item in tuple(frozen.get("validated_slice_ids") or ()))
    rejected_ids = tuple(str(item).strip() for item in tuple(frozen.get("rejected_slice_ids") or ()))
    calculated_validated = tuple(item["slice_id"] for item in slices if item.get("status") == "PASS")
    calculated_rejected = tuple(item["slice_id"] for item in slices if item.get("status") != "PASS")
    if validated_ids != calculated_validated or rejected_ids != calculated_rejected:
        raise ValueError("CTXVAL1 validated/rejected slice 목록이 slice evidence와 일치하지 않습니다.")
    expected_status = "PASS" if calculated_validated and not calculated_rejected else (
        "MIXED" if calculated_validated else "FAIL"
    )
    if str(frozen.get("arena_status") or "").strip().upper() != expected_status:
        raise ValueError("CTXVAL1 arena_status가 slice evidence와 일치하지 않습니다.")
    return frozen


@dataclass(frozen=True)
class ValidatedContextDeploymentPolicyEvidence:
    """Non-operational E8 policy evidence anchored to one CTXVAL1 validated slice."""

    policy: ContextDeploymentPolicy
    feature_id: str
    required_manifest_hash: str
    validation_arena_hash: str
    validation_evidence_hash: str
    validation_contract_hash: str
    partition_attribution_hashes: tuple[tuple[str, str], ...]

    def validate(self) -> None:
        if not isinstance(self.policy, ContextDeploymentPolicy):
            raise ValueError("deployment policy evidence policy 타입이 올바르지 않습니다.")
        self.policy.validate()
        if str(self.policy.evidence_status).strip().upper() != "VALIDATED":
            raise ValueError("deployment policy evidence는 VALIDATED policy만 허용합니다.")
        feature_id = _text(self.feature_id, "deployment evidence feature_id")
        required_manifest_hash = _text(
            self.required_manifest_hash, "deployment evidence required_manifest_hash"
        )
        _text(self.validation_arena_hash, "deployment evidence validation_arena_hash")
        validation_evidence_hash = _text(
            self.validation_evidence_hash, "deployment evidence validation_evidence_hash"
        )
        _text(self.validation_contract_hash, "deployment evidence validation_contract_hash")
        if validation_evidence_hash != str(self.policy.validation_evidence_hash).strip():
            raise ValueError("deployment policy validation_evidence_hash가 CTXVAL1 evidence와 다릅니다.")
        layer_prefix = str(self.policy.rule.layer).strip().lower() + "."
        if not feature_id.lower().startswith(layer_prefix):
            raise ValueError("deployment evidence feature_id가 policy rule layer와 다릅니다.")
        if not required_manifest_hash:
            raise ValueError("deployment evidence required_manifest_hash가 필요합니다.")
        if not self.partition_attribution_hashes:
            raise ValueError("deployment evidence partition attribution이 비어 있습니다.")
        ids = []
        for partition_id, attribution_hash in self.partition_attribution_hashes:
            ids.append(_text(partition_id, "deployment evidence partition_id"))
            _text(attribution_hash, "deployment evidence attribution_hash")
        if len(set(ids)) != len(ids):
            raise ValueError("deployment evidence partition_id에 중복이 있습니다.")
        train_hashes = [
            attribution_hash
            for partition_id, attribution_hash in self.partition_attribution_hashes
            if str(partition_id).strip().upper().startswith("TRAIN")
        ]
        # Partition IDs are caller-defined, so policy.attribution_hash is checked
        # against the selected TRAIN role at creation time rather than inferred here.
        _json_safe(self.public_dict(include_hash=False))

    def public_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema": SCHEMA_VERSION,
            "promotion_policy": PROMOTION_POLICY,
            "policy": self.policy.public_dict(),
            "policy_hash": self.policy.policy_hash,
            "feature_id": str(self.feature_id).strip(),
            "required_manifest_hash": str(self.required_manifest_hash).strip(),
            "validation_arena_hash": str(self.validation_arena_hash).strip(),
            "validation_evidence_hash": str(self.validation_evidence_hash).strip(),
            "validation_contract_hash": str(self.validation_contract_hash).strip(),
            "partition_attribution_hashes": tuple(self.partition_attribution_hashes),
            "policy_evidence_validated": True,
            "operational_authority": False,
            "execution_integration": EXECUTION_INTEGRATION,
        }
        if include_hash:
            payload["evidence_hash"] = self.evidence_hash
        return payload

    @property
    def evidence_hash(self) -> str:
        self.validate()
        return _stable_hash(self.public_dict(include_hash=False))


class ValidatedContextDeploymentPolicyFactory:
    """Promote only one independently validated CTXVAL1 slice into E8 policy evidence."""

    @classmethod
    def create(
        cls,
        *,
        validation_arena: Mapping[str, Any],
        slice_id: str,
        policy_id: str,
        policy_version: str,
        priority_if_allowed: float = 0.0,
    ) -> ValidatedContextDeploymentPolicyEvidence:
        arena = _validate_arena(validation_arena)
        wanted_slice_id = _text(slice_id, "deployment evidence slice_id")
        matches = [item for item in arena["slices"] if str(item.get("slice_id") or "").strip() == wanted_slice_id]
        if len(matches) != 1:
            raise ValueError("요청한 CTXVAL1 slice를 정확히 하나 찾을 수 없습니다.")
        selected = dict(matches[0])
        if selected.get("status") != "PASS":
            raise ValueError("CTXDEP1은 CTXVAL1 PASS slice만 승격할 수 있습니다.")
        if str(selected.get("evidence_status") or "").strip().upper() != "VALIDATED":
            raise ValueError("CTXDEP1 slice evidence_status는 VALIDATED여야 합니다.")
        if selected.get("deployment_policy_evidence_eligible") is not True:
            raise ValueError("CTXDEP1 slice는 deployment-policy evidence eligible이어야 합니다.")
        if selected.get("operational_authority") is not False:
            raise ValueError("CTXDEP1 source slice는 operational_authority=false여야 합니다.")

        feature_id = _text(selected.get("feature_id"), "CTXVAL1 selected feature_id")
        required_manifest_hash = _text(
            selected.get("required_manifest_hash"), "CTXVAL1 selected required_manifest_hash"
        )
        validation_evidence_hash = _text(
            selected.get("validation_evidence_hash"), "CTXVAL1 selected validation_evidence_hash"
        )
        rule = _rule_from_public(selected.get("rule") or {})
        if rule.slice_id != wanted_slice_id:
            raise ValueError("CTXVAL1 selected rule.slice_id가 요청 slice_id와 다릅니다.")
        if not feature_id.lower().startswith(str(rule.layer).strip().lower() + "."):
            raise ValueError("CTXVAL1 selected feature_id가 rule layer namespace와 다릅니다.")

        partition_evidence = tuple(selected.get("partition_evidence") or ())
        if not partition_evidence:
            raise ValueError("CTXVAL1 selected partition evidence가 비어 있습니다.")
        if any(item.get("status") != "PASS" for item in partition_evidence):
            raise ValueError("CTXVAL1 selected slice의 모든 partition이 PASS여야 합니다.")
        role_rows = {str(item.get("role") or "").strip().upper(): item for item in partition_evidence}
        if set(("TRAIN", "VALIDATION", "OOS")) - set(role_rows):
            raise ValueError("CTXVAL1 selected slice의 TRAIN/VALIDATION/OOS evidence가 완전하지 않습니다.")
        if "HARSH" not in role_rows:
            raise ValueError("CTXVAL1 selected slice의 HARSH evidence가 필요합니다.")
        train_attribution_hash = _text(
            role_rows["TRAIN"].get("attribution_hash"), "CTXVAL1 TRAIN attribution_hash"
        )

        policy = ContextDeploymentPolicy(
            policy_id=_text(policy_id, "deployment policy_id"),
            policy_version=_text(policy_version, "deployment policy_version"),
            tactic_id=_text(arena.get("candidate_hash"), "CTXVAL1 candidate_hash"),
            rule=rule,
            attribution_hash=train_attribution_hash,
            evidence_status="VALIDATED",
            validation_evidence_hash=validation_evidence_hash,
            priority_if_allowed=_finite(priority_if_allowed, "priority_if_allowed"),
        )
        policy.validate()

        attribution_rows = tuple(
            (str(item["partition_id"]).strip(), str(item["attribution_hash"]).strip())
            for item in arena["partitions"]
        )
        evidence = ValidatedContextDeploymentPolicyEvidence(
            policy=policy,
            feature_id=feature_id,
            required_manifest_hash=required_manifest_hash,
            validation_arena_hash=_text(arena.get("arena_hash"), "CTXVAL1 arena_hash"),
            validation_evidence_hash=validation_evidence_hash,
            validation_contract_hash=_text(
                arena["contract"].get("contract_hash"), "CTXVAL1 contract_hash"
            ),
            partition_attribution_hashes=attribution_rows,
        )
        evidence.validate()
        return evidence
