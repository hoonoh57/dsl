"""Exact-time causal parent-context frames and read-only feature binding.

PCTX2B sits between PCTX1 provider assemblies and any future Instrument DSL
context reference.  It deliberately does not call providers, Parser, Runtime,
Backtest or Broker code.  Every target timestamp must have an explicitly
precomputed ParentContextAssembly at the exact same knowledge cutoff; there is
no nearest-time lookup, implicit fill-forward or silent defaulting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from core.battlefield_context import BattlefieldContext
from core.parent_feature_provider import (
    ParentContextAssembly,
    ParentFeatureRegistry,
)


FRAME_SCHEMA_VERSION = "parent_context_frame/v1"
BINDING_SCHEMA_VERSION = "parent_context_binding/v1"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) == 8:
        return digits + "235959"
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"parent context frame time은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("parent context frame에 NaN/Infinity를 사용할 수 없습니다.")
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


def _validate_typed_value(value: Any, value_type: str, feature_id: str) -> None:
    kind = str(value_type).strip().upper()
    if kind == "NUMBER":
        if isinstance(value, bool):
            raise ValueError(f"bound parent feature는 NUMBER여야 합니다: {feature_id}")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"bound parent feature는 NUMBER여야 합니다: {feature_id}") from exc
        if not math.isfinite(number):
            raise ValueError(f"bound parent feature NUMBER는 유한해야 합니다: {feature_id}")
        return
    if kind == "STRING":
        if not isinstance(value, str):
            raise ValueError(f"bound parent feature는 STRING이어야 합니다: {feature_id}")
        return
    if kind == "BOOLEAN":
        if not isinstance(value, bool):
            raise ValueError(f"bound parent feature는 BOOLEAN이어야 합니다: {feature_id}")
        return
    raise ValueError(f"지원하지 않는 bound parent feature type: {value_type!r}")


@dataclass(frozen=True)
class ParentContextPoint:
    """One exact decision-time context point backed by a PCTX1 assembly."""

    target_time: str
    assembly: ParentContextAssembly

    def validate(
        self,
        *,
        mode: str,
        manifest_hashes: Sequence[str],
    ) -> None:
        target = _time_key(self.target_time)
        if not isinstance(self.assembly, ParentContextAssembly):
            raise ValueError("parent context point assembly는 ParentContextAssembly여야 합니다.")
        self.assembly.public_dict()
        if _time_key(self.assembly.knowledge_cutoff) != target:
            raise ValueError("parent context point는 target_time과 exact knowledge_cutoff가 같아야 합니다.")
        if _time_key(self.assembly.context.as_of) != target:
            raise ValueError("parent context point는 target_time과 exact context as_of가 같아야 합니다.")
        if str(self.assembly.context.mode).strip().upper() != str(mode).strip().upper():
            raise ValueError("parent context point mode가 frame mode와 다릅니다.")
        expected = tuple(sorted(str(item) for item in manifest_hashes))
        actual = tuple(sorted(str(item) for item in self.assembly.manifest_hashes))
        if actual != expected:
            raise ValueError("parent context point manifest topology가 frame과 다릅니다.")

    @property
    def point_hash(self) -> str:
        return _stable_hash(
            {
                "schema": FRAME_SCHEMA_VERSION,
                "target_time": _time_key(self.target_time),
                "assembly_hash": self.assembly.assembly_hash,
                "context_hash": self.assembly.context.context_hash,
            }
        )

    def public_dict(self) -> dict:
        return {
            "target_time": _time_key(self.target_time),
            "assembly_hash": self.assembly.assembly_hash,
            "context_hash": self.assembly.context.context_hash,
            "point_hash": self.point_hash,
        }


@dataclass(frozen=True)
class ParentContextFrame:
    """Immutable exact-time parent context timeline for one target instrument."""

    frame_id: str
    target_symbol: str
    mode: str
    registry_hash: str
    manifest_hashes: tuple[str, ...]
    points: tuple[ParentContextPoint, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    MODES = {"OBSERVED", "DEPLOYMENT"}

    @classmethod
    def create(
        cls,
        *,
        frame_id: str,
        target_symbol: str,
        registry: ParentFeatureRegistry,
        assemblies: Sequence[ParentContextAssembly],
        mode: str = "OBSERVED",
        metadata: Mapping[str, Any] | None = None,
    ) -> "ParentContextFrame":
        _text(frame_id, "parent context frame_id")
        _text(target_symbol, "parent context target_symbol")
        registry.validate()
        normalized_mode = str(mode).strip().upper()
        if normalized_mode not in cls.MODES:
            raise ValueError("parent context frame mode는 OBSERVED 또는 DEPLOYMENT여야 합니다.")
        items = tuple(assemblies)
        if not items:
            raise ValueError("parent context frame assemblies가 비어 있습니다.")
        for assembly in items:
            if not isinstance(assembly, ParentContextAssembly):
                raise ValueError("parent context frame item은 ParentContextAssembly여야 합니다.")
            assembly.public_dict()
            if str(assembly.context.mode).strip().upper() != normalized_mode:
                raise ValueError("parent context frame assembly mode가 요청 mode와 다릅니다.")

        registry_manifest_hashes = {
            manifest.manifest_hash
            for manifest in registry.manifests
        }
        topology = tuple(sorted(str(item) for item in items[0].manifest_hashes))
        if not topology:
            raise ValueError("parent context frame manifest topology가 비어 있습니다.")
        if not set(topology).issubset(registry_manifest_hashes):
            raise ValueError("parent context frame manifest가 registry에 등록되어 있지 않습니다.")
        for assembly in items[1:]:
            if tuple(sorted(str(item) for item in assembly.manifest_hashes)) != topology:
                raise ValueError("parent context frame 도중 provider/manifest topology가 변경되었습니다.")

        points = tuple(
            sorted(
                (
                    ParentContextPoint(
                        target_time=assembly.knowledge_cutoff,
                        assembly=assembly,
                    )
                    for assembly in items
                ),
                key=lambda point: _time_key(point.target_time),
            )
        )
        target_times = tuple(_time_key(point.target_time) for point in points)
        if len(set(target_times)) != len(target_times):
            raise ValueError("parent context frame target_time에 중복이 있습니다.")
        for point in points:
            point.validate(mode=normalized_mode, manifest_hashes=topology)
        _json_safe(dict(metadata or {}))
        return cls(
            frame_id=str(frame_id).strip(),
            target_symbol=str(target_symbol).strip(),
            mode=normalized_mode,
            registry_hash=registry.registry_hash,
            manifest_hashes=topology,
            points=points,
            metadata=dict(metadata or {}),
        )

    def validate(self) -> None:
        _text(self.frame_id, "parent context frame_id")
        _text(self.target_symbol, "parent context target_symbol")
        normalized_mode = str(self.mode).strip().upper()
        if normalized_mode not in self.MODES:
            raise ValueError("parent context frame mode가 올바르지 않습니다.")
        _text(self.registry_hash, "parent context frame registry_hash")
        if not self.manifest_hashes or any(not str(item).strip() for item in self.manifest_hashes):
            raise ValueError("parent context frame manifest_hashes가 필요합니다.")
        if len(set(self.manifest_hashes)) != len(self.manifest_hashes):
            raise ValueError("parent context frame manifest_hashes에 중복이 있습니다.")
        if not self.points:
            raise ValueError("parent context frame points가 비어 있습니다.")
        previous = None
        for point in self.points:
            point.validate(mode=normalized_mode, manifest_hashes=self.manifest_hashes)
            current = _time_key(point.target_time)
            if previous is not None and current <= previous:
                raise ValueError("parent context frame points는 중복 없이 엄격 오름차순이어야 합니다.")
            previous = current
        _json_safe(dict(self.metadata))

    def resolve_exact(self, target_time: str) -> BattlefieldContext:
        """Resolve only an exact precomputed point; never nearest/fill-forward."""
        self.validate()
        wanted = _time_key(target_time)
        for point in self.points:
            if _time_key(point.target_time) == wanted:
                return point.assembly.context
        raise KeyError(
            f"exact parent context point가 없습니다: {wanted}; nearest/fill-forward는 금지됩니다."
        )

    @property
    def frame_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": FRAME_SCHEMA_VERSION,
                "frame_id": self.frame_id,
                "target_symbol": self.target_symbol,
                "mode": str(self.mode).strip().upper(),
                "registry_hash": self.registry_hash,
                "manifest_hashes": tuple(sorted(self.manifest_hashes)),
                "points": tuple(point.public_dict() for point in self.points),
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict:
        self.validate()
        return {
            "schema": FRAME_SCHEMA_VERSION,
            "frame_id": self.frame_id,
            "target_symbol": self.target_symbol,
            "mode": str(self.mode).strip().upper(),
            "registry_hash": self.registry_hash,
            "manifest_hashes": tuple(sorted(self.manifest_hashes)),
            "points": tuple(point.public_dict() for point in self.points),
            "metadata": dict(self.metadata),
            "resolution_policy": "EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD",
            "frame_hash": self.frame_hash,
        }


@dataclass(frozen=True)
class BoundParentFeature:
    feature_id: str
    value_type: str
    semantic_version: str
    manifest_hash: str
    present: bool
    value: Any = None

    def public_dict(self) -> dict:
        payload = {
            "feature_id": self.feature_id,
            "value_type": str(self.value_type).strip().upper(),
            "semantic_version": self.semantic_version,
            "manifest_hash": self.manifest_hash,
            "present": bool(self.present),
            "value": self.value if self.present else None,
        }
        _json_safe(payload)
        return payload


@dataclass(frozen=True)
class ParentContextBinding:
    target_time: str
    target_symbol: str
    frame_hash: str
    registry_hash: str
    context_hash: str
    values: tuple[BoundParentFeature, ...]

    @property
    def binding_hash(self) -> str:
        return _stable_hash(
            {
                "schema": BINDING_SCHEMA_VERSION,
                "target_time": _time_key(self.target_time),
                "target_symbol": self.target_symbol,
                "frame_hash": self.frame_hash,
                "registry_hash": self.registry_hash,
                "context_hash": self.context_hash,
                "values": tuple(item.public_dict() for item in self.values),
            }
        )

    def public_dict(self) -> dict:
        return {
            "schema": BINDING_SCHEMA_VERSION,
            "target_time": _time_key(self.target_time),
            "target_symbol": self.target_symbol,
            "frame_hash": self.frame_hash,
            "registry_hash": self.registry_hash,
            "context_hash": self.context_hash,
            "values": tuple(item.public_dict() for item in self.values),
            "binding_policy": "REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL",
            "binding_hash": self.binding_hash,
        }


class ParentContextBinder:
    """Generic read-only feature resolver over an already-frozen frame."""

    @classmethod
    def bind(
        cls,
        *,
        frame: ParentContextFrame,
        registry: ParentFeatureRegistry,
        target_time: str,
        feature_ids: Sequence[str],
    ) -> ParentContextBinding:
        frame.validate()
        registry.validate()
        if registry.registry_hash != frame.registry_hash:
            raise ValueError("parent context binder registry_hash가 frame과 다릅니다.")
        requested = tuple(sorted(_text(item, "bound feature_id") for item in feature_ids))
        if not requested:
            raise ValueError("parent context binder feature_ids가 비어 있습니다.")
        if len(set(requested)) != len(requested):
            raise ValueError("parent context binder feature_ids에 중복이 있습니다.")

        context = frame.resolve_exact(target_time)
        bound: list[BoundParentFeature] = []
        for feature_id in requested:
            try:
                resolved = registry.resolve(feature_id)
            except KeyError as exc:
                raise ValueError(f"등록되지 않은 parent feature입니다: {feature_id}") from exc
            manifest = dict(resolved["manifest"])
            feature = dict(resolved["feature"])
            manifest_hash = str(manifest["manifest_hash"])
            if manifest_hash not in frame.manifest_hashes:
                raise ValueError(f"요청 parent feature manifest가 frame에 없습니다: {feature_id}")
            layer = str(manifest["layer"]).strip().upper()
            context_id = str(manifest["context_id"]).strip()
            matches = [
                item
                for item in context.layers
                if str(item.layer).strip().upper() == layer
                and str(item.context_id).strip() == context_id
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"parent context binder layer/context를 정확히 하나 찾을 수 없습니다: {layer}/{context_id}"
                )
            feature_key = str(feature["feature_key"]).strip()
            features = dict(matches[0].features)
            if feature_key not in features:
                if bool(feature["required"]):
                    raise ValueError(f"required bound parent feature가 없습니다: {feature_id}")
                bound.append(
                    BoundParentFeature(
                        feature_id=feature_id,
                        value_type=str(feature["value_type"]),
                        semantic_version=str(feature["semantic_version"]),
                        manifest_hash=manifest_hash,
                        present=False,
                    )
                )
                continue
            value = features[feature_key]
            _validate_typed_value(value, str(feature["value_type"]), feature_id)
            bound.append(
                BoundParentFeature(
                    feature_id=feature_id,
                    value_type=str(feature["value_type"]),
                    semantic_version=str(feature["semantic_version"]),
                    manifest_hash=manifest_hash,
                    present=True,
                    value=value,
                )
            )

        return ParentContextBinding(
            target_time=_time_key(target_time),
            target_symbol=frame.target_symbol,
            frame_hash=frame.frame_hash,
            registry_hash=registry.registry_hash,
            context_hash=context.context_hash,
            values=tuple(bound),
        )
