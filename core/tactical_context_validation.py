"""Partitioned validation arena for registered parent-context attribution.

CTXVAL1 reuses E8 TacticalContextAttributor over frozen NEUTRAL tactical
profiles, but adds explicit TRAIN / VALIDATION / OOS / HARSH evidence gates.
It validates already-produced PCTX1 OBSERVED BattlefieldContext snapshots only.
It never reruns a tactic, calls providers, installs an entry gate, or calls the
Broker.  Passing evidence may later be referenced by an explicit E8 deployment
policy, but this module itself has no operational authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from core.battlefield_context import BattlefieldContext
from core.tactical_context_attribution import ContextSliceRule, TacticalContextAttributor


SCHEMA_VERSION = "tactical_context_validation_arena/v1"
CONTRACT_SCHEMA_VERSION = "tactical_context_validation_contract/v1"
SLICE_SCHEMA_VERSION = "registered_context_validation_slice/v1"
VALIDATION_POLICY = (
    "PARTITIONED_E8_ATTRIBUTION_TRAIN_VALIDATION_OOS_HARSH_"
    "DECLARED_AXES_NO_HIDDEN_SCORE"
)
CONTEXT_POLICY = "EXACT_REGISTERED_PCTX1_OBSERVED_CONTEXT_ONLY"
EXECUTION_INTEGRATION = "EVIDENCE_ONLY_NOT_WIRED_TO_ENTRY_GATE_OR_BROKER"
_ALLOWED_ROLES = {"TRAIN", "VALIDATION", "OOS", "HARSH"}
_ROLE_ORDER = {"TRAIN": 0, "VALIDATION": 1, "OOS": 2, "HARSH": 3}


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"context validation time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return number


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("context validation evidence에 NaN/Infinity를 사용할 수 없습니다.")
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


def _profile_identity(profile: Mapping[str, Any]) -> tuple[str, str, str, tuple[str, ...]]:
    if not isinstance(profile, Mapping):
        raise ValueError("context validation profile은 Mapping이어야 합니다.")
    if str(profile.get("schema") or "") != "tactical_discovery/v1":
        raise ValueError("context validation profile은 tactical_discovery/v1이어야 합니다.")
    run_hash = _text(profile.get("run_hash"), "profile.run_hash")
    case_set_hash = _text(profile.get("case_set_hash"), "profile.case_set_hash")
    candidate = profile.get("candidate") or {}
    if not isinstance(candidate, Mapping):
        raise ValueError("context validation profile.candidate는 Mapping이어야 합니다.")
    candidate_hash = _text(candidate.get("candidate_hash"), "profile.candidate_hash")
    policy = profile.get("context_policy") or {}
    if not isinstance(policy, Mapping) or policy.get("require_neutral_context") is not True:
        raise ValueError("context validation은 NEUTRAL tactical profile만 허용합니다.")
    rows = tuple(profile.get("results") or ())
    if not rows:
        raise ValueError("context validation profile results가 비어 있습니다.")
    case_ids = []
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError("context validation profile result는 Mapping이어야 합니다.")
        case_id = _text(raw.get("case_id"), "profile result.case_id")
        _time_key(raw.get("knowledge_cutoff"))
        case_ids.append(case_id)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("context validation profile case_id에 중복이 있습니다.")
    return run_hash, case_set_hash, candidate_hash, tuple(case_ids)


@dataclass(frozen=True)
class RegisteredContextSlice:
    """E8 slice rule pinned to one registered PCTX1 manifest identity."""

    feature_id: str
    required_manifest_hash: str
    rule: ContextSliceRule
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def slice_id(self) -> str:
        return str(self.rule.slice_id).strip()

    def validate(self) -> None:
        feature_id = _text(self.feature_id, "registered context feature_id")
        _text(self.required_manifest_hash, "registered context required_manifest_hash")
        if not isinstance(self.rule, ContextSliceRule):
            raise ValueError("registered context rule은 ContextSliceRule이어야 합니다.")
        self.rule.validate()
        prefix = str(self.rule.layer).strip().lower() + "."
        if not feature_id.lower().startswith(prefix):
            raise ValueError("registered context feature_id가 rule layer namespace와 다릅니다.")
        _json_safe(dict(self.metadata))

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": SLICE_SCHEMA_VERSION,
            "feature_id": str(self.feature_id).strip(),
            "required_manifest_hash": str(self.required_manifest_hash).strip(),
            "rule": self.rule.public_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ContextValidationPartition:
    """One frozen neutral profile and exact registered OBSERVED contexts."""

    partition_id: str
    role: str
    profile: Mapping[str, Any]
    contexts: Mapping[str, BattlefieldContext]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized_role(self) -> str:
        return str(self.role or "").strip().upper()

    def validate(self) -> None:
        partition_id = _text(self.partition_id, "context validation partition_id")
        role = self.normalized_role()
        if role not in _ALLOWED_ROLES:
            raise ValueError(f"지원하지 않는 context validation role: {self.role!r}")
        if role == "HARSH" and not str(self.metadata.get("adverse_reason") or "").strip():
            raise ValueError(f"HARSH context partition은 adverse_reason을 명시해야 합니다: {partition_id}")
        _, _, _, case_ids = _profile_identity(self.profile)
        supplied = {str(key): value for key, value in self.contexts.items()}
        if set(supplied) != set(case_ids):
            missing = sorted(set(case_ids) - set(supplied))
            extra = sorted(set(supplied) - set(case_ids))
            raise ValueError(
                f"context validation partition coverage가 정확히 일치해야 합니다: missing={missing}, extra={extra}"
            )
        row_by_case = {str(row["case_id"]): row for row in self.profile["results"]}
        for case_id in case_ids:
            context = supplied[case_id]
            if not isinstance(context, BattlefieldContext):
                raise ValueError(f"context validation context 타입이 올바르지 않습니다: {case_id}")
            cutoff = _time_key(row_by_case[case_id]["knowledge_cutoff"])
            context.validate_for(cutoff)
            if str(context.mode).strip().upper() != "OBSERVED":
                raise ValueError(f"context validation은 OBSERVED context만 허용합니다: {case_id}")
            if _time_key(context.as_of) != cutoff:
                raise ValueError(f"context validation은 exact context.as_of == knowledge_cutoff를 요구합니다: {case_id}")
            metadata = dict(context.metadata)
            if metadata.get("parent_feature_contract") != "parent_context_assembly/v1":
                raise ValueError(f"context validation은 PCTX1 assembly context만 허용합니다: {case_id}")
            if _time_key(metadata.get("parent_feature_knowledge_cutoff")) != cutoff:
                raise ValueError(f"PCTX1 context knowledge_cutoff metadata가 exact case cutoff와 다릅니다: {case_id}")
            manifest_hashes = tuple(str(item).strip() for item in metadata.get("parent_feature_manifest_hashes") or ())
            result_hashes = tuple(str(item).strip() for item in metadata.get("parent_feature_result_hashes") or ())
            if (
                not manifest_hashes
                or not result_hashes
                or any(not item for item in manifest_hashes + result_hashes)
                or len(set(manifest_hashes)) != len(manifest_hashes)
                or len(set(result_hashes)) != len(result_hashes)
            ):
                raise ValueError(f"PCTX1 context provider identity metadata가 올바르지 않습니다: {case_id}")
        _json_safe(dict(self.metadata))

    @property
    def case_ids(self) -> tuple[str, ...]:
        return _profile_identity(self.profile)[3]

    @property
    def candidate_hash(self) -> str:
        return _profile_identity(self.profile)[2]


@dataclass(frozen=True)
class ContextSliceValidationContract:
    """Explicit no-score tolerances for context-slice evidence."""

    min_retained_case_rate: float = 0.10
    min_retained_active_case_rate: float = 0.0
    max_average_return_regression_pct: float = 0.0
    max_median_return_regression_pct: float = 0.0
    max_profitable_rate_regression: float = 0.0
    max_worst_case_regression_pct: float = 0.0
    max_worst_mdd_regression_pct: float = 0.0
    max_cost_per_case_regression: float = 0.0
    max_mfe_giveback_regression_pct: float = 0.0
    require_train_material_improvement: bool = True
    min_material_improvement: float = 1e-9

    def validate(self) -> None:
        for name in ("min_retained_case_rate", "min_retained_active_case_rate"):
            value = _finite(getattr(self, name), name)
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{name}는 0..1 범위여야 합니다.")
        for name in (
            "max_average_return_regression_pct",
            "max_median_return_regression_pct",
            "max_profitable_rate_regression",
            "max_worst_case_regression_pct",
            "max_worst_mdd_regression_pct",
            "max_cost_per_case_regression",
            "max_mfe_giveback_regression_pct",
            "min_material_improvement",
        ):
            if _finite(getattr(self, name), name) < 0.0:
                raise ValueError(f"{name}는 0 이상이어야 합니다.")
        if type(self.require_train_material_improvement) is not bool:
            raise ValueError("require_train_material_improvement는 bool이어야 합니다.")

    @property
    def contract_hash(self) -> str:
        return _stable_hash({"schema": CONTRACT_SCHEMA_VERSION, **self.public_dict(include_hash=False)})

    def public_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        self.validate()
        payload = {
            "min_retained_case_rate": float(self.min_retained_case_rate),
            "min_retained_active_case_rate": float(self.min_retained_active_case_rate),
            "max_average_return_regression_pct": float(self.max_average_return_regression_pct),
            "max_median_return_regression_pct": float(self.max_median_return_regression_pct),
            "max_profitable_rate_regression": float(self.max_profitable_rate_regression),
            "max_worst_case_regression_pct": float(self.max_worst_case_regression_pct),
            "max_worst_mdd_regression_pct": float(self.max_worst_mdd_regression_pct),
            "max_cost_per_case_regression": float(self.max_cost_per_case_regression),
            "max_mfe_giveback_regression_pct": float(self.max_mfe_giveback_regression_pct),
            "require_train_material_improvement": bool(self.require_train_material_improvement),
            "min_material_improvement": float(self.min_material_improvement),
        }
        if include_hash:
            payload["schema"] = CONTRACT_SCHEMA_VERSION
            payload["contract_hash"] = self.contract_hash
        return payload


class TacticalContextValidationArena:
    """Validate independent registered E8 slices across explicit holdouts."""

    @staticmethod
    def _normalize_partitions(
        partitions: Sequence[ContextValidationPartition],
    ) -> tuple[ContextValidationPartition, ...]:
        frozen = tuple(partitions)
        if not frozen:
            raise ValueError("context validation partitions가 비어 있습니다.")
        for partition in frozen:
            if not isinstance(partition, ContextValidationPartition):
                raise ValueError("context validation partition 타입이 올바르지 않습니다.")
            partition.validate()
        ids = [str(item.partition_id).strip() for item in frozen]
        if len(set(ids)) != len(ids):
            raise ValueError("context validation partition_id에 중복이 있습니다.")
        counts = {role: 0 for role in _ALLOWED_ROLES}
        all_case_ids: list[str] = []
        candidate_hashes = set()
        for partition in frozen:
            counts[partition.normalized_role()] += 1
            all_case_ids.extend(partition.case_ids)
            candidate_hashes.add(partition.candidate_hash)
        for role in ("TRAIN", "VALIDATION", "OOS"):
            if counts[role] != 1:
                raise ValueError(f"context validation arena는 {role} partition을 정확히 1개 요구합니다.")
        if counts["HARSH"] < 1:
            raise ValueError("context validation arena는 HARSH partition을 최소 1개 요구합니다.")
        if len(set(all_case_ids)) != len(all_case_ids):
            raise ValueError("context validation partition case_id는 전역적으로 분리되어야 합니다.")
        if len(candidate_hashes) != 1:
            raise ValueError("context validation partitions는 동일 candidate_hash를 사용해야 합니다.")
        return tuple(
            sorted(
                frozen,
                key=lambda item: (_ROLE_ORDER[item.normalized_role()], str(item.partition_id).strip()),
            )
        )

    @staticmethod
    def _normalize_slices(slices: Sequence[RegisteredContextSlice]) -> tuple[RegisteredContextSlice, ...]:
        frozen = tuple(sorted(tuple(slices), key=lambda item: str(item.slice_id)))
        if not frozen:
            raise ValueError("registered context validation slices가 비어 있습니다.")
        for item in frozen:
            if not isinstance(item, RegisteredContextSlice):
                raise ValueError("registered context validation slice 타입이 올바르지 않습니다.")
            item.validate()
        ids = [item.slice_id for item in frozen]
        if len(set(ids)) != len(ids):
            raise ValueError("registered context validation slice_id에 중복이 있습니다.")
        return frozen

    @staticmethod
    def _require_registered_manifest(
        partition: ContextValidationPartition,
        registered_slice: RegisteredContextSlice,
    ) -> None:
        wanted = str(registered_slice.required_manifest_hash).strip()
        for case_id, context in partition.contexts.items():
            manifest_hashes = tuple(
                str(item).strip()
                for item in dict(context.metadata).get("parent_feature_manifest_hashes") or ()
            )
            if wanted not in manifest_hashes:
                raise ValueError(
                    f"registered context slice manifest가 case context에 없습니다: "
                    f"slice={registered_slice.slice_id}, case={case_id}"
                )

    @staticmethod
    def _evaluate_partition_slice(
        *,
        role: str,
        evidence: Mapping[str, Any],
        contract: ContextSliceValidationContract,
    ) -> dict[str, Any]:
        contract.validate()
        summary = dict(evidence.get("summary") or {})
        deltas = dict(evidence.get("incremental_vs_all") or {})
        violations: list[str] = []
        if int(summary.get("cases") or 0) < 1:
            violations.append("empty_match")
        retained_case_rate = _finite(evidence.get("retained_case_rate"), "retained_case_rate")
        if retained_case_rate < contract.min_retained_case_rate:
            violations.append("retained_case_rate")
        retained_active = evidence.get("retained_active_case_rate")
        if retained_active is not None:
            retained_active = _finite(retained_active, "retained_active_case_rate")
            if retained_active < contract.min_retained_active_case_rate:
                violations.append("retained_active_case_rate")

        positive_axes = {
            "average_return_pct": contract.max_average_return_regression_pct,
            "median_return_pct": contract.max_median_return_regression_pct,
            "profitable_case_rate": contract.max_profitable_rate_regression,
            "worst_case_return_pct": contract.max_worst_case_regression_pct,
            "worst_mdd_pct": contract.max_worst_mdd_regression_pct,
        }
        negative_axes = {
            "cost_per_case": contract.max_cost_per_case_regression,
            "average_mfe_giveback_pct": contract.max_mfe_giveback_regression_pct,
        }
        improvements: list[str] = []
        eps = contract.min_material_improvement
        normalized_deltas: dict[str, float | None] = {}
        for key, tolerance in positive_axes.items():
            raw = deltas.get(key)
            if raw is None:
                normalized_deltas[key] = None
                continue
            delta = _finite(raw, f"context delta {key}")
            normalized_deltas[key] = delta
            if delta < -float(tolerance):
                violations.append(key)
            if delta > eps:
                improvements.append(key)
        for key, tolerance in negative_axes.items():
            raw = deltas.get(key)
            if raw is None:
                normalized_deltas[key] = None
                continue
            delta = _finite(raw, f"context delta {key}")
            normalized_deltas[key] = delta
            if delta > float(tolerance):
                violations.append(key)
            if delta < -eps:
                improvements.append(key)
        if role == "TRAIN" and contract.require_train_material_improvement and not improvements:
            violations.append("train_no_material_improvement")
        return {
            "status": "PASS" if not violations else "FAIL",
            "role": role,
            "retained_case_rate": retained_case_rate,
            "retained_active_case_rate": retained_active,
            "summary": summary,
            "incremental_vs_all": normalized_deltas,
            "violations": tuple(violations),
            "improvements": tuple(improvements),
            "selection_policy": "DECLARED_AXES_NO_HIDDEN_UNIVERSAL_SCORE",
        }

    @classmethod
    def run(
        cls,
        *,
        partitions: Sequence[ContextValidationPartition],
        slices: Sequence[RegisteredContextSlice],
        contract: ContextSliceValidationContract = ContextSliceValidationContract(),
    ) -> dict[str, Any]:
        contract.validate()
        ordered_partitions = cls._normalize_partitions(partitions)
        ordered_slices = cls._normalize_slices(slices)
        candidate_hash = ordered_partitions[0].candidate_hash

        partition_attributions: list[dict[str, Any]] = []
        by_partition_slice: dict[tuple[str, str], Mapping[str, Any]] = {}
        for partition in ordered_partitions:
            for registered_slice in ordered_slices:
                cls._require_registered_manifest(partition, registered_slice)
            attribution = TacticalContextAttributor.attribute(
                profile=partition.profile,
                contexts=partition.contexts,
                rules=tuple(item.rule for item in ordered_slices),
            )
            slice_rows = {str(item["slice"]["slice_id"]): item for item in attribution["slices"]}
            for registered_slice in ordered_slices:
                by_partition_slice[(partition.partition_id, registered_slice.slice_id)] = slice_rows[
                    registered_slice.slice_id
                ]
            partition_attributions.append(
                {
                    "partition_id": str(partition.partition_id).strip(),
                    "role": partition.normalized_role(),
                    "profile_run_hash": str(partition.profile["run_hash"]),
                    "case_set_hash": str(partition.profile["case_set_hash"]),
                    "attribution_hash": attribution["attribution_hash"],
                    "context_case_hashes": attribution["context_case_hashes"],
                    "adverse_reason": (
                        str(partition.metadata.get("adverse_reason") or "").strip()
                        if partition.normalized_role() == "HARSH"
                        else ""
                    ),
                }
            )

        slice_results = []
        for registered_slice in ordered_slices:
            evaluations = []
            for partition in ordered_partitions:
                evidence = by_partition_slice[(partition.partition_id, registered_slice.slice_id)]
                judged = cls._evaluate_partition_slice(
                    role=partition.normalized_role(),
                    evidence=evidence,
                    contract=contract,
                )
                evaluations.append(
                    {
                        "partition_id": str(partition.partition_id).strip(),
                        "attribution_hash": next(
                            row["attribution_hash"]
                            for row in partition_attributions
                            if row["partition_id"] == str(partition.partition_id).strip()
                        ),
                        **judged,
                    }
                )
            passed = all(item["status"] == "PASS" for item in evaluations)
            slice_identity = {
                "schema": SCHEMA_VERSION,
                "validation_policy": VALIDATION_POLICY,
                "context_policy": CONTEXT_POLICY,
                "candidate_hash": candidate_hash,
                "registered_slice": registered_slice.public_dict(),
                "contract_hash": contract.contract_hash,
                "partition_evidence": tuple(evaluations),
            }
            validation_hash = _stable_hash(slice_identity)
            slice_results.append(
                {
                    "slice_id": registered_slice.slice_id,
                    "feature_id": str(registered_slice.feature_id).strip(),
                    "required_manifest_hash": str(registered_slice.required_manifest_hash).strip(),
                    "rule": registered_slice.rule.public_dict(),
                    "status": "PASS" if passed else "FAIL",
                    "evidence_status": "VALIDATED" if passed else "REJECTED",
                    "deployment_policy_evidence_eligible": bool(passed),
                    "operational_authority": False,
                    "partition_evidence": tuple(evaluations),
                    "validation_evidence_hash": validation_hash,
                }
            )

        validated = tuple(item["slice_id"] for item in slice_results if item["status"] == "PASS")
        rejected = tuple(item["slice_id"] for item in slice_results if item["status"] != "PASS")
        if validated and not rejected:
            arena_status = "PASS"
        elif validated:
            arena_status = "MIXED"
        else:
            arena_status = "FAIL"
        identity = {
            "schema": SCHEMA_VERSION,
            "validation_policy": VALIDATION_POLICY,
            "context_policy": CONTEXT_POLICY,
            "candidate_hash": candidate_hash,
            "contract_hash": contract.contract_hash,
            "partitions": tuple(partition_attributions),
            "slices": tuple(slice_results),
        }
        return {
            "schema": SCHEMA_VERSION,
            "validation_policy": VALIDATION_POLICY,
            "context_policy": CONTEXT_POLICY,
            "arena_status": arena_status,
            "candidate_hash": candidate_hash,
            "contract": contract.public_dict(),
            "partitions": tuple(partition_attributions),
            "slices": tuple(slice_results),
            "validated_slice_ids": validated,
            "rejected_slice_ids": rejected,
            "operational_authority": False,
            "execution_integration": EXECUTION_INTEGRATION,
            "arena_hash": _stable_hash(identity),
        }
