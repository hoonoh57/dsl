"""Exact-time parent-context series binding for optional DSL ctx.* consumption.

This module converts already-trusted PCTX2B exact-time frames into one immutable
vector binding suitable for DSL semantic/runtime consumption.  It never calls a
provider and it accepts only DEPLOYMENT frames because values exposed here may
change executable tactic decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

from core.parent_context_frame import ParentContextBinder, ParentContextFrame
from core.parent_feature_provider import ParentFeatureRegistry


SCHEMA_VERSION = "dsl_parent_context_series/v1"
BINDING_POLICY = "REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) == 8:
        return digits + "235959"
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"DSL parent context time은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("DSL parent context binding에 NaN/Infinity를 사용할 수 없습니다.")
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


def _normalize_value(value: Any, value_type: str, feature_id: str) -> Any:
    kind = str(value_type).strip().upper()
    if kind == "NUMBER":
        if isinstance(value, bool):
            raise ValueError(f"DSL parent feature는 NUMBER여야 합니다: {feature_id}")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"DSL parent feature NUMBER는 유한해야 합니다: {feature_id}")
        return number
    if kind == "BOOLEAN":
        if not isinstance(value, bool):
            raise ValueError(f"DSL parent feature는 BOOLEAN이어야 합니다: {feature_id}")
        return bool(value)
    if kind == "STRING":
        if not isinstance(value, str):
            raise ValueError(f"DSL parent feature는 STRING이어야 합니다: {feature_id}")
        return value
    raise ValueError(f"지원하지 않는 DSL parent feature type: {value_type!r}")


@dataclass(frozen=True)
class DSLContextSeriesBinding:
    """Immutable exact-time vector binding used by the DSL compiler/runtime."""

    target_symbol: str
    target_times: tuple[str, ...]
    frame_hash: str
    registry_hash: str
    feature_types: Mapping[str, str]
    feature_values: Mapping[str, tuple[Any, ...]]

    @classmethod
    def from_frame(
        cls,
        *,
        frame: ParentContextFrame,
        registry: ParentFeatureRegistry,
        target_times: Sequence[str],
    ) -> "DSLContextSeriesBinding":
        frame.validate()
        registry.validate()
        if str(frame.mode).strip().upper() != "DEPLOYMENT":
            raise ValueError("DSL ctx.* 실행 바인딩은 DEPLOYMENT ParentContextFrame만 허용합니다.")
        if frame.registry_hash != registry.registry_hash:
            raise ValueError("DSL parent context registry_hash가 frame과 다릅니다.")

        normalized_times = tuple(_time_key(item) for item in target_times)
        if not normalized_times:
            raise ValueError("DSL parent context target_times가 비어 있습니다.")
        if len(set(normalized_times)) != len(normalized_times):
            raise ValueError("DSL parent context target_times에 중복이 있습니다.")
        if any(normalized_times[index] >= normalized_times[index + 1] for index in range(len(normalized_times) - 1)):
            raise ValueError("DSL parent context target_times는 엄격 오름차순이어야 합니다.")

        active_manifests = tuple(
            manifest for manifest in registry.manifests if manifest.manifest_hash in frame.manifest_hashes
        )
        if len(active_manifests) != len(frame.manifest_hashes):
            raise ValueError("DSL parent context frame manifest topology가 registry와 완전히 일치하지 않습니다.")

        specs = []
        for manifest in active_manifests:
            for spec in manifest.features:
                if not bool(spec.required):
                    continue
                specs.append(spec)
        specs.sort(key=lambda item: str(item.feature_id))
        if not specs:
            raise ValueError("DSL ctx.* v1에서 실행 가능한 required parent feature가 없습니다.")

        feature_types = {str(spec.feature_id): str(spec.value_type).strip().upper() for spec in specs}
        feature_values = {str(spec.feature_id): [] for spec in specs}
        requested_ids = tuple(feature_values)

        for target_time in normalized_times:
            binding = ParentContextBinder.bind(
                frame=frame,
                registry=registry,
                target_time=target_time,
                feature_ids=requested_ids,
            )
            by_id = {item.feature_id: item for item in binding.values}
            if set(by_id) != set(requested_ids):
                raise ValueError("DSL parent context exact-time binding feature coverage가 다릅니다.")
            for feature_id in requested_ids:
                item = by_id[feature_id]
                if not item.present:
                    raise ValueError(
                        f"DSL ctx.* v1은 optional/missing 값을 실행 입력으로 사용하지 않습니다: {feature_id}"
                    )
                feature_values[feature_id].append(
                    _normalize_value(item.value, feature_types[feature_id], feature_id)
                )

        return cls(
            target_symbol=str(frame.target_symbol).strip(),
            target_times=normalized_times,
            frame_hash=frame.frame_hash,
            registry_hash=registry.registry_hash,
            feature_types=dict(feature_types),
            feature_values={key: tuple(values) for key, values in feature_values.items()},
        )

    def validate(self) -> None:
        if not str(self.target_symbol).strip():
            raise ValueError("DSL parent context target_symbol이 필요합니다.")
        if not self.target_times:
            raise ValueError("DSL parent context target_times가 비어 있습니다.")
        if len(set(self.target_times)) != len(self.target_times):
            raise ValueError("DSL parent context target_times에 중복이 있습니다.")
        if any(self.target_times[index] >= self.target_times[index + 1] for index in range(len(self.target_times) - 1)):
            raise ValueError("DSL parent context target_times는 엄격 오름차순이어야 합니다.")
        if not str(self.frame_hash).strip() or not str(self.registry_hash).strip():
            raise ValueError("DSL parent context frame/registry hash가 필요합니다.")
        if not self.feature_types:
            raise ValueError("DSL parent context feature_types가 비어 있습니다.")
        if set(self.feature_types) != set(self.feature_values):
            raise ValueError("DSL parent context feature type/value identity가 일치하지 않습니다.")
        for feature_id, value_type in self.feature_types.items():
            values = tuple(self.feature_values[feature_id])
            if len(values) != len(self.target_times):
                raise ValueError(f"DSL parent context series 길이가 target_times와 다릅니다: {feature_id}")
            for value in values:
                _normalize_value(value, value_type, feature_id)

    @property
    def binding_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": SCHEMA_VERSION,
                "target_symbol": self.target_symbol,
                "target_times": self.target_times,
                "frame_hash": self.frame_hash,
                "registry_hash": self.registry_hash,
                "feature_types": dict(sorted(self.feature_types.items())),
                "feature_values": {
                    key: tuple(self.feature_values[key]) for key in sorted(self.feature_values)
                },
                "binding_policy": BINDING_POLICY,
            }
        )

    def semantic_types(self) -> dict[str, str]:
        self.validate()
        return {key: str(value).strip().upper() for key, value in self.feature_types.items()}

    def runtime_values(self) -> dict[str, np.ndarray]:
        self.validate()
        result: dict[str, np.ndarray] = {}
        for feature_id, value_type in self.feature_types.items():
            values = tuple(self.feature_values[feature_id])
            kind = str(value_type).strip().upper()
            if kind == "NUMBER":
                array = np.asarray(values, dtype=float)
            elif kind == "BOOLEAN":
                array = np.asarray(values, dtype=bool)
            else:
                array = np.asarray(values, dtype=object)
            result[f"ctx.{feature_id}"] = array
        return result

    def validate_target_times(self, target_times: Sequence[str]) -> None:
        self.validate()
        supplied = tuple(_time_key(item) for item in target_times)
        if supplied != self.target_times:
            raise ValueError(
                "DSL parent context binding target_times가 compile 대상과 exact 일치하지 않습니다."
            )

    def public_dict(self) -> dict:
        self.validate()
        return {
            "schema": SCHEMA_VERSION,
            "target_symbol": self.target_symbol,
            "target_times": self.target_times,
            "frame_hash": self.frame_hash,
            "registry_hash": self.registry_hash,
            "feature_types": dict(sorted(self.feature_types.items())),
            "feature_values": {
                key: tuple(self.feature_values[key]) for key in sorted(self.feature_values)
            },
            "binding_policy": BINDING_POLICY,
            "binding_hash": self.binding_hash,
        }
