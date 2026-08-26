"""Bounded structural one-skill proposals for evolving micro tactics.

E5 is intentionally not a free-form DSL generator.  It consumes one trusted
EvolutionGeneration, the matching deterministic failure report and E4
characterization, then instantiates only skills already registered by the tactic
family.  Rendering is explicit/fail-closed and produces proposal evidence only;
no family head is promoted here.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from core.dsl_parser import DSLParser
from core.tactic_family import TacticFamilySpec
from core.tactical_discovery import TacticCandidate
from core.tactical_evolution import EvolutionGeneration, SkillSpec


SCHEMA_VERSION = "tactical_skill_generator/v1"


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


def _assignment_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"(?m)^(\s*(?:input\s+)?{re.escape(name)}\s*=\s*)([^\r\n]+)$")


def _require_absent(source: str, names: Sequence[str]) -> None:
    for name in names:
        if _assignment_pattern(name).search(source):
            raise ValueError(f"structural renderer target name이 parent DSL에 이미 있습니다: {name}")


def _insert_after_timeframe(source: str, lines: Sequence[str]) -> str:
    pattern = re.compile(r"(?m)^(\s*timeframe\s*=\s*[^\r\n]+)$")
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise ValueError("parent DSL timeframe assignment가 정확히 1개여야 합니다.")
    block = "\n".join(lines)
    match = matches[0]
    return source[: match.end()] + "\n" + block + source[match.end() :]


def _insert_before_assignment(source: str, name: str, lines: Sequence[str]) -> str:
    pattern = _assignment_pattern(name)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise ValueError(f"parent DSL assignment가 정확히 1개여야 합니다: {name}")
    block = "\n".join(lines) + "\n"
    match = matches[0]
    return source[: match.start()] + block + source[match.start() :]


def _append_boolean_condition(source: str, name: str, condition: str, *, operator: str) -> str:
    if operator not in {"and", "or"}:
        raise ValueError(f"지원하지 않는 boolean 결합 연산자입니다: {operator}")
    pattern = _assignment_pattern(name)
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise ValueError(f"parent DSL assignment가 정확히 1개여야 합니다: {name}")
    match = matches[0]
    prefix, expression = match.group(1), match.group(2).strip()
    replacement = f"{prefix}({expression}) {operator} ({condition})"
    return source[: match.start()] + replacement + source[match.end() :]


def _parameter_manifest(skill: SkillSpec) -> dict[str, dict[str, Any]]:
    raw = skill.metadata.get("parameters", {})
    if not isinstance(raw, Mapping):
        raise ValueError(f"SkillSpec metadata.parameters는 mapping이어야 합니다: {skill.skill_id}")
    output: dict[str, dict[str, Any]] = {}
    for name, spec in raw.items():
        if not isinstance(spec, Mapping):
            raise ValueError(f"Skill parameter spec은 mapping이어야 합니다: {skill.skill_id}/{name}")
        kind = str(spec.get("type") or "").strip().lower()
        if kind not in {"int", "number"}:
            raise ValueError(f"지원하지 않는 skill parameter type입니다: {skill.skill_id}/{name}={kind}")
        if not all(key in spec for key in ("min", "max", "default")):
            raise ValueError(f"skill parameter min/max/default가 필요합니다: {skill.skill_id}/{name}")
        low = float(spec["min"])
        high = float(spec["max"])
        default = float(spec["default"])
        if high < low or default < low or default > high:
            raise ValueError(f"skill parameter 범위/default가 올바르지 않습니다: {skill.skill_id}/{name}")
        if kind == "int" and any(abs(value - round(value)) > 1e-12 for value in (low, high, default)):
            raise ValueError(f"int skill parameter는 정수 범위/default여야 합니다: {skill.skill_id}/{name}")
        output[str(name)] = {
            "type": kind,
            "min": int(round(low)) if kind == "int" else low,
            "max": int(round(high)) if kind == "int" else high,
            "default": int(round(default)) if kind == "int" else default,
            "target": "dsl",
        }
    return output


def _format_default(spec: Mapping[str, Any]) -> str:
    value = spec["default"]
    if str(spec["type"]) == "int":
        return str(int(value))
    rounded = round(float(value))
    return str(int(rounded)) if abs(float(value) - rounded) < 1e-12 else format(float(value), ".12g")


class JmaTrendCrossResumeRenderer:
    """Explicit renderer for the currently registered JMA family only."""

    FAMILY_ID = "JMA_TREND_CROSS_RESUME_V1"

    @classmethod
    def render(cls, parent_dsl: str, skill: SkillSpec) -> tuple[str, dict[str, dict[str, Any]]]:
        source = str(parent_dsl or "")
        if not source.strip():
            raise ValueError("parent DSL이 비어 있습니다.")
        manifest = _parameter_manifest(skill)
        skill_id = skill.skill_id

        if skill_id == "JMA_RANGE_COOLDOWN":
            _require_absent(source, ("cooldown_bars", "cooldown_ok"))
            source = _insert_after_timeframe(
                source,
                (f"    input cooldown_bars = {_format_default(manifest['cooldown_bars'])}",),
            )
            source = _insert_before_assignment(
                source,
                "long_entry",
                ("    cooldown_ok = ta.bars_since(ta.crossunder(fast, slow)) > cooldown_bars",),
            )
            source = _append_boolean_condition(source, "long_entry", "cooldown_ok", operator="and")

        elif skill_id == "JMA_ADX_ENTRY_QUALITY":
            _require_absent(source, ("adx_length", "adx_threshold", "entry_strength"))
            source = _insert_after_timeframe(
                source,
                (
                    f"    input adx_length = {_format_default(manifest['adx_length'])}",
                    f"    input adx_threshold = {_format_default(manifest['adx_threshold'])}",
                ),
            )
            source = _insert_before_assignment(
                source,
                "long_entry",
                ("    entry_strength = ta.adx(adx_length)",),
            )
            source = _append_boolean_condition(
                source,
                "long_entry",
                "entry_strength > adx_threshold",
                operator="and",
            )

        elif skill_id == "JMA_CONFIRM_AFTER_RANGE":
            _require_absent(source, ("confirm_bars", "range_confirmed"))
            source = _insert_after_timeframe(
                source,
                (f"    input confirm_bars = {_format_default(manifest['confirm_bars'])}",),
            )
            source = _insert_before_assignment(
                source,
                "long_entry",
                ("    range_confirmed = state.persist(fast > slow and close > fast, confirm_bars)",),
            )
            source = _append_boolean_condition(source, "long_entry", "range_confirmed", operator="and")

        elif skill_id == "JMA_FAST_PROFIT_PROTECTION":
            if manifest:
                raise ValueError("JMA_FAST_PROFIT_PROTECTION은 parameter-free skill이어야 합니다.")
            source = _append_boolean_condition(source, "long_exit", "close < fast", operator="or")

        else:
            raise ValueError(f"JMA structural renderer가 지원하지 않는 skill입니다: {skill_id}")

        DSLParser.parse(source)
        if source == parent_dsl:
            raise ValueError(f"structural renderer가 DSL을 변경하지 않았습니다: {skill_id}")
        return source, manifest


class BoundedStructuralSkillGenerator:
    """Produce deterministic proposal-only children from legal registered skills."""

    _RENDERERS = {
        JmaTrendCrossResumeRenderer.FAMILY_ID: JmaTrendCrossResumeRenderer,
    }

    @staticmethod
    def _validate_evidence(
        *,
        family: TacticFamilySpec,
        parent_generation: EvolutionGeneration,
        parent_candidate: TacticCandidate,
        failure_report: Mapping[str, Any],
        characterization: Mapping[str, Any],
    ) -> None:
        family.validate()
        parent_candidate.validate()
        if parent_generation.family_id != family.family_id:
            raise ValueError("parent generation family_id가 TacticFamily와 다릅니다.")
        if parent_generation.candidate_hash != parent_candidate.candidate_hash:
            raise ValueError("parent generation candidate_hash와 parent candidate가 다릅니다.")
        metadata_family = str(parent_candidate.metadata.get("family_id") or "").strip()
        if metadata_family and metadata_family != family.family_id:
            raise ValueError("parent candidate metadata family_id가 TacticFamily와 다릅니다.")
        if str(failure_report.get("schema") or "") != "tactical_failure/v1":
            raise ValueError("failure_report는 tactical_failure/v1이어야 합니다.")
        if str(failure_report.get("profile_run_hash") or "") != parent_generation.profile_run_hash:
            raise ValueError("failure_report가 parent generation profile에서 생성되지 않았습니다.")
        if str(failure_report.get("case_set_hash") or "") != parent_generation.case_set_hash:
            raise ValueError("failure_report case_set_hash가 parent generation과 다릅니다.")
        if not str(failure_report.get("failure_hash") or "").strip():
            raise ValueError("failure_report failure_hash가 필요합니다.")

        if str(characterization.get("schema") or "") != "tactical_characterization/v1":
            raise ValueError("characterization은 tactical_characterization/v1이어야 합니다.")
        if str(characterization.get("profile_run_hash") or "") != parent_generation.profile_run_hash:
            raise ValueError("characterization profile_run_hash가 parent generation과 다릅니다.")
        if str(characterization.get("case_set_hash") or "") != parent_generation.case_set_hash:
            raise ValueError("characterization case_set_hash가 parent generation과 다릅니다.")
        if str(characterization.get("family_id") or "") != family.family_id:
            raise ValueError("characterization family_id가 TacticFamily와 다릅니다.")
        if str(characterization.get("generation_hash") or "") != parent_generation.generation_hash:
            raise ValueError("characterization generation_hash가 parent generation과 다릅니다.")
        if not str(characterization.get("characterization_hash") or "").strip():
            raise ValueError("characterization_hash가 필요합니다.")
        attached_failure = characterization.get("case_failure_analysis") or {}
        if str(attached_failure.get("failure_hash") or "") != str(failure_report.get("failure_hash") or ""):
            raise ValueError("characterization에 부착된 failure evidence가 failure_report와 다릅니다.")

    @staticmethod
    def _project_usage(
        family: TacticFamilySpec,
        generation: EvolutionGeneration,
        skill: SkillSpec,
    ) -> dict[str, int]:
        usage = {str(key): int(value) for key, value in dict(generation.capability_usage).items()}
        usage["skills"] = int(usage.get("skills", len(generation.acquired_skills))) + 1
        for key, value in skill.cost.items():
            usage[key] = int(usage.get(key, 0)) + int(value)
        family.budget.validate_usage(usage)
        return usage

    @classmethod
    def propose(
        cls,
        *,
        family: TacticFamilySpec,
        parent_generation: EvolutionGeneration,
        parent_candidate: TacticCandidate,
        failure_report: Mapping[str, Any],
        characterization: Mapping[str, Any],
        requested_skill_id: str = "",
    ) -> dict:
        cls._validate_evidence(
            family=family,
            parent_generation=parent_generation,
            parent_candidate=parent_candidate,
            failure_report=failure_report,
            characterization=characterization,
        )
        renderer = cls._RENDERERS.get(family.family_id)
        if renderer is None:
            raise ValueError(f"등록된 structural renderer가 없는 family입니다: {family.family_id}")

        legal = family.legal_skills(
            generation=parent_generation,
            failure_report=failure_report,
        )
        requested = str(requested_skill_id or "").strip()
        if requested:
            legal_map = {skill.skill_id: skill for skill in legal}
            if requested not in legal_map:
                raise ValueError(f"요청 skill이 현재 failure/dependency/budget 계약에서 legal하지 않습니다: {requested}")
            selected = (legal_map[requested],)
        else:
            selected = legal

        proposals = []
        for skill in selected:
            child_dsl, parameter_manifest = renderer.render(parent_candidate.dsl_code, skill)
            projected_usage = cls._project_usage(family, parent_generation, skill)
            complexity = int(parent_candidate.complexity_units) + int(skill.cost.get("complexity_units", 0))
            if complexity > int(projected_usage.get("complexity_units", complexity)):
                raise ValueError("child complexity가 projected capability usage를 초과합니다.")
            metadata = {
                **dict(parent_candidate.metadata),
                "family_id": family.family_id,
                "parent_candidate_hash": parent_candidate.candidate_hash,
                "parent_generation_hash": parent_generation.generation_hash,
                "generation_proposal": parent_generation.generation_index + 1,
                "proposed_skill_id": skill.skill_id,
                "proposed_capability": skill.capability,
                "failure_hash": str(failure_report.get("failure_hash") or ""),
                "characterization_hash": str(characterization.get("characterization_hash") or ""),
                "parameter_manifest": parameter_manifest,
                "mutation_policy": "ONE_REGISTERED_SKILL_ONLY",
            }
            candidate = TacticCandidate(
                candidate_id=f"{parent_candidate.candidate_id}__{skill.skill_id}",
                dsl_code=child_dsl,
                complexity_units=complexity,
                metadata=metadata,
            )
            candidate.validate()
            if candidate.candidate_hash == parent_candidate.candidate_hash:
                raise ValueError("generated child candidate_hash가 parent와 같습니다.")
            relevant_tags = tuple(
                sorted(
                    {
                        str(cluster.get("failure_tag") or "")
                        for cluster in failure_report.get("clusters", ())
                        if str(cluster.get("failure_tag") or "") in set(skill.addresses_failure_tags)
                    }
                )
            )
            proposal_identity = {
                "schema": SCHEMA_VERSION,
                "family_id": family.family_id,
                "parent_generation_hash": parent_generation.generation_hash,
                "parent_candidate_hash": parent_candidate.candidate_hash,
                "failure_hash": str(failure_report.get("failure_hash") or ""),
                "characterization_hash": str(characterization.get("characterization_hash") or ""),
                "skill_id": skill.skill_id,
                "relevant_failure_tags": relevant_tags,
                "projected_usage": projected_usage,
                "parameter_manifest": parameter_manifest,
                "child_candidate_hash": candidate.candidate_hash,
            }
            proposals.append(
                {
                    "skill_id": skill.skill_id,
                    "capability": skill.capability,
                    "implementation": skill.implementation,
                    "addresses_failure_tags": tuple(skill.addresses_failure_tags),
                    "relevant_failure_tags": relevant_tags,
                    "projected_capability_usage": projected_usage,
                    "parameter_manifest": parameter_manifest,
                    "candidate": {
                        "candidate_id": candidate.candidate_id,
                        "candidate_hash": candidate.candidate_hash,
                        "dsl_code": candidate.dsl_code,
                        "complexity_units": candidate.complexity_units,
                        "metadata": dict(candidate.metadata),
                    },
                    "proposal_hash": _stable_hash(proposal_identity),
                }
            )

        result_identity = {
            "schema": SCHEMA_VERSION,
            "family_id": family.family_id,
            "parent_generation_hash": parent_generation.generation_hash,
            "parent_candidate_hash": parent_candidate.candidate_hash,
            "failure_hash": str(failure_report.get("failure_hash") or ""),
            "characterization_hash": str(characterization.get("characterization_hash") or ""),
            "legal_skill_ids": [skill.skill_id for skill in legal],
            "proposal_hashes": [proposal["proposal_hash"] for proposal in proposals],
        }
        return {
            "schema": SCHEMA_VERSION,
            "family_id": family.family_id,
            "parent_generation_hash": parent_generation.generation_hash,
            "parent_candidate_hash": parent_candidate.candidate_hash,
            "profile_run_hash": parent_generation.profile_run_hash,
            "case_set_hash": parent_generation.case_set_hash,
            "failure_hash": str(failure_report.get("failure_hash") or ""),
            "characterization_hash": str(characterization.get("characterization_hash") or ""),
            "legal_skill_ids": tuple(skill.skill_id for skill in legal),
            "proposals": proposals,
            "selection_policy": "LEGAL_REGISTERED_SKILLS_ONLY_NO_AUTOMATIC_RANKING",
            "promotion_policy": "PROPOSAL_ONLY_REQUIRES_REPLAY_AND_EVOLUTION_ARENA",
            "generator_hash": _stable_hash(result_identity),
        }

    @staticmethod
    def materialize_candidate(proposal: Mapping[str, Any]) -> TacticCandidate:
        raw = dict(proposal.get("candidate") or {})
        candidate = TacticCandidate(
            candidate_id=str(raw.get("candidate_id") or ""),
            dsl_code=str(raw.get("dsl_code") or ""),
            complexity_units=int(raw.get("complexity_units") or 0),
            metadata=dict(raw.get("metadata") or {}),
        )
        candidate.validate()
        expected = str(raw.get("candidate_hash") or "")
        if not expected or candidate.candidate_hash != expected:
            raise ValueError("proposal candidate_hash가 materialized candidate와 다릅니다.")
        return candidate
