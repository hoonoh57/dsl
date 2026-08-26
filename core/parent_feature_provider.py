"""Deterministic parent-feature provider contracts for post-E8 context production.

This module is intentionally outside Instrument DSL execution. Providers own
calculation/source logic and publish immutable, typed point-in-time results.
Consumers receive only declared feature identities and BattlefieldContext
snapshots; no provider is called from Parser/Runtime/Backtest/Broker code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import math
from typing import Any, Mapping, Protocol, Sequence

from core.battlefield_context import BattlefieldContext, ContextLayerSnapshot


SCHEMA_VERSION = "parent_feature_provider/v1"
REGISTRY_SCHEMA_VERSION = "parent_feature_registry/v1"
ASSEMBLY_SCHEMA_VERSION = "parent_context_assembly/v1"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) == 8:
        return digits + "235959"
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"parent feature time은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _time_value(value: Any) -> datetime:
    return datetime.strptime(_time_key(value), "%Y%m%d%H%M%S")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("parent feature evidence에 NaN/Infinity를 사용할 수 없습니다.")
        return value
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


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _validate_value(value: Any, value_type: str, label: str) -> None:
    kind = str(value_type).strip().upper()
    if kind == "NUMBER":
        if isinstance(value, bool):
            raise ValueError(f"{label}는 NUMBER여야 합니다.")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label}는 NUMBER여야 합니다.") from exc
        if not math.isfinite(number):
            raise ValueError(f"{label}는 유한한 NUMBER여야 합니다.")
        return
    if kind == "STRING":
        if not isinstance(value, str):
            raise ValueError(f"{label}는 STRING이어야 합니다.")
        return
    if kind == "BOOLEAN":
        if not isinstance(value, bool):
            raise ValueError(f"{label}는 BOOLEAN이어야 합니다.")
        return
    raise ValueError(f"지원하지 않는 parent feature value_type: {value_type!r}")


@dataclass(frozen=True)
class ParentFeatureSpec:
    """One stable public feature identity produced by a parent provider."""

    feature_id: str
    feature_key: str
    value_type: str
    semantic_version: str = "v1"
    causality_policy: str = "CONFIRMED_ONLY"
    required: bool = True
    missing_policy: str = "FAIL_CLOSED"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    VALUE_TYPES = {"NUMBER", "STRING", "BOOLEAN"}
    CAUSALITY_POLICIES = {"CONFIRMED_ONLY"}
    MISSING_POLICIES = {"FAIL_CLOSED", "OPTIONAL_ABSENT"}

    def validate(self, *, layer: str) -> None:
        feature_id = _text(self.feature_id, "feature_id")
        _text(self.feature_key, "feature_key")
        _text(self.semantic_version, "feature semantic_version")
        if str(self.value_type).strip().upper() not in self.VALUE_TYPES:
            raise ValueError(f"parent feature value_type이 올바르지 않습니다: {self.value_type!r}")
        if str(self.causality_policy).strip().upper() not in self.CAUSALITY_POLICIES:
            raise ValueError(f"parent feature causality_policy가 올바르지 않습니다: {self.causality_policy!r}")
        missing = str(self.missing_policy).strip().upper()
        if missing not in self.MISSING_POLICIES:
            raise ValueError(f"parent feature missing_policy가 올바르지 않습니다: {self.missing_policy!r}")
        if bool(self.required) and missing != "FAIL_CLOSED":
            raise ValueError("required parent feature는 FAIL_CLOSED missing_policy여야 합니다.")
        if not bool(self.required) and missing != "OPTIONAL_ABSENT":
            raise ValueError("optional parent feature는 OPTIONAL_ABSENT missing_policy여야 합니다.")
        prefix = str(layer).strip().lower() + "."
        if not feature_id.lower().startswith(prefix):
            raise ValueError(f"feature_id는 layer namespace로 시작해야 합니다: {feature_id!r}, expected={prefix!r}")
        _json_safe(dict(self.metadata))

    def public_dict(self) -> dict:
        return {
            "feature_id": str(self.feature_id).strip(),
            "feature_key": str(self.feature_key).strip(),
            "value_type": str(self.value_type).strip().upper(),
            "semantic_version": str(self.semantic_version).strip(),
            "causality_policy": str(self.causality_policy).strip().upper(),
            "required": bool(self.required),
            "missing_policy": str(self.missing_policy).strip().upper(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ParentFeatureManifest:
    """Versioned provider contract; feature additions do not alter DSL grammar."""

    provider_id: str
    provider_version: str
    layer: str
    context_id: str
    features: tuple[ParentFeatureSpec, ...]
    max_staleness_seconds: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.provider_id, "provider_id")
        _text(self.provider_version, "provider_version")
        layer = _text(self.layer, "provider layer").upper()
        _text(self.context_id, "provider context_id")
        if not self.features:
            raise ValueError("parent feature manifest features가 비어 있습니다.")
        ids = []
        keys = []
        for spec in self.features:
            if not isinstance(spec, ParentFeatureSpec):
                raise ValueError("manifest feature는 ParentFeatureSpec이어야 합니다.")
            spec.validate(layer=layer)
            ids.append(str(spec.feature_id).strip())
            keys.append(str(spec.feature_key).strip())
        if len(set(ids)) != len(ids):
            raise ValueError("parent feature manifest feature_id에 중복이 있습니다.")
        if len(set(keys)) != len(keys):
            raise ValueError("parent feature manifest feature_key에 중복이 있습니다.")
        if self.max_staleness_seconds is not None and int(self.max_staleness_seconds) < 0:
            raise ValueError("max_staleness_seconds는 0 이상이어야 합니다.")
        _json_safe(dict(self.metadata))

    @property
    def manifest_hash(self) -> str:
        self.validate()
        ordered = sorted((spec.public_dict() for spec in self.features), key=lambda item: item["feature_id"])
        return _stable_hash(
            {
                "schema": SCHEMA_VERSION,
                "provider_id": str(self.provider_id).strip(),
                "provider_version": str(self.provider_version).strip(),
                "layer": str(self.layer).strip().upper(),
                "context_id": str(self.context_id).strip(),
                "features": ordered,
                "max_staleness_seconds": self.max_staleness_seconds,
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict:
        self.validate()
        return {
            "schema": SCHEMA_VERSION,
            "provider_id": str(self.provider_id).strip(),
            "provider_version": str(self.provider_version).strip(),
            "layer": str(self.layer).strip().upper(),
            "context_id": str(self.context_id).strip(),
            "features": sorted((spec.public_dict() for spec in self.features), key=lambda item: item["feature_id"]),
            "max_staleness_seconds": self.max_staleness_seconds,
            "metadata": dict(self.metadata),
            "manifest_hash": self.manifest_hash,
        }


@dataclass(frozen=True)
class ParentFeatureRegistry:
    """Deterministic discoverability contract for later generators/binders."""

    manifests: tuple[ParentFeatureManifest, ...]

    def validate(self) -> None:
        if not self.manifests:
            raise ValueError("parent feature registry manifests가 비어 있습니다.")
        providers = []
        feature_ids = []
        for manifest in self.manifests:
            manifest.validate()
            providers.append((str(manifest.provider_id).strip(), str(manifest.provider_version).strip()))
            feature_ids.extend(str(spec.feature_id).strip() for spec in manifest.features)
        if len(set(providers)) != len(providers):
            raise ValueError("parent feature registry provider/version에 중복이 있습니다.")
        if len(set(feature_ids)) != len(feature_ids):
            raise ValueError("parent feature registry feature_id가 여러 manifest에 중복됩니다.")

    def resolve(self, feature_id: str) -> dict:
        self.validate()
        wanted = _text(feature_id, "feature_id")
        for manifest in self.manifests:
            for spec in manifest.features:
                if str(spec.feature_id).strip() == wanted:
                    return {
                        "manifest": manifest.public_dict(),
                        "feature": spec.public_dict(),
                    }
        raise KeyError(wanted)

    @property
    def registry_hash(self) -> str:
        self.validate()
        manifests = sorted(
            (manifest.public_dict() for manifest in self.manifests),
            key=lambda item: (item["provider_id"], item["provider_version"]),
        )
        return _stable_hash({"schema": REGISTRY_SCHEMA_VERSION, "manifests": manifests})

    def public_dict(self) -> dict:
        self.validate()
        return {
            "schema": REGISTRY_SCHEMA_VERSION,
            "manifests": sorted(
                (manifest.public_dict() for manifest in self.manifests),
                key=lambda item: (item["provider_id"], item["provider_version"]),
            ),
            "registry_hash": self.registry_hash,
        }


@dataclass(frozen=True)
class ParentFeatureProviderResult:
    """Immutable output from one provider calculation at one causal cutoff."""

    manifest: ParentFeatureManifest
    as_of: str
    knowledge_cutoff: str
    source: str
    features: Mapping[str, Any]
    dependency_result_hashes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.manifest.validate()
        as_of = _time_key(self.as_of)
        cutoff = _time_key(self.knowledge_cutoff)
        if as_of > cutoff:
            raise ValueError("parent feature result가 knowledge_cutoff보다 미래입니다.")
        if self.manifest.max_staleness_seconds is not None:
            age = (_time_value(cutoff) - _time_value(as_of)).total_seconds()
            if age > int(self.manifest.max_staleness_seconds):
                raise ValueError("parent feature result가 manifest staleness 한도를 초과했습니다.")
        _text(self.source, "parent feature source")
        supplied = {str(key): value for key, value in self.features.items()}
        declared = {str(spec.feature_key).strip(): spec for spec in self.manifest.features}
        unknown = sorted(set(supplied) - set(declared))
        if unknown:
            raise ValueError(f"manifest에 선언되지 않은 parent feature가 있습니다: {unknown}")
        for key, spec in declared.items():
            if key not in supplied:
                if bool(spec.required):
                    raise ValueError(f"required parent feature가 없습니다: {spec.feature_id}")
                continue
            _validate_value(supplied[key], spec.value_type, str(spec.feature_id))
        dependencies = tuple(str(item).strip() for item in self.dependency_result_hashes)
        if any(not item for item in dependencies) or len(set(dependencies)) != len(dependencies):
            raise ValueError("dependency_result_hashes는 비어 있지 않은 고유 hash여야 합니다.")
        _json_safe(dict(self.metadata))

    @property
    def layer_snapshot(self) -> ContextLayerSnapshot:
        self.validate()
        return ContextLayerSnapshot(
            layer=str(self.manifest.layer).strip().upper(),
            context_id=str(self.manifest.context_id).strip(),
            as_of=_time_key(self.as_of),
            source=str(self.source).strip(),
            features=dict(self.features),
        )

    @property
    def result_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": SCHEMA_VERSION,
                "manifest_hash": self.manifest.manifest_hash,
                "snapshot_hash": self.layer_snapshot.snapshot_hash,
                "knowledge_cutoff": _time_key(self.knowledge_cutoff),
                "dependency_result_hashes": sorted(self.dependency_result_hashes),
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict:
        self.validate()
        return {
            "schema": SCHEMA_VERSION,
            "manifest": self.manifest.public_dict(),
            "as_of": _time_key(self.as_of),
            "knowledge_cutoff": _time_key(self.knowledge_cutoff),
            "source": str(self.source).strip(),
            "features": dict(self.features),
            "dependency_result_hashes": tuple(sorted(self.dependency_result_hashes)),
            "metadata": dict(self.metadata),
            "snapshot_hash": self.layer_snapshot.snapshot_hash,
            "result_hash": self.result_hash,
        }


class ParentFeatureProvider(Protocol):
    """Calculation seam. Concrete implementations may use source adapters externally."""

    @property
    def manifest(self) -> ParentFeatureManifest: ...

    def build(
        self,
        *,
        as_of: str,
        knowledge_cutoff: str,
        dependencies: Mapping[str, ParentFeatureProviderResult] | None = None,
    ) -> ParentFeatureProviderResult: ...


@dataclass(frozen=True)
class ParentContextAssembly:
    context: BattlefieldContext
    knowledge_cutoff: str
    provider_result_hashes: tuple[str, ...]
    manifest_hashes: tuple[str, ...]

    @property
    def assembly_hash(self) -> str:
        return _stable_hash(
            {
                "schema": ASSEMBLY_SCHEMA_VERSION,
                "context_hash": self.context.context_hash,
                "knowledge_cutoff": _time_key(self.knowledge_cutoff),
                "provider_result_hashes": tuple(sorted(self.provider_result_hashes)),
                "manifest_hashes": tuple(sorted(self.manifest_hashes)),
            }
        )

    def public_dict(self) -> dict:
        self.context.validate_for(self.knowledge_cutoff)
        return {
            "schema": ASSEMBLY_SCHEMA_VERSION,
            "context": self.context.public_dict(),
            "knowledge_cutoff": _time_key(self.knowledge_cutoff),
            "provider_result_hashes": tuple(sorted(self.provider_result_hashes)),
            "manifest_hashes": tuple(sorted(self.manifest_hashes)),
            "assembly_hash": self.assembly_hash,
        }


class ParentContextAssembler:
    """Combine provider results without invoking provider calculation logic."""

    @classmethod
    def assemble(
        cls,
        *,
        as_of: str,
        knowledge_cutoff: str,
        results: Sequence[ParentFeatureProviderResult],
        mode: str = "OBSERVED",
        metadata: Mapping[str, Any] | None = None,
    ) -> ParentContextAssembly:
        context_as_of = _time_key(as_of)
        cutoff = _time_key(knowledge_cutoff)
        if context_as_of > cutoff:
            raise ValueError("parent context assembly as_of가 knowledge_cutoff보다 미래입니다.")
        normalized_mode = str(mode).strip().upper()
        if normalized_mode not in {"OBSERVED", "DEPLOYMENT"}:
            raise ValueError("parent context assembly mode는 OBSERVED 또는 DEPLOYMENT여야 합니다.")
        items = tuple(results)
        if not items:
            raise ValueError("parent context assembly results가 비어 있습니다.")
        for result in items:
            if not isinstance(result, ParentFeatureProviderResult):
                raise ValueError("parent context assembly item은 ParentFeatureProviderResult여야 합니다.")
            result.validate()
            if _time_key(result.knowledge_cutoff) != cutoff:
                raise ValueError("provider result knowledge_cutoff가 assembly cutoff와 다릅니다.")
            if _time_key(result.as_of) > context_as_of:
                raise ValueError("provider result가 assembly as_of보다 미래입니다.")

        result_by_hash = {item.result_hash: item for item in items}
        if len(result_by_hash) != len(items):
            raise ValueError("parent context assembly provider result_hash에 중복이 있습니다.")
        layer_keys = [(item.manifest.layer.upper(), item.manifest.context_id) for item in items]
        if len(set(layer_keys)) != len(layer_keys):
            raise ValueError("parent context assembly layer/context_id에 중복이 있습니다.")

        known_hashes = set(result_by_hash)
        for item in items:
            for dependency_hash in item.dependency_result_hashes:
                if dependency_hash not in known_hashes:
                    raise ValueError(f"parent provider dependency result가 assembly에 없습니다: {dependency_hash}")
                dependency = result_by_hash[dependency_hash]
                if _time_key(dependency.as_of) > _time_key(item.as_of):
                    raise ValueError("parent provider dependency가 child provider result보다 미래입니다.")

        ordered = tuple(
            sorted(
                items,
                key=lambda item: (
                    str(item.manifest.layer).strip().upper(),
                    str(item.manifest.context_id).strip(),
                    str(item.manifest.provider_id).strip(),
                    str(item.manifest.provider_version).strip(),
                ),
            )
        )
        result_hashes = tuple(item.result_hash for item in ordered)
        manifest_hashes = tuple(item.manifest.manifest_hash for item in ordered)
        context_metadata = dict(metadata or {})
        context_metadata["parent_feature_contract"] = ASSEMBLY_SCHEMA_VERSION
        context_metadata["parent_feature_result_hashes"] = result_hashes
        context_metadata["parent_feature_manifest_hashes"] = manifest_hashes
        context_metadata["parent_feature_knowledge_cutoff"] = cutoff
        context_metadata["assembly_policy"] = "PRECOMPUTED_IMMUTABLE_CAUSAL_PROVIDER_RESULTS_ONLY"
        context = BattlefieldContext(
            as_of=context_as_of,
            mode=normalized_mode,
            layers=tuple(item.layer_snapshot for item in ordered),
            metadata=context_metadata,
        )
        context.validate_for(cutoff)
        return ParentContextAssembly(
            context=context,
            knowledge_cutoff=cutoff,
            provider_result_hashes=result_hashes,
            manifest_hashes=manifest_hashes,
        )
