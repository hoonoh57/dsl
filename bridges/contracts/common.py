"""Versioned, JSON-safe common contracts for cross-axis Bridges.

Bridge contracts are data boundaries only.  They must not import AXIS 1/2/3
runtime internals, providers, databases, or the frozen legacy core.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping


COMMON_CONTRACT_VERSION = "v1"
KNOWN_AXES = frozenset({"AXIS1", "AXIS2", "AXIS3", "EXTERNAL"})
RESPONSE_STATUSES = frozenset({"OK", "REJECTED", "ERROR"})


class BridgeContractError(ValueError):
    def __init__(self, message: str, code: str = "BRIDGE_CONTRACT_ERROR"):
        self.code = str(code)
        super().__init__(message)


def require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BridgeContractError(f"{label} must be a mapping", "BRIDGE_MAPPING_REQUIRED")
    return value


def require_nonempty(value: Any, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise BridgeContractError(f"{label} is required", "BRIDGE_VALUE_REQUIRED")
    return text


def require_schema(value: Any, expected: str) -> str:
    actual = require_nonempty(value, "schema")
    if actual != expected:
        raise BridgeContractError(
            f"unsupported schema: {actual!r}; expected {expected!r}",
            "BRIDGE_SCHEMA_MISMATCH",
        )
    return actual


def json_safe(value: Any, *, path: str = "$") -> Any:
    """Return a canonical JSON-compatible copy and reject opaque objects.

    Cross-axis boundaries intentionally reject arbitrary Python objects so one
    axis cannot leak mutable runtime state or internal class instances into
    another axis through the Bridge.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BridgeContractError(
                f"non-finite number is not allowed at {path}",
                "BRIDGE_NONFINITE_NUMBER",
            )
        return float(value)
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise BridgeContractError(
                    f"mapping keys must be non-empty strings at {path}",
                    "BRIDGE_BAD_MAPPING_KEY",
                )
            result[key] = json_safe(item, path=f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [json_safe(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    raise BridgeContractError(
        f"opaque value is not allowed across Bridge at {path}: {type(value).__name__}",
        "BRIDGE_OPAQUE_VALUE",
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BridgeRequestMeta:
    request_id: str
    source_axis: str
    target_axis: str
    operation: str
    contract_version: str = COMMON_CONTRACT_VERSION

    def validate(self) -> None:
        request_id = require_nonempty(self.request_id, "request_id")
        if len(request_id) > 160:
            raise BridgeContractError("request_id is too long", "BRIDGE_BAD_REQUEST_ID")
        source = require_nonempty(self.source_axis, "source_axis").upper()
        target = require_nonempty(self.target_axis, "target_axis").upper()
        if source not in KNOWN_AXES or target not in KNOWN_AXES - {"EXTERNAL"}:
            raise BridgeContractError(
                f"unsupported axis route: {source} -> {target}",
                "BRIDGE_BAD_AXIS_ROUTE",
            )
        if source == target:
            raise BridgeContractError("Bridge route must cross an axis boundary", "BRIDGE_SAME_AXIS_ROUTE")
        require_nonempty(self.operation, "operation")
        if self.contract_version != COMMON_CONTRACT_VERSION:
            raise BridgeContractError(
                f"unsupported common contract version: {self.contract_version}",
                "BRIDGE_VERSION_MISMATCH",
            )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["source_axis"] = self.source_axis.upper()
        value["target_axis"] = self.target_axis.upper()
        value["operation"] = self.operation.upper()
        return value


@dataclass(frozen=True)
class BridgeResponseMeta:
    request_id: str
    source_axis: str
    target_axis: str
    operation: str
    status: str
    contract_version: str = COMMON_CONTRACT_VERSION

    def validate(self) -> None:
        require_nonempty(self.request_id, "request_id")
        source = require_nonempty(self.source_axis, "source_axis").upper()
        target = require_nonempty(self.target_axis, "target_axis").upper()
        if source not in KNOWN_AXES - {"EXTERNAL"} or target not in KNOWN_AXES:
            raise BridgeContractError(
                f"unsupported response route: {source} -> {target}",
                "BRIDGE_BAD_AXIS_ROUTE",
            )
        if source == target:
            raise BridgeContractError("Bridge response must cross an axis boundary", "BRIDGE_SAME_AXIS_ROUTE")
        require_nonempty(self.operation, "operation")
        if str(self.status).upper() not in RESPONSE_STATUSES:
            raise BridgeContractError(f"unsupported response status: {self.status}", "BRIDGE_BAD_STATUS")
        if self.contract_version != COMMON_CONTRACT_VERSION:
            raise BridgeContractError(
                f"unsupported common contract version: {self.contract_version}",
                "BRIDGE_VERSION_MISMATCH",
            )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["source_axis"] = self.source_axis.upper()
        value["target_axis"] = self.target_axis.upper()
        value["operation"] = self.operation.upper()
        value["status"] = self.status.upper()
        return value
