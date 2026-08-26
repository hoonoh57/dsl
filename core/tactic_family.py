"""Tactic-family registry for bounded evolving micro-warrior skill trees."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from core.tactical_discovery import TacticCandidate
from core.tactical_evolution import CapabilityBudget, EvolutionGeneration, SkillSpec


USAGE_KEYS = {
    "skills",
    "complexity_units",
    "indicators",
    "parameters",
    "state_variables",
    "branches",
    "setup_variants",
}


def _skill_refs(skill: SkillSpec, key: str) -> tuple[str, ...]:
    raw = skill.metadata.get(key, ())
    if raw is None:
        return ()
    if isinstance(raw, str):
        values = (raw,)
    elif isinstance(raw, Sequence):
        values = tuple(str(item) for item in raw)
    else:
        raise ValueError(f"SkillSpec metadata.{key}는 문자열 또는 목록이어야 합니다: {skill.skill_id}")
    normalized = tuple(item.strip() for item in values if item.strip())
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"SkillSpec metadata.{key}에 중복이 있습니다: {skill.skill_id}")
    return normalized


@dataclass(frozen=True)
class TacticFamilySpec:
    family_id: str
    base_candidate_id: str
    base_dsl: str
    base_complexity_units: int
    budget: CapabilityBudget
    base_usage: Mapping[str, int]
    skills: tuple[SkillSpec, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.family_id.strip():
            raise ValueError("TacticFamily family_id가 필요합니다.")
        if not self.base_candidate_id.strip() or not self.base_dsl.strip():
            raise ValueError("TacticFamily base candidate/DSL이 필요합니다.")
        if int(self.base_complexity_units) < 1:
            raise ValueError("base_complexity_units는 1 이상이어야 합니다.")
        self.budget.validate()
        usage = {str(key): int(value) for key, value in dict(self.base_usage).items()}
        unknown_usage = set(usage) - USAGE_KEYS
        if unknown_usage:
            raise ValueError(f"TacticFamily 알 수 없는 base_usage 항목: {sorted(unknown_usage)}")
        usage.setdefault("skills", 0)
        usage.setdefault("complexity_units", int(self.base_complexity_units))
        if usage["skills"] != 0:
            raise ValueError("base_usage.skills는 0이어야 합니다.")
        if usage["complexity_units"] < int(self.base_complexity_units):
            raise ValueError("base_usage.complexity_units가 base candidate보다 작습니다.")
        self.budget.validate_usage(usage)

        ids = []
        skill_map: dict[str, SkillSpec] = {}
        for skill in self.skills:
            skill.validate()
            ids.append(skill.skill_id)
            skill_map[skill.skill_id] = skill
        if len(set(ids)) != len(ids):
            raise ValueError("TacticFamily skill_id에 중복이 있습니다.")

        known = set(ids)
        dependencies: dict[str, tuple[str, ...]] = {}
        for skill in self.skills:
            requires = _skill_refs(skill, "requires_skills")
            excludes = _skill_refs(skill, "excludes_skills")
            unknown = (set(requires) | set(excludes)) - known
            if unknown:
                raise ValueError(
                    f"TacticFamily skill tree가 알 수 없는 skill을 참조합니다: "
                    f"{skill.skill_id} -> {sorted(unknown)}"
                )
            if skill.skill_id in requires or skill.skill_id in excludes:
                raise ValueError(f"TacticFamily skill이 자기 자신을 참조합니다: {skill.skill_id}")
            overlap = set(requires) & set(excludes)
            if overlap:
                raise ValueError(
                    f"TacticFamily skill requires/excludes가 충돌합니다: "
                    f"{skill.skill_id} -> {sorted(overlap)}"
                )
            dependencies[skill.skill_id] = requires

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(skill_id: str) -> None:
            if skill_id in visited:
                return
            if skill_id in visiting:
                raise ValueError(f"TacticFamily skill dependency cycle이 있습니다: {skill_id}")
            visiting.add(skill_id)
            for required in dependencies.get(skill_id, ()):
                visit(required)
            visiting.remove(skill_id)
            visited.add(skill_id)

        for skill_id in ids:
            visit(skill_id)

    def base_candidate(self) -> TacticCandidate:
        self.validate()
        metadata = {**dict(self.metadata), "family_id": self.family_id, "generation": 0}
        return TacticCandidate(
            candidate_id=self.base_candidate_id,
            dsl_code=self.base_dsl,
            complexity_units=int(self.base_complexity_units),
            metadata=metadata,
        )

    def normalized_base_usage(self) -> dict[str, int]:
        self.validate()
        usage = {str(key): int(value) for key, value in dict(self.base_usage).items()}
        usage.setdefault("skills", 0)
        usage.setdefault("complexity_units", int(self.base_complexity_units))
        return usage

    def skill(self, skill_id: str) -> SkillSpec:
        self.validate()
        target = str(skill_id or "").strip()
        for skill in self.skills:
            if skill.skill_id == target:
                return skill
        raise KeyError(f"TacticFamily skill not found: {target}")

    def legal_skills(
        self,
        *,
        generation: EvolutionGeneration,
        failure_report: Mapping[str, Any],
    ) -> tuple[SkillSpec, ...]:
        self.validate()
        if generation.family_id != self.family_id:
            raise ValueError("generation family_id가 TacticFamily와 다릅니다.")
        if str(failure_report.get("schema") or "") != "tactical_failure/v1":
            raise ValueError("failure_report는 tactical_failure/v1이어야 합니다.")
        if str(failure_report.get("profile_run_hash") or "") != generation.profile_run_hash:
            raise ValueError("failure_report가 현재 generation profile에서 생성되지 않았습니다.")
        observed = {
            str(cluster.get("failure_tag") or "")
            for cluster in (failure_report.get("clusters") or [])
            if str(cluster.get("failure_tag") or "")
        }
        acquired = set(generation.acquired_skills)
        legal = []
        for skill in self.skills:
            if skill.skill_id in acquired:
                continue
            if not observed.intersection(set(skill.addresses_failure_tags)):
                continue
            requires = set(_skill_refs(skill, "requires_skills"))
            excludes = set(_skill_refs(skill, "excludes_skills"))
            if not requires.issubset(acquired):
                continue
            if excludes.intersection(acquired):
                continue
            usage = dict(generation.capability_usage)
            usage["skills"] = int(usage.get("skills", len(acquired))) + 1
            for key, value in skill.cost.items():
                usage[key] = int(usage.get(key, 0)) + int(value)
            try:
                self.budget.validate_usage(usage)
            except ValueError:
                continue
            legal.append(skill)
        return tuple(legal)


class TacticFamilyRegistry:
    def __init__(self, families: Sequence[TacticFamilySpec] = ()):
        self._families: dict[str, TacticFamilySpec] = {}
        for family in families:
            self.register(family)

    def register(self, family: TacticFamilySpec) -> None:
        family.validate()
        if family.family_id in self._families:
            raise ValueError(f"TacticFamily already registered: {family.family_id}")
        self._families[family.family_id] = family

    def get(self, family_id: str) -> TacticFamilySpec:
        key = str(family_id or "").strip()
        if key not in self._families:
            raise KeyError(f"TacticFamily not found: {key}")
        return self._families[key]

    def list_ids(self) -> tuple[str, ...]:
        return tuple(self._families)
