"""Evidence-gated generation upgrades for evolving micro tactics.

A generation may acquire exactly one declared SkillSpec at a time.  The arena
compares parent and child on the same frozen BattleCase/context contract, checks
that the skill addresses an observed failure, enforces a capability budget, and
only auto-accepts upgrades that improve at least one mission/survival axis
without breaching declared survival tolerances.

This module never edits DSL or trusted engine code.  A human/LLM proposes the
child DSL; TacticalDiscoveryEngine produces immutable profiles; this arena only
judges the proposed generation transition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Optional, Sequence


SCHEMA_VERSION = "tactical_evolution/v1"


def _safe_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _safe_json(value), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), default=str, allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    number = float(value)
    return number if math.isfinite(number) else default


def _profile_identity(profile: Mapping[str, Any]) -> dict:
    if str(profile.get("schema") or "") != "tactical_discovery/v1":
        raise ValueError("evolution profile은 tactical_discovery/v1이어야 합니다.")
    candidate = dict(profile.get("candidate") or {})
    aggregate = dict(profile.get("aggregate") or {})
    candidate_hash = str(candidate.get("candidate_hash") or "").strip()
    run_hash = str(profile.get("run_hash") or "").strip()
    case_set_hash = str(profile.get("case_set_hash") or "").strip()
    if not candidate_hash or not run_hash or not case_set_hash:
        raise ValueError("evolution profile identity가 불완전합니다.")
    cases = int(aggregate.get("cases") or 0)
    if cases < 1:
        raise ValueError("evolution profile aggregate cases가 비어 있습니다.")
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "candidate_hash": candidate_hash,
        "run_hash": run_hash,
        "case_set_hash": case_set_hash,
        "context_policy": dict(profile.get("context_policy") or {}),
        "complexity_units": int(candidate.get("complexity_units") or aggregate.get("complexity_units") or 1),
        "cases": cases,
    }


@dataclass(frozen=True)
class CapabilityBudget:
    """Declared personal arsenal budget; no hidden complexity formula."""

    max_skills: int = 8
    max_complexity_units: int = 16
    max_indicators: int = 8
    max_parameters: int = 16
    max_state_variables: int = 8
    max_branches: int = 12
    max_setup_variants: int = 4

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if int(value) < 0:
                raise ValueError(f"CapabilityBudget {name}는 0 이상이어야 합니다.")

    def validate_usage(self, usage: Mapping[str, Any]) -> None:
        self.validate()
        limits = {
            "skills": self.max_skills,
            "complexity_units": self.max_complexity_units,
            "indicators": self.max_indicators,
            "parameters": self.max_parameters,
            "state_variables": self.max_state_variables,
            "branches": self.max_branches,
            "setup_variants": self.max_setup_variants,
        }
        for key, limit in limits.items():
            value = int(usage.get(key, 0) or 0)
            if value < 0:
                raise ValueError(f"capability usage {key}는 0 이상이어야 합니다.")
            if value > int(limit):
                raise ValueError(f"CapabilityBudget 초과: {key}={value} > {limit}")


@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    capability: str
    implementation: str
    addresses_failure_tags: tuple[str, ...]
    cost: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.skill_id.strip() or not self.capability.strip() or not self.implementation.strip():
            raise ValueError("SkillSpec skill_id/capability/implementation이 필요합니다.")
        if not self.addresses_failure_tags:
            raise ValueError("SkillSpec은 최소 1개 failure tag를 해결 대상으로 가져야 합니다.")
        allowed = {"complexity_units", "indicators", "parameters", "state_variables", "branches", "setup_variants"}
        unknown = set(self.cost) - allowed
        if unknown:
            raise ValueError(f"SkillSpec 알 수 없는 cost 항목: {sorted(unknown)}")
        for key, value in self.cost.items():
            if int(value) < 0:
                raise ValueError(f"SkillSpec cost {key}는 0 이상이어야 합니다.")


@dataclass(frozen=True)
class PromotionContract:
    """Conservative automatic promotion gate.

    Mixed trade-offs become REVIEW rather than being hidden in one universal score.
    """

    max_profitable_rate_regression: float = 0.0
    max_worst_mdd_regression_pct: float = 0.0
    max_worst_case_regression_pct: float = 0.0
    max_cost_per_case_regression: float = 0.0
    max_top1_concentration_regression: float = 0.0
    min_material_improvement: float = 1e-9
    require_failure_relevance: bool = True

    def validate(self) -> None:
        for name in (
            "max_profitable_rate_regression",
            "max_worst_mdd_regression_pct",
            "max_worst_case_regression_pct",
            "max_cost_per_case_regression",
            "max_top1_concentration_regression",
            "min_material_improvement",
        ):
            if float(getattr(self, name)) < 0:
                raise ValueError(f"PromotionContract {name}는 0 이상이어야 합니다.")


@dataclass(frozen=True)
class EvolutionGeneration:
    family_id: str
    generation_index: int
    candidate_hash: str
    profile_run_hash: str
    case_set_hash: str
    context_policy_hash: str
    acquired_skills: tuple[str, ...]
    capability_usage: Mapping[str, int]
    parent_generation_hash: str = ""
    acquired_from_failure_hash: str = ""
    generation_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        family_id: str,
        generation_index: int,
        profile: Mapping[str, Any],
        acquired_skills: Sequence[str] = (),
        capability_usage: Optional[Mapping[str, int]] = None,
        parent_generation_hash: str = "",
        acquired_from_failure_hash: str = "",
    ) -> "EvolutionGeneration":
        identity = _profile_identity(profile)
        if not str(family_id).strip():
            raise ValueError("evolution family_id가 필요합니다.")
        if int(generation_index) < 0:
            raise ValueError("generation_index는 0 이상이어야 합니다.")
        skills = tuple(str(item).strip() for item in acquired_skills if str(item).strip())
        if len(set(skills)) != len(skills):
            raise ValueError("acquired_skills에 중복이 있습니다.")
        usage = {str(key): int(value) for key, value in dict(capability_usage or {}).items()}
        usage.setdefault("skills", len(skills))
        if usage["skills"] != len(skills):
            raise ValueError("capability_usage.skills와 acquired_skills 수가 일치해야 합니다.")
        usage.setdefault("complexity_units", identity["complexity_units"])
        context_policy_hash = _stable_hash(identity["context_policy"])
        raw = {
            "schema": SCHEMA_VERSION,
            "family_id": family_id,
            "generation_index": int(generation_index),
            "candidate_hash": identity["candidate_hash"],
            "profile_run_hash": identity["run_hash"],
            "case_set_hash": identity["case_set_hash"],
            "context_policy_hash": context_policy_hash,
            "acquired_skills": skills,
            "capability_usage": usage,
            "parent_generation_hash": parent_generation_hash,
            "acquired_from_failure_hash": acquired_from_failure_hash,
        }
        return cls(
            family_id=str(family_id),
            generation_index=int(generation_index),
            candidate_hash=identity["candidate_hash"],
            profile_run_hash=identity["run_hash"],
            case_set_hash=identity["case_set_hash"],
            context_policy_hash=context_policy_hash,
            acquired_skills=skills,
            capability_usage=usage,
            parent_generation_hash=str(parent_generation_hash or ""),
            acquired_from_failure_hash=str(acquired_from_failure_hash or ""),
            generation_hash=_stable_hash(raw),
        )


class EvolutionArena:
    """Judge one-skill child mutations against their parent generation."""

    @staticmethod
    def _aggregate(profile: Mapping[str, Any]) -> dict:
        aggregate = dict(profile.get("aggregate") or {})
        cases = int(aggregate.get("cases") or 0)
        if cases < 1:
            raise ValueError("evolution aggregate cases가 필요합니다.")
        total_cost = _number(aggregate.get("total_cost"))
        top1 = aggregate.get("top1_positive_return_concentration")
        return {
            "average_return_pct": _number(aggregate.get("average_return_pct")),
            "median_return_pct": _number(aggregate.get("median_return_pct")),
            "profitable_case_rate": _number(aggregate.get("profitable_case_rate")),
            "worst_mdd_pct": _number(aggregate.get("worst_mdd_pct")),
            "worst_case_return_pct": _number(aggregate.get("worst_case_return_pct")),
            "cost_per_case": total_cost / cases,
            "average_mfe_giveback_pct": _number(aggregate.get("average_mfe_giveback_pct")),
            "top1_positive_return_concentration": None if top1 is None else _number(top1),
        }

    @classmethod
    def evaluate_upgrade(
        cls,
        *,
        parent_generation: EvolutionGeneration,
        parent_profile: Mapping[str, Any],
        child_profile: Mapping[str, Any],
        skill: SkillSpec,
        failure_report: Mapping[str, Any],
        budget: CapabilityBudget,
        contract: PromotionContract = PromotionContract(),
    ) -> dict:
        skill.validate()
        budget.validate()
        contract.validate()
        parent_id = _profile_identity(parent_profile)
        child_id = _profile_identity(child_profile)
        if parent_generation.candidate_hash != parent_id["candidate_hash"] or parent_generation.profile_run_hash != parent_id["run_hash"]:
            raise ValueError("parent generation과 parent profile identity가 일치하지 않습니다.")
        if parent_id["case_set_hash"] != child_id["case_set_hash"]:
            raise ValueError("parent/child는 동일 frozen case_set_hash에서 비교되어야 합니다.")
        if _stable_hash(parent_id["context_policy"]) != _stable_hash(child_id["context_policy"]):
            raise ValueError("parent/child context policy가 일치해야 합니다.")
        if child_id["candidate_hash"] == parent_id["candidate_hash"]:
            raise ValueError("child candidate는 parent와 다른 candidate_hash여야 합니다.")
        if skill.skill_id in parent_generation.acquired_skills:
            raise ValueError(f"이미 획득한 skill입니다: {skill.skill_id}")
        if str(failure_report.get("schema") or "") != "tactical_failure/v1":
            raise ValueError("failure_report는 tactical_failure/v1이어야 합니다.")
        if str(failure_report.get("profile_run_hash") or "") != parent_id["run_hash"]:
            raise ValueError("failure_report는 parent profile에서 생성되어야 합니다.")
        if str(failure_report.get("case_set_hash") or "") != parent_id["case_set_hash"]:
            raise ValueError("failure_report case_set_hash가 parent와 다릅니다.")

        observed_tags = {
            str(cluster.get("failure_tag") or "")
            for cluster in (failure_report.get("clusters") or [])
            if str(cluster.get("failure_tag") or "")
        }
        relevance = sorted(observed_tags.intersection(set(skill.addresses_failure_tags)))
        if contract.require_failure_relevance and not relevance:
            raise ValueError(
                f"Skill {skill.skill_id}은 parent의 관찰된 failure를 해결 대상으로 하지 않습니다."
            )

        usage = dict(parent_generation.capability_usage)
        usage["skills"] = int(usage.get("skills", len(parent_generation.acquired_skills))) + 1
        for key, value in skill.cost.items():
            usage[key] = int(usage.get(key, 0)) + int(value)
        usage.setdefault("complexity_units", parent_id["complexity_units"] + int(skill.cost.get("complexity_units", 0)))
        budget.validate_usage(usage)
        if child_id["complexity_units"] > int(usage.get("complexity_units", 0)):
            raise ValueError(
                "child tactic complexity_units가 선언된 CapabilityBudget usage보다 큽니다."
            )

        parent = cls._aggregate(parent_profile)
        child = cls._aggregate(child_profile)
        deltas = {key: child[key] - parent[key] for key in (
            "average_return_pct", "median_return_pct", "profitable_case_rate",
            "worst_mdd_pct", "worst_case_return_pct", "cost_per_case",
            "average_mfe_giveback_pct",
        )}
        if parent["top1_positive_return_concentration"] is None or child["top1_positive_return_concentration"] is None:
            concentration_delta = None
        else:
            concentration_delta = child["top1_positive_return_concentration"] - parent["top1_positive_return_concentration"]
        deltas["top1_positive_return_concentration"] = concentration_delta

        violations = []
        if deltas["profitable_case_rate"] < -contract.max_profitable_rate_regression:
            violations.append("profitable_case_rate")
        if deltas["worst_mdd_pct"] < -contract.max_worst_mdd_regression_pct:
            violations.append("worst_mdd_pct")
        if deltas["worst_case_return_pct"] < -contract.max_worst_case_regression_pct:
            violations.append("worst_case_return_pct")
        if deltas["cost_per_case"] > contract.max_cost_per_case_regression:
            violations.append("cost_per_case")
        if concentration_delta is not None and concentration_delta > contract.max_top1_concentration_regression:
            violations.append("top1_positive_return_concentration")

        eps = contract.min_material_improvement
        improvements = []
        for key in ("average_return_pct", "median_return_pct", "profitable_case_rate", "worst_mdd_pct", "worst_case_return_pct"):
            if deltas[key] > eps:
                improvements.append(key)
        if deltas["cost_per_case"] < -eps:
            improvements.append("cost_per_case")
        if deltas["average_mfe_giveback_pct"] < -eps:
            improvements.append("average_mfe_giveback_pct")
        if concentration_delta is not None and concentration_delta < -eps:
            improvements.append("top1_positive_return_concentration")

        if not violations and improvements:
            decision = "ACCEPT"
            child_generation = EvolutionGeneration.create(
                family_id=parent_generation.family_id,
                generation_index=parent_generation.generation_index + 1,
                profile=child_profile,
                acquired_skills=(*parent_generation.acquired_skills, skill.skill_id),
                capability_usage=usage,
                parent_generation_hash=parent_generation.generation_hash,
                acquired_from_failure_hash=str(failure_report.get("failure_hash") or ""),
            )
        elif violations and not improvements:
            decision = "REJECT"
            child_generation = None
        else:
            decision = "REVIEW"
            child_generation = None

        evidence = {
            "schema": SCHEMA_VERSION,
            "decision": decision,
            "family_id": parent_generation.family_id,
            "parent_generation_hash": parent_generation.generation_hash,
            "parent_candidate_hash": parent_id["candidate_hash"],
            "child_candidate_hash": child_id["candidate_hash"],
            "skill_id": skill.skill_id,
            "capability": skill.capability,
            "failure_relevance": relevance,
            "failure_hash": str(failure_report.get("failure_hash") or ""),
            "case_set_hash": parent_id["case_set_hash"],
            "deltas": deltas,
            "survival_violations": violations,
            "improvements": improvements,
            "capability_usage": usage,
            "child_generation_hash": child_generation.generation_hash if child_generation else None,
            "promotion_policy": "ONE_SKILL_EVIDENCE_GATED_NO_HIDDEN_SCORE",
        }
        evidence["decision_hash"] = _stable_hash(evidence)
        if child_generation is not None:
            evidence["child_generation"] = child_generation
        return evidence
