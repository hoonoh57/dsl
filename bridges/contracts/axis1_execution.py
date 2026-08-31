"""AXIS 1 execution Request -> Response contract v1.

This module is deliberately data-only and imports no AXIS 1 implementation.
The adapter that owns AXIS 1 execution lives outside ``bridges.contracts``.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
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


AXIS1_EXECUTION_REQUEST_SCHEMA = "bridge.axis1_execution_request/v1"
AXIS1_EXECUTION_RESPONSE_SCHEMA = "bridge.axis1_execution_response/v1"
AXIS1_OPERATION = "BACKTEST"
PARENT_CONTEXT_SCHEMA = "dsl_parent_context_series/v1"


def _only_keys(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise BridgeContractError(
            f"unknown {label} fields: {', '.join(unknown)}",
            "BRIDGE_UNKNOWN_FIELD",
        )


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise BridgeContractError(f"{label} must be numeric", "BRIDGE_BAD_MARKET_VALUE")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise BridgeContractError(f"{label} must be numeric", "BRIDGE_BAD_MARKET_VALUE") from exc
    if not math.isfinite(number):
        raise BridgeContractError(f"{label} must be finite", "BRIDGE_BAD_MARKET_VALUE")
    return number


def _normalize_market(value: Any) -> dict[str, Any]:
    market = require_mapping(value, "market")
    _only_keys(market, {"time", "open", "high", "low", "close", "volume", "meta"}, "market")
    required = ("time", "open", "high", "low", "close", "volume")
    missing = [key for key in required if key not in market]
    if missing:
        raise BridgeContractError(
            f"market fields missing: {', '.join(missing)}",
            "BRIDGE_MARKET_FIELD_MISSING",
        )
    if any(not isinstance(market[key], (list, tuple)) for key in required):
        raise BridgeContractError("market fields must be arrays", "BRIDGE_MARKET_ARRAY_REQUIRED")
    lengths = {key: len(market[key]) for key in required}
    if len(set(lengths.values())) != 1 or lengths["close"] < 2:
        raise BridgeContractError(
            f"market array lengths are invalid: {lengths}",
            "BRIDGE_MARKET_LENGTH_MISMATCH",
        )
    times = [require_nonempty(item, f"market.time[{index}]") for index, item in enumerate(market["time"])]
    if len(set(times)) != len(times) or any(times[index] >= times[index + 1] for index in range(len(times) - 1)):
        raise BridgeContractError(
            "market.time must be unique and strictly increasing",
            "BRIDGE_MARKET_TIME_ORDER",
        )
    result: dict[str, Any] = {"time": times}
    for field in ("open", "high", "low", "close", "volume"):
        result[field] = [
            _finite_number(item, f"market.{field}[{index}]")
            for index, item in enumerate(market[field])
        ]
    meta = market.get("meta") or {}
    result["meta"] = json_safe(require_mapping(meta, "market.meta"), path="$.market.meta")
    return result


def _normalize_parent_context(value: Any, *, symbol: str, market_times: list[str]) -> dict[str, Any] | None:
    if value is None:
        return None
    context = require_mapping(value, "parent_context")
    allowed = {
        "schema", "target_symbol", "target_times", "frame_hash", "registry_hash",
        "feature_types", "feature_values", "binding_policy", "binding_hash",
    }
    _only_keys(context, allowed, "parent_context")
    require_schema(context.get("schema"), PARENT_CONTEXT_SCHEMA)
    target_symbol = require_nonempty(context.get("target_symbol"), "parent_context.target_symbol")
    if target_symbol != symbol:
        raise BridgeContractError(
            f"parent_context target_symbol mismatch: {target_symbol!r} != {symbol!r}",
            "BRIDGE_CONTEXT_SYMBOL_MISMATCH",
        )
    raw_times = context.get("target_times")
    if not isinstance(raw_times, (list, tuple)):
        raise BridgeContractError("parent_context.target_times must be an array", "BRIDGE_CONTEXT_TIME_REQUIRED")
    target_times = [require_nonempty(item, "parent_context.target_times") for item in raw_times]
    if target_times != market_times:
        raise BridgeContractError(
            "parent_context.target_times must exactly match market.time",
            "BRIDGE_CONTEXT_TIME_MISMATCH",
        )
    frame_hash = require_nonempty(context.get("frame_hash"), "parent_context.frame_hash")
    registry_hash = require_nonempty(context.get("registry_hash"), "parent_context.registry_hash")
    feature_types = require_mapping(context.get("feature_types"), "parent_context.feature_types")
    feature_values = require_mapping(context.get("feature_values"), "parent_context.feature_values")
    if not feature_types or set(feature_types) != set(feature_values):
        raise BridgeContractError(
            "parent_context feature type/value identities must match and be non-empty",
            "BRIDGE_CONTEXT_FEATURE_MISMATCH",
        )
    normalized_types: dict[str, str] = {}
    normalized_values: dict[str, list[Any]] = {}
    for feature_id in sorted(feature_types):
        identity = require_nonempty(feature_id, "parent_context.feature_id")
        kind = require_nonempty(feature_types[feature_id], f"parent_context.feature_types.{identity}").upper()
        if kind not in {"NUMBER", "BOOLEAN", "STRING"}:
            raise BridgeContractError(
                f"unsupported parent context type: {kind}",
                "BRIDGE_CONTEXT_TYPE_UNSUPPORTED",
            )
        values = feature_values[feature_id]
        if not isinstance(values, (list, tuple)) or len(values) != len(market_times):
            raise BridgeContractError(
                f"parent context feature length mismatch: {identity}",
                "BRIDGE_CONTEXT_FEATURE_LENGTH",
            )
        normalized_types[identity] = kind
        normalized_values[identity] = json_safe(list(values), path=f"$.parent_context.feature_values.{identity}")
    result = {
        "schema": PARENT_CONTEXT_SCHEMA,
        "target_symbol": target_symbol,
        "target_times": target_times,
        "frame_hash": frame_hash,
        "registry_hash": registry_hash,
        "feature_types": normalized_types,
        "feature_values": normalized_values,
    }
    if context.get("binding_policy") is not None:
        result["binding_policy"] = require_nonempty(context.get("binding_policy"), "parent_context.binding_policy")
    if context.get("binding_hash") is not None:
        result["binding_hash"] = require_nonempty(context.get("binding_hash"), "parent_context.binding_hash")
    return result


@dataclass(frozen=True)
class Axis1ExecutionRequest:
    meta: BridgeRequestMeta
    symbol: str
    timeframe: str
    strategy_id: str
    strategy_version: str
    dsl_code: str
    market: Mapping[str, Any]
    settings: Mapping[str, Any]
    entry_gate: tuple[bool, ...] | None = None
    parent_context: Mapping[str, Any] | None = None

    @classmethod
    def from_dict(cls, value: Any) -> "Axis1ExecutionRequest":
        raw = require_mapping(value, "request")
        _only_keys(
            raw,
            {"schema", "meta", "instrument", "strategy", "market", "settings", "entry_gate", "parent_context"},
            "request",
        )
        require_schema(raw.get("schema"), AXIS1_EXECUTION_REQUEST_SCHEMA)
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
        if meta.target_axis.upper() != "AXIS1" or meta.operation.upper() != AXIS1_OPERATION:
            raise BridgeContractError(
                f"AXIS 1 execution route must target AXIS1/{AXIS1_OPERATION}",
                "BRIDGE_AXIS1_ROUTE_MISMATCH",
            )
        instrument = require_mapping(raw.get("instrument"), "instrument")
        _only_keys(instrument, {"symbol", "timeframe"}, "instrument")
        symbol = require_nonempty(instrument.get("symbol"), "instrument.symbol")
        timeframe = require_nonempty(instrument.get("timeframe"), "instrument.timeframe")
        strategy = require_mapping(raw.get("strategy"), "strategy")
        _only_keys(strategy, {"strategy_id", "strategy_version", "dsl_code"}, "strategy")
        strategy_id = require_nonempty(strategy.get("strategy_id"), "strategy.strategy_id")
        strategy_version = require_nonempty(strategy.get("strategy_version"), "strategy.strategy_version")
        dsl_code = require_nonempty(strategy.get("dsl_code"), "strategy.dsl_code")
        market = _normalize_market(raw.get("market"))
        settings = json_safe(require_mapping(raw.get("settings") or {}, "settings"), path="$.settings")
        raw_gate = raw.get("entry_gate")
        entry_gate: tuple[bool, ...] | None = None
        if raw_gate is not None:
            if not isinstance(raw_gate, (list, tuple)) or len(raw_gate) != len(market["time"]):
                raise BridgeContractError(
                    "entry_gate must match market bar count",
                    "BRIDGE_ENTRY_GATE_LENGTH",
                )
            if any(not isinstance(item, bool) for item in raw_gate):
                raise BridgeContractError("entry_gate values must be boolean", "BRIDGE_ENTRY_GATE_TYPE")
            entry_gate = tuple(bool(item) for item in raw_gate)
        parent_context = _normalize_parent_context(
            raw.get("parent_context"), symbol=symbol, market_times=market["time"]
        )
        return cls(
            meta=meta,
            symbol=symbol,
            timeframe=timeframe,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            dsl_code=dsl_code,
            market=market,
            settings=settings,
            entry_gate=entry_gate,
            parent_context=parent_context,
        )

    def public_dict(self) -> dict[str, Any]:
        value = {
            "schema": AXIS1_EXECUTION_REQUEST_SCHEMA,
            "meta": self.meta.public_dict(),
            "instrument": {"symbol": self.symbol, "timeframe": self.timeframe},
            "strategy": {
                "strategy_id": self.strategy_id,
                "strategy_version": self.strategy_version,
                "dsl_code": self.dsl_code,
            },
            "market": dict(self.market),
            "settings": dict(self.settings),
            "entry_gate": None if self.entry_gate is None else list(self.entry_gate),
            "parent_context": None if self.parent_context is None else dict(self.parent_context),
        }
        return json_safe(value)

    @property
    def request_hash(self) -> str:
        return stable_hash(self.public_dict())


@dataclass(frozen=True)
class Axis1ExecutionResponse:
    meta: BridgeResponseMeta
    request_hash: str
    capability_registry_hash: str
    result: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None

    def public_dict(self) -> dict[str, Any]:
        self.meta.validate()
        request_hash = require_nonempty(self.request_hash, "request_hash")
        registry_hash = require_nonempty(self.capability_registry_hash, "capability_registry_hash")
        status = self.meta.status.upper()
        if status == "OK":
            if self.result is None or self.error is not None:
                raise BridgeContractError("OK response requires result and no error", "BRIDGE_BAD_RESPONSE_SHAPE")
        else:
            if self.result is not None or self.error is None:
                raise BridgeContractError("non-OK response requires error and no result", "BRIDGE_BAD_RESPONSE_SHAPE")
        value = {
            "schema": AXIS1_EXECUTION_RESPONSE_SCHEMA,
            "meta": self.meta.public_dict(),
            "request_hash": request_hash,
            "capability_registry_hash": registry_hash,
            "result": None if self.result is None else dict(self.result),
            "error": None if self.error is None else dict(self.error),
        }
        safe = json_safe(value)
        safe["response_hash"] = stable_hash(safe)
        return safe
