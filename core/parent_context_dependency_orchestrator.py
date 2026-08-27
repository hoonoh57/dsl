"""Explicit dependency-DAG orchestration for parent-context providers.

PCTX2D extends the trusted root-only PCTX2C precomputation model without moving
provider execution into Parser/Runtime/Backtest/Broker.  Callers declare the
provider graph explicitly.  For every exact target timestamp, providers are
run in deterministic topological order and receive only the declared immutable
parent results for that same timestamp.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureProvider,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
)
from core.parent_context_orchestrator import _target_timeline


SCHEMA_VERSION = "parent_context_dependency_frame_build/v1"
BUILD_POLICY = "EXPLICIT_DEPENDENCY_DAG_PRECOMPUTE_EVERY_EXACT_TARGET_BAR"


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


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _time_key(value: Any) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"parent context target time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


@dataclass(frozen=True)
class ParentProviderNode:
    """One explicitly wired provider in the causal dependency graph."""

    provider: ParentFeatureProvider
    depends_on: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def provider_id(self) -> str:
        manifest = getattr(self.provider, "manifest", None)
        if manifest is None:
            raise ValueError("dependency provider manifest가 필요합니다.")
        manifest.validate()
        return str(manifest.provider_id).strip()

    @property
    def provider_version(self) -> str:
        manifest = self.provider.manifest
        manifest.validate()
        return str(manifest.provider_version).strip()

    def validate(self) -> None:
        _text(self.provider_id, "dependency provider_id")
        _text(self.provider_version, "dependency provider_version")
        normalized = tuple(_text(item, "depends_on provider_id") for item in self.depends_on)
        if len(set(normalized)) != len(normalized):
            raise ValueError(f"provider {self.provider_id} depends_on에 중복이 있습니다.")
        if self.provider_id in normalized:
            raise ValueError(f"provider {self.provider_id}는 자기 자신에 의존할 수 없습니다.")
        json.dumps(dict(self.metadata), ensure_ascii=False, sort_keys=True, default=str, allow_nan=False)


@dataclass(frozen=True)
class DependencyParentContextFrameBuild:
    registry: ParentFeatureRegistry
    frame: ParentContextFrame
    target_times: tuple[str, ...]
    target_timeline_hash: str
    provider_order: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    mode: str

    def validate(self) -> None:
        self.registry.validate()
        self.frame.validate()
        if self.frame.registry_hash != self.registry.registry_hash:
            raise ValueError("dependency frame registry_hash가 registry와 다릅니다.")
        frame_times = tuple(_time_key(point.target_time) for point in self.frame.points)
        expected_times = tuple(_time_key(item) for item in self.target_times)
        if frame_times != expected_times:
            raise ValueError("dependency frame target_times가 exact frame points와 다릅니다.")
        if not self.provider_order or len(set(self.provider_order)) != len(self.provider_order):
            raise ValueError("dependency frame provider_order가 비어 있거나 중복됩니다.")
        known = set(self.provider_order)
        for parent_id, child_id in self.dependency_edges:
            if parent_id not in known or child_id not in known:
                raise ValueError("dependency frame edge가 알려지지 않은 provider를 참조합니다.")
        if str(self.mode).strip().upper() != str(self.frame.mode).strip().upper():
            raise ValueError("dependency frame mode가 frame mode와 다릅니다.")
        _text(self.target_timeline_hash, "dependency target_timeline_hash")

    @property
    def build_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": SCHEMA_VERSION,
                "policy": BUILD_POLICY,
                "registry_hash": self.registry.registry_hash,
                "frame_hash": self.frame.frame_hash,
                "target_times": self.target_times,
                "target_timeline_hash": self.target_timeline_hash,
                "provider_order": self.provider_order,
                "dependency_edges": self.dependency_edges,
                "mode": str(self.mode).strip().upper(),
            }
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": SCHEMA_VERSION,
            "policy": BUILD_POLICY,
            "registry_hash": self.registry.registry_hash,
            "frame_hash": self.frame.frame_hash,
            "target_symbol": self.frame.target_symbol,
            "target_times": self.target_times,
            "target_timeline_hash": self.target_timeline_hash,
            "provider_order": self.provider_order,
            "dependency_edges": self.dependency_edges,
            "mode": str(self.mode).strip().upper(),
            "build_hash": self.build_hash,
        }


class DependencyParentContextFrameBuilder:
    """Precompute exact parent context from one explicit provider DAG."""

    @staticmethod
    def _normalize(nodes: Sequence[ParentProviderNode]) -> tuple[tuple[ParentProviderNode, ...], tuple[tuple[str, str], ...]]:
        items = tuple(nodes)
        if not items:
            raise ValueError("parent context dependency nodes가 비어 있습니다.")
        for node in items:
            if not isinstance(node, ParentProviderNode):
                raise ValueError("dependency node는 ParentProviderNode여야 합니다.")
            node.validate()
        by_id = {node.provider_id: node for node in items}
        if len(by_id) != len(items):
            raise ValueError("parent context dependency provider_id에 중복이 있습니다.")
        provider_versions = [(node.provider_id, node.provider_version) for node in items]
        if len(set(provider_versions)) != len(provider_versions):
            raise ValueError("parent context dependency provider/version에 중복이 있습니다.")

        unknown = sorted(
            {
                dependency
                for node in items
                for dependency in node.depends_on
                if dependency not in by_id
            }
        )
        if unknown:
            raise ValueError(f"알려지지 않은 parent provider dependency가 있습니다: {unknown}")

        indegree = {provider_id: 0 for provider_id in by_id}
        children = {provider_id: set() for provider_id in by_id}
        edges = []
        for node in items:
            for parent_id in node.depends_on:
                indegree[node.provider_id] += 1
                children[parent_id].add(node.provider_id)
                edges.append((parent_id, node.provider_id))

        ready = sorted(provider_id for provider_id, count in indegree.items() if count == 0)
        ordered_ids = []
        while ready:
            current = ready.pop(0)
            ordered_ids.append(current)
            for child_id in sorted(children[current]):
                indegree[child_id] -= 1
                if indegree[child_id] == 0:
                    ready.append(child_id)
                    ready.sort()
        if len(ordered_ids) != len(by_id):
            raise ValueError("parent provider dependency graph에 cycle이 있습니다.")

        ordered = tuple(by_id[provider_id] for provider_id in ordered_ids)
        return ordered, tuple(sorted(edges))

    @classmethod
    def build(
        cls,
        *,
        frame_id: str,
        target_market: Mapping[str, Any],
        nodes: Sequence[ParentProviderNode],
        mode: str = "OBSERVED",
    ) -> DependencyParentContextFrameBuild:
        frame_id = _text(frame_id, "parent context dependency frame_id")
        target_symbol, timeframe, target_source, target_times, timeline_hash = _target_timeline(target_market)
        normalized_mode = str(mode).strip().upper()
        if normalized_mode not in {"OBSERVED", "DEPLOYMENT"}:
            raise ValueError("parent context dependency mode는 OBSERVED 또는 DEPLOYMENT여야 합니다.")

        ordered_nodes, edges = cls._normalize(nodes)
        registry = ParentFeatureRegistry(tuple(node.provider.manifest for node in ordered_nodes))
        registry.validate()
        assemblies = []

        for target_time in target_times:
            results_by_id: dict[str, ParentFeatureProviderResult] = {}
            for node in ordered_nodes:
                dependencies = {
                    parent_id: results_by_id[parent_id]
                    for parent_id in node.depends_on
                }
                result = node.provider.build(
                    as_of=target_time,
                    knowledge_cutoff=target_time,
                    dependencies=(dependencies or None),
                )
                if not isinstance(result, ParentFeatureProviderResult):
                    raise ValueError("dependency provider는 ParentFeatureProviderResult를 반환해야 합니다.")
                result.validate()
                if result.manifest.manifest_hash != node.provider.manifest.manifest_hash:
                    raise ValueError("dependency provider result manifest가 provider 선언과 다릅니다.")
                if _time_key(result.as_of) != target_time or _time_key(result.knowledge_cutoff) != target_time:
                    raise ValueError("dependency provider result가 exact target timestamp와 다릅니다.")
                expected_hashes = tuple(sorted(item.result_hash for item in dependencies.values()))
                actual_hashes = tuple(sorted(str(item) for item in result.dependency_result_hashes))
                if actual_hashes != expected_hashes:
                    raise ValueError(
                        f"provider {node.provider_id} dependency_result_hashes가 선언 DAG와 다릅니다."
                    )
                results_by_id[node.provider_id] = result

            assemblies.append(
                ParentContextAssembler.assemble(
                    as_of=target_time,
                    knowledge_cutoff=target_time,
                    results=tuple(results_by_id[node.provider_id] for node in ordered_nodes),
                    mode=normalized_mode,
                    metadata={
                        "orchestration_policy": BUILD_POLICY,
                        "target_symbol": target_symbol,
                        "target_timeframe": timeframe,
                        "target_source": target_source,
                        "target_timeline_hash": timeline_hash,
                        "provider_order": tuple(node.provider_id for node in ordered_nodes),
                        "dependency_edges": edges,
                    },
                )
            )

        frame = ParentContextFrame.create(
            frame_id=frame_id,
            target_symbol=target_symbol,
            registry=registry,
            assemblies=tuple(assemblies),
            mode=normalized_mode,
            metadata={
                "orchestration_policy": BUILD_POLICY,
                "target_timeframe": timeframe,
                "target_source": target_source,
                "target_timeline_hash": timeline_hash,
                "provider_order": tuple(node.provider_id for node in ordered_nodes),
                "dependency_edges": edges,
            },
        )
        bundle = DependencyParentContextFrameBuild(
            registry=registry,
            frame=frame,
            target_times=target_times,
            target_timeline_hash=timeline_hash,
            provider_order=tuple(node.provider_id for node in ordered_nodes),
            dependency_edges=edges,
            mode=normalized_mode,
        )
        bundle.validate()
        return bundle
