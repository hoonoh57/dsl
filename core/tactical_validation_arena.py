"""Train / Validation / OOS / harsh replay arena for evolving micro tactics.

E6 evaluates one fixed parent/child pair across explicit, frozen partitions.  It
reuses TacticalDiscoveryEngine for replay and EvolutionArena for the Train
promotion contract, then applies declared holdout survival checks to Validation,
OOS and deliberately adverse HARSH partitions.  There is no hidden universal
score and no family-head mutation in this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from core.tactical_discovery import BattleCase, TacticCandidate, TacticalDiscoveryEngine
from core.tactical_evolution import (
    CapabilityBudget,
    EvolutionArena,
    EvolutionGeneration,
    PromotionContract,
    SkillSpec,
)


SCHEMA_VERSION = "tactical_validation_arena/v1"
_ALLOWED_ROLES = {"TRAIN", "VALIDATION", "OOS", "HARSH"}
_ROLE_ORDER = {"TRAIN": 0, "VALIDATION": 1, "OOS": 2, "HARSH": 3}


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    number = float(value)
    return number if math.isfinite(number) else default


@dataclass(frozen=True)
class ValidationPartition:
    """One explicit frozen replay partition.

    E6 v1 requires globally disjoint BattleCase ids across partitions.  HARSH
    partitions additionally declare why the slice is adverse; the arena never
    guesses or synthesizes harsh cases.
    """

    partition_id: str
    role: str
    cases: tuple[BattleCase, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized_role(self) -> str:
        return str(self.role or "").strip().upper()

    def validate(self) -> None:
        partition_id = str(self.partition_id or "").strip()
        role = self.normalized_role()
        if not partition_id:
            raise ValueError("validation partition_id가 필요합니다.")
        if role not in _ALLOWED_ROLES:
            raise ValueError(f"지원하지 않는 validation role입니다: {self.role!r}")
        if not self.cases:
            raise ValueError(f"validation partition BattleCase가 비어 있습니다: {partition_id}")
        ids = []
        for case in self.cases:
            case.validate()
            ids.append(case.case_id)
        if len(set(ids)) != len(ids):
            raise ValueError(f"validation partition case_id가 중복되었습니다: {partition_id}")
        if role == "HARSH" and not str(self.metadata.get("adverse_reason") or "").strip():
            raise ValueError(f"HARSH partition은 adverse_reason을 명시해야 합니다: {partition_id}")


@dataclass(frozen=True)
class HoldoutContract:
    """Declared no-score mission/survival tolerances for non-Train partitions."""

    max_average_return_regression_pct: float = 0.0
    max_median_return_regression_pct: float = 0.0
    max_profitable_rate_regression: float = 0.0
    max_worst_mdd_regression_pct: float = 0.0
    max_worst_case_regression_pct: float = 0.0
    max_cost_per_case_regression: float = 0.0
    max_mfe_giveback_regression_pct: float = 0.0
    max_top1_concentration_regression: float = 0.0
    require_child_activity_if_parent_active: bool = True
    min_material_improvement: float = 1e-9

    def validate(self) -> None:
        for name in (
            "max_average_return_regression_pct",
            "max_median_return_regression_pct",
            "max_profitable_rate_regression",
            "max_worst_mdd_regression_pct",
            "max_worst_case_regression_pct",
            "max_cost_per_case_regression",
            "max_mfe_giveback_regression_pct",
            "max_top1_concentration_regression",
            "min_material_improvement",
        ):
            if float(getattr(self, name)) < 0.0:
                raise ValueError(f"HoldoutContract {name}는 0 이상이어야 합니다.")


class TacticalValidationArena:
    """Replay and judge one fixed child without changing the trusted engine."""

    @staticmethod
    def _aggregate(profile: Mapping[str, Any]) -> dict[str, Any]:
        if str(profile.get("schema") or "") != "tactical_discovery/v1":
            raise ValueError("validation arena profile은 tactical_discovery/v1이어야 합니다.")
        aggregate = dict(profile.get("aggregate") or {})
        cases = int(aggregate.get("cases") or 0)
        if cases < 1:
            raise ValueError("validation arena aggregate cases가 비어 있습니다.")
        top1 = aggregate.get("top1_positive_return_concentration")
        return {
            "cases": cases,
            "active_cases": int(aggregate.get("active_cases") or 0),
            "average_return_pct": _number(aggregate.get("average_return_pct")),
            "median_return_pct": _number(aggregate.get("median_return_pct")),
            "profitable_case_rate": _number(aggregate.get("profitable_case_rate")),
            "worst_mdd_pct": _number(aggregate.get("worst_mdd_pct")),
            "worst_case_return_pct": _number(aggregate.get("worst_case_return_pct")),
            "cost_per_case": _number(aggregate.get("total_cost")) / cases,
            "average_mfe_giveback_pct": _number(aggregate.get("average_mfe_giveback_pct")),
            "top1_positive_return_concentration": None if top1 is None else _number(top1),
        }

    @staticmethod
    def _validate_profile_pair(parent: Mapping[str, Any], child: Mapping[str, Any]) -> None:
        parent_case_set = str(parent.get("case_set_hash") or "")
        child_case_set = str(child.get("case_set_hash") or "")
        if not parent_case_set or parent_case_set != child_case_set:
            raise ValueError("validation parent/child는 동일 case_set_hash를 사용해야 합니다.")
        if _stable_hash(dict(parent.get("context_policy") or {})) != _stable_hash(
            dict(child.get("context_policy") or {})
        ):
            raise ValueError("validation parent/child context policy가 달라졌습니다.")

    @classmethod
    def _compare_holdout(
        cls,
        *,
        parent_profile: Mapping[str, Any],
        child_profile: Mapping[str, Any],
        contract: HoldoutContract,
    ) -> dict:
        contract.validate()
        cls._validate_profile_pair(parent_profile, child_profile)
        parent = cls._aggregate(parent_profile)
        child = cls._aggregate(child_profile)
        keys = (
            "average_return_pct",
            "median_return_pct",
            "profitable_case_rate",
            "worst_mdd_pct",
            "worst_case_return_pct",
            "cost_per_case",
            "average_mfe_giveback_pct",
        )
        deltas = {key: child[key] - parent[key] for key in keys}
        if (
            parent["top1_positive_return_concentration"] is None
            or child["top1_positive_return_concentration"] is None
        ):
            concentration_delta = None
        else:
            concentration_delta = (
                child["top1_positive_return_concentration"]
                - parent["top1_positive_return_concentration"]
            )
        deltas["top1_positive_return_concentration"] = concentration_delta
        deltas["active_cases"] = child["active_cases"] - parent["active_cases"]

        violations: list[str] = []
        if deltas["average_return_pct"] < -contract.max_average_return_regression_pct:
            violations.append("average_return_pct")
        if deltas["median_return_pct"] < -contract.max_median_return_regression_pct:
            violations.append("median_return_pct")
        if deltas["profitable_case_rate"] < -contract.max_profitable_rate_regression:
            violations.append("profitable_case_rate")
        if deltas["worst_mdd_pct"] < -contract.max_worst_mdd_regression_pct:
            violations.append("worst_mdd_pct")
        if deltas["worst_case_return_pct"] < -contract.max_worst_case_regression_pct:
            violations.append("worst_case_return_pct")
        if deltas["cost_per_case"] > contract.max_cost_per_case_regression:
            violations.append("cost_per_case")
        if deltas["average_mfe_giveback_pct"] > contract.max_mfe_giveback_regression_pct:
            violations.append("average_mfe_giveback_pct")
        if (
            concentration_delta is not None
            and concentration_delta > contract.max_top1_concentration_regression
        ):
            violations.append("top1_positive_return_concentration")
        if (
            contract.require_child_activity_if_parent_active
            and parent["active_cases"] > 0
            and child["active_cases"] == 0
        ):
            violations.append("engagement_collapse")

        eps = contract.min_material_improvement
        improvements: list[str] = []
        for key in (
            "average_return_pct",
            "median_return_pct",
            "profitable_case_rate",
            "worst_mdd_pct",
            "worst_case_return_pct",
        ):
            if deltas[key] > eps:
                improvements.append(key)
        for key in ("cost_per_case", "average_mfe_giveback_pct"):
            if deltas[key] < -eps:
                improvements.append(key)
        if concentration_delta is not None and concentration_delta < -eps:
            improvements.append("top1_positive_return_concentration")

        return {
            "status": "PASS" if not violations else "FAIL",
            "parent": parent,
            "child": child,
            "deltas": deltas,
            "violations": tuple(violations),
            "improvements": tuple(improvements),
            "selection_policy": "DECLARED_AXES_NO_HIDDEN_UNIVERSAL_SCORE",
        }

    @staticmethod
    def _normalize_partitions(
        partitions: Sequence[ValidationPartition],
    ) -> tuple[ValidationPartition, ...]:
        frozen = tuple(partitions)
        if not frozen:
            raise ValueError("validation partitions가 비어 있습니다.")
        for partition in frozen:
            partition.validate()
        ids = [str(partition.partition_id).strip() for partition in frozen]
        if len(set(ids)) != len(ids):
            raise ValueError("validation partition_id가 중복되었습니다.")
        role_counts = {role: 0 for role in _ALLOWED_ROLES}
        all_case_ids: list[str] = []
        for partition in frozen:
            role_counts[partition.normalized_role()] += 1
            all_case_ids.extend(case.case_id for case in partition.cases)
        for role in ("TRAIN", "VALIDATION", "OOS"):
            if role_counts[role] != 1:
                raise ValueError(f"validation arena는 {role} partition을 정확히 1개 요구합니다.")
        if role_counts["HARSH"] < 1:
            raise ValueError("validation arena는 HARSH partition을 최소 1개 요구합니다.")
        if len(set(all_case_ids)) != len(all_case_ids):
            raise ValueError(
                "E6 v1 partition BattleCase case_id는 전역적으로 분리되어야 합니다."
            )
        return tuple(
            sorted(
                frozen,
                key=lambda partition: (
                    _ROLE_ORDER[partition.normalized_role()],
                    str(partition.partition_id),
                ),
            )
        )

    @staticmethod
    def _validate_child_provenance(
        *,
        parent_generation: EvolutionGeneration,
        parent_candidate: TacticCandidate,
        child_candidate: TacticCandidate,
        skill: SkillSpec,
        failure_report: Mapping[str, Any],
    ) -> None:
        parent_candidate.validate()
        child_candidate.validate()
        skill.validate()
        if parent_generation.candidate_hash != parent_candidate.candidate_hash:
            raise ValueError("validation parent generation/candidate identity가 다릅니다.")
        if child_candidate.candidate_hash == parent_candidate.candidate_hash:
            raise ValueError("validation child candidate는 parent와 달라야 합니다.")
        metadata = dict(child_candidate.metadata)
        if str(metadata.get("family_id") or "") != parent_generation.family_id:
            raise ValueError("validation child family_id가 parent generation과 다릅니다.")
        if str(metadata.get("parent_generation_hash") or "") != parent_generation.generation_hash:
            raise ValueError("validation child parent_generation_hash가 다릅니다.")
        if str(metadata.get("proposed_skill_id") or "") != skill.skill_id:
            raise ValueError("validation child proposed_skill_id가 SkillSpec과 다릅니다.")
        if str(metadata.get("mutation_policy") or "") != "ONE_REGISTERED_SKILL_ONLY":
            raise ValueError("validation child는 E5 one-skill mutation evidence가 필요합니다.")
        if str(metadata.get("failure_hash") or "") != str(failure_report.get("failure_hash") or ""):
            raise ValueError("validation child failure_hash가 parent failure evidence와 다릅니다.")

    @classmethod
    def run(
        cls,
        *,
        parent_generation: EvolutionGeneration,
        parent_candidate: TacticCandidate,
        child_candidate: TacticCandidate,
        skill: SkillSpec,
        failure_report: Mapping[str, Any],
        budget: CapabilityBudget,
        partitions: Sequence[ValidationPartition],
        train_contract: PromotionContract = PromotionContract(),
        holdout_contract: HoldoutContract = HoldoutContract(),
        max_workers: int = 4,
        require_neutral_context: bool = True,
        require_uniform_settings: bool = True,
    ) -> dict:
        budget.validate()
        train_contract.validate()
        holdout_contract.validate()
        if int(max_workers) < 1:
            raise ValueError("validation max_workers는 1 이상이어야 합니다.")
        if str(failure_report.get("schema") or "") != "tactical_failure/v1":
            raise ValueError("validation failure_report는 tactical_failure/v1이어야 합니다.")
        if str(failure_report.get("profile_run_hash") or "") != parent_generation.profile_run_hash:
            raise ValueError("validation failure_report profile_run_hash가 parent generation과 다릅니다.")
        if str(failure_report.get("case_set_hash") or "") != parent_generation.case_set_hash:
            raise ValueError("validation failure_report case_set_hash가 parent generation과 다릅니다.")
        cls._validate_child_provenance(
            parent_generation=parent_generation,
            parent_candidate=parent_candidate,
            child_candidate=child_candidate,
            skill=skill,
            failure_report=failure_report,
        )
        ordered = cls._normalize_partitions(partitions)

        partition_rows: list[dict[str, Any]] = []
        train_parent_profile: Mapping[str, Any] | None = None
        train_child_profile: Mapping[str, Any] | None = None
        for partition in ordered:
            parent_profile = TacticalDiscoveryEngine.evaluate(
                candidate=parent_candidate,
                cases=partition.cases,
                max_workers=int(max_workers),
                require_neutral_context=bool(require_neutral_context),
                require_uniform_settings=bool(require_uniform_settings),
            )
            child_profile = TacticalDiscoveryEngine.evaluate(
                candidate=child_candidate,
                cases=partition.cases,
                max_workers=int(max_workers),
                require_neutral_context=bool(require_neutral_context),
                require_uniform_settings=bool(require_uniform_settings),
            )
            cls._validate_profile_pair(parent_profile, child_profile)
            role = partition.normalized_role()
            if role == "TRAIN":
                train_parent_profile = parent_profile
                train_child_profile = child_profile
                if str(parent_profile.get("run_hash") or "") != parent_generation.profile_run_hash:
                    raise ValueError("TRAIN parent replay run_hash가 parent generation과 다릅니다.")
                if str(parent_profile.get("case_set_hash") or "") != parent_generation.case_set_hash:
                    raise ValueError("TRAIN parent replay case_set_hash가 parent generation과 다릅니다.")
                if _stable_hash(dict(parent_profile.get("context_policy") or {})) != parent_generation.context_policy_hash:
                    raise ValueError("TRAIN parent replay context policy가 parent generation과 다릅니다.")
                adjudication = {"status": "TRAIN_PENDING_EVOLUTION_ARENA"}
            else:
                adjudication = cls._compare_holdout(
                    parent_profile=parent_profile,
                    child_profile=child_profile,
                    contract=holdout_contract,
                )

            partition_identity = {
                "partition_id": partition.partition_id,
                "role": role,
                "case_set_hash": parent_profile["case_set_hash"],
                "parent_run_hash": parent_profile["run_hash"],
                "child_run_hash": child_profile["run_hash"],
                "status": adjudication["status"],
                "metadata": dict(partition.metadata),
            }
            partition_rows.append(
                {
                    "partition_id": partition.partition_id,
                    "role": role,
                    "metadata": dict(partition.metadata),
                    "case_ids": tuple(case.case_id for case in partition.cases),
                    "case_set_hash": parent_profile["case_set_hash"],
                    "parent_profile": parent_profile,
                    "child_profile": child_profile,
                    "adjudication": adjudication,
                    "partition_hash": _stable_hash(partition_identity),
                }
            )

        if train_parent_profile is None or train_child_profile is None:
            raise ValueError("TRAIN partition replay가 없습니다.")
        train_decision = EvolutionArena.evaluate_upgrade(
            parent_generation=parent_generation,
            parent_profile=train_parent_profile,
            child_profile=train_child_profile,
            skill=skill,
            failure_report=failure_report,
            budget=budget,
            contract=train_contract,
        )
        for row in partition_rows:
            if row["role"] == "TRAIN":
                row["adjudication"] = {
                    "status": train_decision["decision"],
                    "decision_hash": train_decision["decision_hash"],
                    "survival_violations": tuple(train_decision["survival_violations"]),
                    "improvements": tuple(train_decision["improvements"]),
                }
                row["partition_hash"] = _stable_hash(
                    {
                        "partition_id": row["partition_id"],
                        "role": "TRAIN",
                        "case_set_hash": row["case_set_hash"],
                        "parent_run_hash": row["parent_profile"]["run_hash"],
                        "child_run_hash": row["child_profile"]["run_hash"],
                        "status": train_decision["decision"],
                        "decision_hash": train_decision["decision_hash"],
                        "metadata": row["metadata"],
                    }
                )
                break

        holdout_failures = tuple(
            row["partition_id"]
            for row in partition_rows
            if row["role"] != "TRAIN" and row["adjudication"]["status"] == "FAIL"
        )
        if train_decision["decision"] == "REJECT" or holdout_failures:
            final_decision = "REJECT"
        elif train_decision["decision"] == "REVIEW":
            final_decision = "REVIEW"
        else:
            final_decision = "ACCEPT"

        accepted_generation = train_decision.get("child_generation") if final_decision == "ACCEPT" else None
        identity = {
            "schema": SCHEMA_VERSION,
            "parent_generation_hash": parent_generation.generation_hash,
            "parent_candidate_hash": parent_candidate.candidate_hash,
            "child_candidate_hash": child_candidate.candidate_hash,
            "skill_id": skill.skill_id,
            "failure_hash": str(failure_report.get("failure_hash") or ""),
            "train_decision_hash": train_decision["decision_hash"],
            "partition_hashes": [row["partition_hash"] for row in partition_rows],
            "final_decision": final_decision,
            "holdout_failures": holdout_failures,
            "accepted_generation_hash": accepted_generation.generation_hash if accepted_generation else None,
        }
        result = {
            "schema": SCHEMA_VERSION,
            "family_id": parent_generation.family_id,
            "parent_generation_hash": parent_generation.generation_hash,
            "parent_candidate_hash": parent_candidate.candidate_hash,
            "child_candidate_hash": child_candidate.candidate_hash,
            "skill_id": skill.skill_id,
            "failure_hash": str(failure_report.get("failure_hash") or ""),
            "partitions": partition_rows,
            "train_decision": train_decision,
            "holdout_failures": holdout_failures,
            "decision": final_decision,
            "promotion_eligible": final_decision == "ACCEPT",
            "selection_policy": "TRAIN_ACCEPT_PLUS_ALL_HOLDOUTS_PASS_NO_HIDDEN_SCORE",
            "head_policy": "PARENT_REMAINS_HEAD_UNTIL_EXPLICIT_PROMOTION",
            "arena_hash": _stable_hash(identity),
        }
        if accepted_generation is not None:
            result["accepted_generation"] = accepted_generation
        return result
