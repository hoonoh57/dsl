"""Point-in-time battlefield context contracts for macro-ready tactical research.

The current micro-discovery phase normally uses ``BattlefieldContext.neutral``.
Later market/sector/group/narrative providers can attach immutable snapshots
without modifying DSL execution or historical micro evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) == 8:
        return digits + "235959"
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"context time은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("BattlefieldContext에 NaN/Infinity를 사용할 수 없습니다.")
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


@dataclass(frozen=True)
class ContextLayerSnapshot:
    """One immutable point-in-time information layer."""

    layer: str
    context_id: str
    as_of: str
    source: str
    features: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not str(self.layer).strip():
            raise ValueError("context layer가 필요합니다.")
        if not str(self.context_id).strip():
            raise ValueError("context_id가 필요합니다.")
        _time_key(self.as_of)
        if not str(self.source).strip():
            raise ValueError("context source가 필요합니다.")
        _json_safe(dict(self.features))

    @property
    def snapshot_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "layer": str(self.layer).strip().upper(),
                "context_id": str(self.context_id).strip(),
                "as_of": _time_key(self.as_of),
                "source": str(self.source).strip(),
                "features": dict(self.features),
            }
        )

    def public_dict(self) -> dict:
        return {
            "layer": str(self.layer).strip().upper(),
            "context_id": str(self.context_id).strip(),
            "as_of": _time_key(self.as_of),
            "source": str(self.source).strip(),
            "features": dict(self.features),
            "snapshot_hash": self.snapshot_hash,
        }


@dataclass(frozen=True)
class BattlefieldContext:
    """Immutable envelope for optional macro/group context.

    Modes:
    - NEUTRAL: context does not influence micro execution.
    - OBSERVED: context is attached for attribution/evidence only.
    - DEPLOYMENT: a separate DeploymentDecision may use the context to gate or
      prioritize a validated tactic.
    """

    as_of: str
    mode: str = "NEUTRAL"
    layers: tuple[ContextLayerSnapshot, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    MODES = {"NEUTRAL", "OBSERVED", "DEPLOYMENT"}

    @classmethod
    def neutral(cls, as_of: str, metadata: Mapping[str, Any] | None = None) -> "BattlefieldContext":
        return cls(as_of=as_of, mode="NEUTRAL", layers=(), metadata=dict(metadata or {}))

    def validate(self) -> None:
        mode = str(self.mode).strip().upper()
        if mode not in self.MODES:
            raise ValueError(f"BattlefieldContext mode가 유효하지 않습니다: {self.mode!r}")
        envelope_time = _time_key(self.as_of)
        seen = set()
        for layer in self.layers:
            layer.validate()
            key = (str(layer.layer).strip().upper(), str(layer.context_id).strip())
            if key in seen:
                raise ValueError(f"중복 context layer snapshot: {key}")
            seen.add(key)
            if _time_key(layer.as_of) > envelope_time:
                raise ValueError(
                    f"context layer가 BattlefieldContext as_of보다 미래입니다: {key} {layer.as_of} > {self.as_of}"
                )
        if mode == "NEUTRAL" and self.layers:
            raise ValueError("NEUTRAL BattlefieldContext에는 context layer를 넣을 수 없습니다.")
        _json_safe(dict(self.metadata))

    def validate_for(self, knowledge_cutoff: str) -> None:
        self.validate()
        if _time_key(self.as_of) > _time_key(knowledge_cutoff):
            raise ValueError(
                f"BattlefieldContext가 battle knowledge cutoff보다 미래입니다: {self.as_of} > {knowledge_cutoff}"
            )
        for layer in self.layers:
            if _time_key(layer.as_of) > _time_key(knowledge_cutoff):
                raise ValueError(
                    f"context layer가 battle knowledge cutoff보다 미래입니다: {layer.context_id}"
                )

    @property
    def context_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": "battlefield_context/v1",
                "as_of": _time_key(self.as_of),
                "mode": str(self.mode).strip().upper(),
                "layers": [layer.public_dict() for layer in self.layers],
                "metadata": dict(self.metadata),
            }
        )

    def public_dict(self) -> dict:
        return {
            "schema": "battlefield_context/v1",
            "as_of": _time_key(self.as_of),
            "mode": str(self.mode).strip().upper(),
            "layers": [layer.public_dict() for layer in self.layers],
            "metadata": dict(self.metadata),
            "context_hash": self.context_hash,
        }


@dataclass(frozen=True)
class DeploymentDecision:
    """Future command-layer result. It never rewrites a tactic."""

    context_hash: str
    allowed: bool = True
    priority: float = 0.0
    eligible_tactics: tuple[str, ...] = ()
    blocked_tactics: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not str(self.context_hash).strip():
            raise ValueError("DeploymentDecision context_hash가 필요합니다.")
        if not math.isfinite(float(self.priority)):
            raise ValueError("DeploymentDecision priority는 유한해야 합니다.")
        if set(self.eligible_tactics).intersection(self.blocked_tactics):
            raise ValueError("같은 tactic을 eligible_tactics와 blocked_tactics에 동시에 둘 수 없습니다.")
        if len(set(self.eligible_tactics)) != len(self.eligible_tactics):
            raise ValueError("eligible_tactics에 중복이 있습니다.")
        if len(set(self.blocked_tactics)) != len(self.blocked_tactics):
            raise ValueError("blocked_tactics에 중복이 있습니다.")

    def public_dict(self) -> dict:
        self.validate()
        return asdict(self)
