"""Versioned data-only contract for AXIS2 -> AXIS3 -> AXIS1 E2E backtests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bridges.contracts.common import (
    BridgeContractError,
    BridgeRequestMeta,
    BridgeResponseMeta,
    json_safe,
    require_mapping,
    require_nonempty,
    require_schema,
    stable_hash,
)


THREE_AXIS_E2E_REQUEST_SCHEMA = "bridge.three_axis_e2e_request/v1"
THREE_AXIS_E2E_RESPONSE_SCHEMA = "bridge.three_axis_e2e_response/v1"
THREE_AXIS_E2E_OPERATION = "SELECT_PLAN_BACKTEST"


def _only_keys(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise BridgeContractError(
            f"unknown {label} fields: {', '.join(unknown)}",
            "BRIDGE_UNKNOWN_FIELD",
        )


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BridgeContractError(f"{label} must be a positive integer", "BRIDGE_BAD_INTEGER")
    return int(value)


def _artifact_ref(value: Any, label: str, *, id_key: str) -> dict[str, Any]:
    raw = require_mapping(value, label)
    _only_keys(raw, {id_key, "version", "artifact_hash"}, label)
    return {
        id_key: require_nonempty(raw.get(id_key), f"{label}.{id_key}"),
        "version": _positive_int(raw.get("version"), f"{label}.version"),
        "artifact_hash": require_nonempty(raw.get("artifact_hash"), f"{label}.artifact_hash"),
    }


def _execution_inputs(value: Any) -> dict[str, dict[str, Any]]:
    raw = require_mapping(value, "execution_inputs")
    result: dict[str, dict[str, Any]] = {}
    for symbol, item in raw.items():
        symbol_name = require_nonempty(symbol, "execution_inputs symbol")
        payload = require_mapping(item, f"execution_inputs.{symbol_name}")
        _only_keys(payload, {"market", "entry_gate", "parent_context"}, f"execution_inputs.{symbol_name}")
        if "market" not in payload:
            raise BridgeContractError(
                f"execution_inputs.{symbol_name}.market is required",
                "BRIDGE_MARKET_FIELD_MISSING",
            )
        result[symbol_name] = {
            "market": json_safe(payload["market"], path=f"$.execution_inputs.{symbol_name}.market"),
            "entry_gate": json_safe(payload.get("entry_gate"), path=f"$.execution_inputs.{symbol_name}.entry_gate"),
            "parent_context": json_safe(
                payload.get("parent_context"), path=f"$.execution_inputs.{symbol_name}.parent_context"
            ),
        }
    return result


@dataclass(frozen=True)
class ThreeAxisE2ERequest:
    meta: BridgeRequestMeta
    run_id: str
    strategy_ref: Mapping[str, Any]
    condition_ref: Mapping[str, Any]
    snapshot: Mapping[str, Any]
    selection_spec: Mapping[str, Any]
    execution_inputs: Mapping[str, Mapping[str, Any]]

    @classmethod
    def from_dict(cls, value: Any) -> "ThreeAxisE2ERequest":
        raw = require_mapping(value, "request")
        _only_keys(
            raw,
            {"schema", "meta", "run_id", "strategy_ref", "condition_ref", "snapshot", "selection_spec", "execution_inputs"},
            "request",
        )
        require_schema(raw.get("schema"), THREE_AXIS_E2E_REQUEST_SCHEMA)
        meta_raw = require_mapping(raw.get("meta"), "meta")
        _only_keys(meta_raw, {"request_id", "source_axis", "target_axis", "operation", "contract_version"}, "meta")
        meta = BridgeRequestMeta(
            request_id=require_nonempty(meta_raw.get("request_id"), "meta.request_id"),
            source_axis=require_nonempty(meta_raw.get("source_axis"), "meta.source_axis"),
            target_axis=require_nonempty(meta_raw.get("target_axis"), "meta.target_axis"),
            operation=require_nonempty(meta_raw.get("operation"), "meta.operation"),
            contract_version=str(meta_raw.get("contract_version", "v1")),
        )
        meta.validate()
        if meta.target_axis.upper() != "AXIS3" or meta.operation.upper() != THREE_AXIS_E2E_OPERATION:
            raise BridgeContractError(
                f"three-axis route must target AXIS3/{THREE_AXIS_E2E_OPERATION}",
                "BRIDGE_E2E_ROUTE_MISMATCH",
            )
        snapshot = json_safe(require_mapping(raw.get("snapshot"), "snapshot"), path="$.snapshot")
        selection = json_safe(
            require_mapping(raw.get("selection_spec"), "selection_spec"), path="$.selection_spec"
        )
        if snapshot.get("schema_version") != "axis2_point_in_time_snapshot/v1":
            raise BridgeContractError("bad AXIS2 snapshot schema", "BRIDGE_E2E_SNAPSHOT_SCHEMA")
        if not isinstance(snapshot.get("snapshot_hash"), str) or not snapshot["snapshot_hash"]:
            raise BridgeContractError("snapshot_hash is required", "BRIDGE_E2E_SNAPSHOT_HASH_REQUIRED")
        if selection.get("schema_version") != "axis2_selection_spec/v1":
            raise BridgeContractError("bad AXIS2 selection schema", "BRIDGE_E2E_SELECTION_SCHEMA")
        if not isinstance(selection.get("selection_hash"), str) or not selection["selection_hash"]:
            raise BridgeContractError("selection_hash is required", "BRIDGE_E2E_SELECTION_HASH_REQUIRED")
        return cls(
            meta=meta,
            run_id=require_nonempty(raw.get("run_id"), "run_id"),
            strategy_ref=_artifact_ref(raw.get("strategy_ref"), "strategy_ref", id_key="strategy_id"),
            condition_ref=_artifact_ref(raw.get("condition_ref"), "condition_ref", id_key="condition_id"),
            snapshot=snapshot,
            selection_spec=selection,
            execution_inputs=_execution_inputs(raw.get("execution_inputs") or {}),
        )

    def public_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "schema": THREE_AXIS_E2E_REQUEST_SCHEMA,
                "meta": self.meta.public_dict(),
                "run_id": self.run_id,
                "strategy_ref": dict(self.strategy_ref),
                "condition_ref": dict(self.condition_ref),
                "snapshot": dict(self.snapshot),
                "selection_spec": dict(self.selection_spec),
                "execution_inputs": {key: dict(value) for key, value in sorted(self.execution_inputs.items())},
            }
        )

    @property
    def request_hash(self) -> str:
        return stable_hash(self.public_dict())


@dataclass(frozen=True)
class ThreeAxisE2EResponse:
    meta: BridgeResponseMeta
    request_hash: str
    trace: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None

    def public_dict(self) -> dict[str, Any]:
        self.meta.validate()
        status = self.meta.status.upper()
        request_hash = require_nonempty(self.request_hash, "request_hash")
        if status == "OK":
            if self.trace is None or self.error is not None:
                raise BridgeContractError("OK E2E response requires trace and no error", "BRIDGE_BAD_RESPONSE_SHAPE")
        else:
            if self.error is None:
                raise BridgeContractError("non-OK E2E response requires error", "BRIDGE_BAD_RESPONSE_SHAPE")
        value = {
            "schema": THREE_AXIS_E2E_RESPONSE_SCHEMA,
            "meta": self.meta.public_dict(),
            "request_hash": request_hash,
            "trace": None if self.trace is None else dict(self.trace),
            "error": None if self.error is None else dict(self.error),
        }
        safe = json_safe(value)
        safe["response_hash"] = stable_hash(safe)
        return safe
