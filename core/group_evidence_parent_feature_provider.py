"""Registered GROUP parent features derived from precomputed MSA2 evidence.

MSA3 is a narrow publication bridge.  It does not run MSA1/MSA2 analysis,
discover symbols, rank peers, call DSL/Backtest/Broker, or create deployment
authority.  It reads an immutable exact-time MSA2 evidence timeline and
publishes only bounded aggregate GROUP features through the PCTX1 contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

from core.multi_symbol_group_evidence import (
    ANALYSIS_POLICY as MSA2_ANALYSIS_POLICY,
    SCHEMA_VERSION as MSA2_SCHEMA_VERSION,
    TOPOLOGY_POLICY as MSA2_TOPOLOGY_POLICY,
)
from core.parent_feature_provider import (
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureSpec,
)


PROVIDER_VERSION = "v1"
CALCULATION_POLICY = (
    "EXACT_PRECOMPUTED_MSA2_EVIDENCE_PLUS_EXPLICIT_SECTOR_DEPENDENCY_"
    "NO_PEER_RUNTIME_READ_NO_DEPLOYMENT_AUTHORITY"
)
PUBLICATION_STATE = "RESEARCH_ONLY"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"GROUP evidence time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _namespace(value: str) -> str:
    result = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", result):
        raise ValueError("group namespace는 소문자 영문자로 시작하는 식별자여야 합니다.")
    return result


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


def _rate(value: Any, label: str) -> float:
    number = _finite(value, label)
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{label}은 0..1 범위여야 합니다.")
    return number


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("GROUP parent evidence에 NaN/Infinity를 사용할 수 없습니다.")
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


def _validated_msa2_evidence(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("MSA3 evidence item은 Mapping이어야 합니다.")
    evidence = dict(raw)
    if evidence.get("schema") != MSA2_SCHEMA_VERSION:
        raise ValueError("MSA3는 multi_symbol_group_evidence/v1만 허용합니다.")
    if evidence.get("analysis_policy") != MSA2_ANALYSIS_POLICY:
        raise ValueError("MSA3 evidence analysis_policy가 MSA2와 다릅니다.")
    if evidence.get("topology_policy") != MSA2_TOPOLOGY_POLICY:
        raise ValueError("MSA3 evidence topology_policy가 MSA2와 다릅니다.")
    if str(evidence.get("mode") or "").strip().upper() != "OBSERVATION_ONLY":
        raise ValueError("MSA3는 OBSERVATION_ONLY MSA2 evidence만 허용합니다.")
    if evidence.get("operational_authority") is not False:
        raise ValueError("MSA3 source evidence는 operational_authority=false여야 합니다.")

    start = _time_key(evidence.get("start_as_of"))
    end = _time_key(evidence.get("end_as_of"))
    if start > end:
        raise ValueError("MSA3 evidence start_as_of가 end_as_of보다 늦습니다.")
    latest = evidence.get("latest")
    if not isinstance(latest, Mapping):
        raise ValueError("MSA3 evidence latest가 필요합니다.")
    latest = dict(latest)
    if _time_key(latest.get("as_of")) != end:
        raise ValueError("MSA3 evidence latest.as_of가 end_as_of와 다릅니다.")

    policy = evidence.get("policy")
    if not isinstance(policy, Mapping):
        raise ValueError("MSA3 evidence policy가 필요합니다.")
    policy_hash = _text(policy.get("policy_hash"), "MSA3 MSA2 policy_hash")
    universe_id = _text(evidence.get("universe_id"), "MSA3 universe_id")
    source_authority = _text(evidence.get("source_authority"), "MSA3 source_authority")
    symbols = tuple(_text(item, "MSA3 universe symbol") for item in tuple(evidence.get("symbols") or ()))
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("MSA3 evidence symbols가 비어 있거나 중복됩니다.")
    point_hashes = tuple(_text(item, "MSA3 point_hash") for item in tuple(evidence.get("point_hashes") or ()))
    points = tuple(evidence.get("points") or ())
    if not point_hashes or len(point_hashes) != len(points):
        raise ValueError("MSA3 evidence point_hashes/points가 비어 있거나 길이가 다릅니다.")
    if int(evidence.get("point_count") or 0) != len(points):
        raise ValueError("MSA3 evidence point_count가 points와 다릅니다.")

    identity = {
        "schema": MSA2_SCHEMA_VERSION,
        "analysis_policy": MSA2_ANALYSIS_POLICY,
        "topology_policy": MSA2_TOPOLOGY_POLICY,
        "policy_hash": policy_hash,
        "universe_id": universe_id,
        "symbols": symbols,
        "source_authority": source_authority,
        "point_hashes": point_hashes,
        "point_evidence": points,
        "latest": latest,
    }
    expected_hash = _stable_hash(identity)
    actual_hash = _text(evidence.get("result_hash"), "MSA3 MSA2 result_hash")
    if actual_hash != expected_hash:
        raise ValueError("MSA3 MSA2 result_hash가 evidence payload와 일치하지 않습니다.")

    _rate(latest.get("comparison_eligible_rate"), "comparison_eligible_rate")
    _rate(latest.get("favorable_breadth_rate"), "favorable_breadth_rate")
    persistence = tuple(latest.get("leader_persistence") or ())
    leaders = tuple(_text(item, "MSA3 leader symbol") for item in tuple(latest.get("leader_symbols") or ()))
    if not leaders or len(persistence) != len(leaders):
        raise ValueError("MSA3 leader_persistence가 current leaders와 일치하지 않습니다.")
    persistence_symbols = []
    for row in persistence:
        if not isinstance(row, Mapping):
            raise ValueError("MSA3 leader_persistence row는 Mapping이어야 합니다.")
        persistence_symbols.append(_text(row.get("symbol"), "MSA3 persistence symbol"))
        _rate(row.get("leader_persistence_rate"), "leader_persistence_rate")
    if set(persistence_symbols) != set(leaders):
        raise ValueError("MSA3 leader_persistence symbol 집합이 leader_symbols와 다릅니다.")

    spread = latest.get("leader_follower_spread")
    if spread is not None:
        _finite(spread, "leader_follower_spread")
    follower_rate = latest.get("follower_favorable_rate")
    if follower_rate is not None:
        _rate(follower_rate, "follower_favorable_rate")
    _json_safe(evidence)
    return evidence


@dataclass(frozen=True)
class ImmutableGroupEvidenceTimeline:
    """Exact-time lookup source for already-computed MSA2 evidence."""

    evidence: tuple[Mapping[str, Any], ...]

    def validate(self) -> None:
        if not self.evidence:
            raise ValueError("MSA3 evidence timeline이 비어 있습니다.")
        times = []
        for raw in self.evidence:
            item = _validated_msa2_evidence(raw)
            times.append(_time_key(item["end_as_of"]))
        if len(set(times)) != len(times) or any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
            raise ValueError("MSA3 evidence timeline은 exact end_as_of 기준 엄격 오름차순이어야 합니다.")

    def resolve(self, target_time: str) -> dict[str, Any]:
        self.validate()
        target = _time_key(target_time)
        for raw in self.evidence:
            item = _validated_msa2_evidence(raw)
            if _time_key(item["end_as_of"]) == target:
                return item
        raise KeyError(target)

    @property
    def timeline_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "policy": "EXACT_PRECOMPUTED_MSA2_EVIDENCE_NO_NEAREST_NO_FILL_FORWARD",
                "items": tuple(
                    {
                        "end_as_of": _time_key(item["end_as_of"]),
                        "result_hash": _text(item["result_hash"], "MSA3 result_hash"),
                    }
                    for item in self.evidence
                ),
            }
        )


class GroupEvidenceParentFeatureProvider:
    """Publish aggregate MSA2 evidence as registered research-only GROUP context."""

    def __init__(
        self,
        timeline: ImmutableGroupEvidenceTimeline,
        *,
        group_namespace: str,
        universe_id: str,
        evidence_source_authority: str,
        msa2_policy_hash: str,
        metric_id: str,
        sector_dependency_provider_id: str,
    ):
        if not isinstance(timeline, ImmutableGroupEvidenceTimeline):
            raise ValueError("timeline은 ImmutableGroupEvidenceTimeline이어야 합니다.")
        timeline.validate()
        self.timeline = timeline
        self.group_namespace = _namespace(group_namespace)
        self.universe_id = _text(universe_id, "group universe_id")
        self.evidence_source_authority = _text(evidence_source_authority, "group evidence_source_authority")
        self.msa2_policy_hash = _text(msa2_policy_hash, "group msa2_policy_hash")
        self.metric_id = _text(metric_id, "group metric_id")
        self.sector_dependency_provider_id = _text(
            sector_dependency_provider_id, "group sector_dependency_provider_id"
        )

        ns = self.group_namespace
        prefix = f"group.{ns}_"
        self._manifest = ParentFeatureManifest(
            provider_id=f"msa2_group_evidence_{ns}",
            provider_version=PROVIDER_VERSION,
            layer="GROUP",
            context_id=f"{ns.upper()}_MSA2_GROUP_EVIDENCE",
            max_staleness_seconds=0,
            features=(
                ParentFeatureSpec(prefix + "comparison_eligible_rate", "comparison_eligible_rate", "NUMBER"),
                ParentFeatureSpec(prefix + "favorable_breadth_rate", "favorable_breadth_rate", "NUMBER"),
                ParentFeatureSpec(prefix + "leader_persistence_rate", "leader_persistence_rate", "NUMBER"),
                ParentFeatureSpec(
                    prefix + "leader_follower_spread",
                    "leader_follower_spread",
                    "NUMBER",
                    required=False,
                    missing_policy="OPTIONAL_ABSENT",
                ),
                ParentFeatureSpec(
                    prefix + "follower_favorable_rate",
                    "follower_favorable_rate",
                    "NUMBER",
                    required=False,
                    missing_policy="OPTIONAL_ABSENT",
                ),
            ),
            metadata={
                "calculation_policy": CALCULATION_POLICY,
                "publication_state": PUBLICATION_STATE,
                "operational_authority": False,
                "publishes_peer_symbol_identities": False,
                "universe_id": self.universe_id,
                "evidence_source_authority": self.evidence_source_authority,
                "msa2_policy_hash": self.msa2_policy_hash,
                "metric_id": self.metric_id,
                "sector_dependency_provider_id": self.sector_dependency_provider_id,
                "timeline_hash": self.timeline.timeline_hash,
            },
        )
        self._manifest.validate()

    @property
    def manifest(self) -> ParentFeatureManifest:
        return self._manifest

    def _dependency(
        self,
        dependencies: Mapping[str, ParentFeatureProviderResult] | None,
        target: str,
    ) -> ParentFeatureProviderResult:
        if not dependencies or set(dependencies) != {self.sector_dependency_provider_id}:
            raise ValueError("GROUP provider는 선언된 SECTOR dependency 하나만 필요합니다.")
        parent = dependencies[self.sector_dependency_provider_id]
        if not isinstance(parent, ParentFeatureProviderResult):
            raise ValueError("SECTOR dependency는 ParentFeatureProviderResult여야 합니다.")
        parent.validate()
        if str(parent.manifest.provider_id).strip() != self.sector_dependency_provider_id:
            raise ValueError("GROUP SECTOR dependency provider_id가 다릅니다.")
        if str(parent.manifest.layer).strip().upper() != "SECTOR":
            raise ValueError("GROUP dependency manifest layer는 SECTOR여야 합니다.")
        if _time_key(parent.as_of) != target or _time_key(parent.knowledge_cutoff) != target:
            raise ValueError("GROUP SECTOR dependency가 exact target timestamp와 다릅니다.")
        return parent

    def _evidence(self, target: str) -> dict[str, Any]:
        try:
            evidence = self.timeline.resolve(target)
        except KeyError as exc:
            raise ValueError("GROUP provider에 exact target MSA2 evidence가 없습니다.") from exc
        if _text(evidence["universe_id"], "GROUP evidence universe_id") != self.universe_id:
            raise ValueError("GROUP evidence universe_id가 provider 선언과 다릅니다.")
        if _text(evidence["source_authority"], "GROUP evidence source_authority") != self.evidence_source_authority:
            raise ValueError("GROUP evidence source_authority가 provider 선언과 다릅니다.")
        policy_hash = _text(evidence["policy"]["policy_hash"], "GROUP evidence policy_hash")
        if policy_hash != self.msa2_policy_hash:
            raise ValueError("GROUP evidence policy_hash가 provider 선언과 다릅니다.")
        latest = dict(evidence["latest"])
        if _text(latest.get("metric_id"), "GROUP evidence metric_id") != self.metric_id:
            raise ValueError("GROUP evidence metric_id가 provider 선언과 다릅니다.")
        if _time_key(evidence["end_as_of"]) != target or _time_key(latest["as_of"]) != target:
            raise ValueError("GROUP evidence가 exact target timestamp와 다릅니다.")
        return evidence

    def build(
        self,
        *,
        as_of: str,
        knowledge_cutoff: str,
        dependencies: Mapping[str, ParentFeatureProviderResult] | None = None,
    ) -> ParentFeatureProviderResult:
        target = _time_key(as_of)
        cutoff = _time_key(knowledge_cutoff)
        if target != cutoff:
            raise ValueError("GROUP provider는 exact as_of == knowledge_cutoff를 요구합니다.")
        sector_parent = self._dependency(dependencies, target)
        evidence = self._evidence(target)
        latest = dict(evidence["latest"])
        persistence = tuple(latest["leader_persistence"])
        persistence_rate = sum(
            _rate(row["leader_persistence_rate"], "leader_persistence_rate")
            for row in persistence
        ) / len(persistence)

        features: dict[str, Any] = {
            "comparison_eligible_rate": _rate(latest["comparison_eligible_rate"], "comparison_eligible_rate"),
            "favorable_breadth_rate": _rate(latest["favorable_breadth_rate"], "favorable_breadth_rate"),
            "leader_persistence_rate": _rate(persistence_rate, "leader_persistence_rate"),
        }
        if latest.get("leader_follower_spread") is not None:
            features["leader_follower_spread"] = _finite(
                latest["leader_follower_spread"], "leader_follower_spread"
            )
        if latest.get("follower_favorable_rate") is not None:
            features["follower_favorable_rate"] = _rate(
                latest["follower_favorable_rate"], "follower_favorable_rate"
            )

        result = ParentFeatureProviderResult(
            manifest=self.manifest,
            as_of=target,
            knowledge_cutoff=cutoff,
            source=f"MSA2::{self.evidence_source_authority}::{self.universe_id}",
            features=features,
            dependency_result_hashes=(sector_parent.result_hash,),
            metadata={
                "calculation_policy": CALCULATION_POLICY,
                "publication_state": PUBLICATION_STATE,
                "operational_authority": False,
                "publishes_peer_symbol_identities": False,
                "msa2_result_hash": evidence["result_hash"],
                "msa2_policy_hash": self.msa2_policy_hash,
                "msa2_point_hashes": tuple(evidence["point_hashes"]),
                "evidence_start_as_of": _time_key(evidence["start_as_of"]),
                "evidence_end_as_of": target,
                "evidence_point_count": int(evidence["point_count"]),
                "timeline_hash": self.timeline.timeline_hash,
                "sector_dependency_result_hash": sector_parent.result_hash,
            },
        )
        result.validate()
        return result
