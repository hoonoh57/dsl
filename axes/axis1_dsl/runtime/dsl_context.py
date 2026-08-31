"""Exact-time read-only context binding consumed by AXIS 1 DSL runtime.

AXIS 1 never owns or calls parent-feature providers. External/AXIS 2 preparation
must supply an already-frozen typed binding payload whose target times exactly
match the executable market bars.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np


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
    """Immutable typed vector binding for exact executable bar times."""

    target_symbol: str
    target_times: tuple[str, ...]
    frame_hash: str
    registry_hash: str
    feature_types: Mapping[str, str]
    feature_values: Mapping[str, tuple[Any, ...]]

    @classmethod
    def from_prepared(
        cls,
        *,
        target_symbol: str,
        target_times: Sequence[str],
        frame_hash: str,
        registry_hash: str,
        feature_types: Mapping[str, str],
        feature_values: Mapping[str, Sequence[Any]],
    ) -> "DSLContextSeriesBinding":
        """Build only from an already-prepared provider-free binding payload."""
        binding = cls(
            target_symbol=str(target_symbol).strip(),
            target_times=tuple(_time_key(item) for item in target_times),
            frame_hash=str(frame_hash).strip(),
            registry_hash=str(registry_hash).strip(),
            feature_types={str(key): str(value).strip().upper() for key, value in feature_types.items()},
            feature_values={str(key): tuple(values) for key, values in feature_values.items()},
        )
        binding.validate()
        return binding

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
